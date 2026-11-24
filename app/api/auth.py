"""处理登录、当前用户查询及退出。"""

from collections.abc import Callable
from functools import lru_cache
from threading import BoundedSemaphore
from uuid import UUID, uuid4

import sqlalchemy as sa
from argon2.exceptions import VerificationError
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.database import account_table, database_engine
from app.core.security import (
    COOKIE_NAME,
    COOKIE_PATH,
    SESSION_SECONDS,
    create_token,
    read_token,
    verify_password,
)


class AuthRoute(APIRoute):
    """统一禁止缓存认证响应，并避免回显验证失败的凭据。"""

    def get_route_handler(self) -> Callable:
        """包装认证路由的响应及常见输入错误。"""
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                response = await handler(request)
            except RequestValidationError:
                response = JSONResponse({"detail": "请求格式无效"}, status_code=422)
            except HTTPException as error:
                response = JSONResponse(
                    {"detail": error.detail}, status_code=error.status_code, headers=error.headers
                )
            response.headers["Cache-Control"] = "no-store"
            return response

        return handle


router = APIRouter(prefix="/api/auth", tags=["auth"], route_class=AuthRoute)
columns = account_table.c
account_id_column = columns.account_id
identity_columns = (account_id_column, columns.name, columns.roles)
# 限制同时执行的 Argon2 校验次数，控制每个进程的内存开销。
_password_slots = BoundedSemaphore(4)


class LoginBody(BaseModel):
    """接受登录名和原始密码。"""

    username: str = Field(max_length=128)
    password: SecretStr = Field(max_length=1024)


class Identity(BaseModel):
    """返回页面需要的最小账号信息。"""

    id: UUID
    name: str
    role: str


def unavailable() -> HTTPException:
    """生成统一的服务不可用响应。"""
    return HTTPException(status_code=503, detail="服务暂不可用")


@lru_cache(maxsize=1)
def auth_engine(database_url: str) -> Engine:
    """复用本进程的连接池。"""
    return database_engine(database_url)


def auth_settings(request: Request) -> tuple[Settings, Engine, str]:
    """读取已配置的运行账号和签名密钥。"""
    settings: Settings = request.app.state.settings
    secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
    if settings.database_url is None or len(secret.encode("utf-8")) < 32:
        raise unavailable()
    try:
        engine = auth_engine(settings.database_url.get_secret_value())
    except (ValueError, SQLAlchemyError):
        raise unavailable() from None
    return settings, engine, secret


def check_origin(request: Request) -> None:
    """对改变会话的请求精确校验代理保留的浏览器 Origin。"""
    settings: Settings = request.app.state.settings
    allowed = {origin.strip() for origin in settings.auth_origins.split(",") if origin.strip()}
    origins = request.headers.getlist("origin")
    if len(origins) != 1 or origins[0] == "null" or origins[0] not in allowed:
        raise HTTPException(status_code=403, detail="请求来源不受信任")


def identity(row: RowMapping) -> Identity:
    """从数据库记录构造当前用户。"""
    return Identity(id=row[account_id_column], name=row["name"], role=row["roles"][0])


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response) -> Identity:
    """验证账号密码，写入新会话，并设置本端 Cookie。"""
    check_origin(request)
    settings, engine, secret = auth_settings(request)
    login_name, password = body.username.strip(), body.password.get_secret_value()
    invalid = HTTPException(status_code=401, detail="账号或密码错误")
    if not login_name or "\x00" in login_name or not password:
        raise invalid
    try:
        with engine.connect() as connection:
            stored_hash = connection.scalar(
                sa.select(columns.password_hash).where(columns.username == login_name)
            )
        if not _password_slots.acquire(blocking=False):
            raise unavailable()
        try:
            valid = verify_password(password, stored_hash)
        finally:
            _password_slots.release()
        if not valid:
            raise invalid
        session_id = uuid4()
        with engine.begin() as connection:
            row = connection.execute(
                account_table.update()
                .where(columns.username == login_name, columns.password_hash == stored_hash)
                .values(session_id=session_id)
                .returning(*identity_columns)
            ).mappings().one_or_none()
            if row is None:
                raise invalid
            user = identity(row)
            token = create_token(user.id, session_id, secret)
    except (SQLAlchemyError, VerificationError):
        raise unavailable() from None
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_SECONDS,
        path=COOKIE_PATH,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return user


@router.get("/me")
def me(request: Request) -> Identity:
    """检查令牌和服务器会话，并返回当前账号信息。"""
    _, engine, secret = auth_settings(request)
    claims = read_token(request.cookies.get(COOKIE_NAME, ""), secret)
    if claims is not None:
        account_id, session_id = claims
        try:
            with engine.connect() as connection:
                row = connection.execute(
                    sa.select(*identity_columns).where(
                        account_id_column == account_id, columns.session_id == session_id
                    )
                ).mappings().one_or_none()
        except SQLAlchemyError:
            raise unavailable() from None
        if row is not None:
            return identity(row)
    raise HTTPException(status_code=401, detail="请先登录")


@router.post("/logout", status_code=204)
def logout(request: Request) -> Response:
    """撤销匹配的会话并清理本端 Cookie，允许重复退出。"""
    check_origin(request)
    settings, engine, secret = auth_settings(request)
    claims = read_token(request.cookies.get(COOKIE_NAME, ""), secret)
    if claims is not None:
        account_id, session_id = claims
        try:
            with engine.begin() as connection:
                connection.execute(
                    account_table.update()
                    .where(account_id_column == account_id, columns.session_id == session_id)
                    .values(session_id=None)
                )
        except SQLAlchemyError:
            raise unavailable() from None
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE_NAME, path=COOKIE_PATH, secure=settings.cookie_secure, httponly=True, samesite="lax"
    )
    return response
