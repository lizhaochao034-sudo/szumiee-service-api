"""处理密码和本端 JWT 会话。"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from argon2.low_level import Type

COOKIE_NAME = "service_session"
COOKIE_PATH = "/api/auth"
SESSION_SECONDS = 1800
ISSUER = "szumiee-service-api"
AUDIENCE = "szumiee-service-web"
password_hasher = PasswordHasher(type=Type.ID)
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def verify_password(password: str, stored_hash: str | None) -> bool:
    """校验 Argon2id 密码。账号不存在时仍执行一次同成本校验。"""
    is_supported = stored_hash is not None and stored_hash.startswith("$argon2id$")
    try:
        password_hasher.verify(stored_hash if is_supported else _dummy_hash, password)
    except (InvalidHashError, VerifyMismatchError):
        return False
    return is_supported


def create_token(account_id: UUID, session_id: UUID, secret: str) -> str:
    """签发绑定当前服务和会话的短期令牌。"""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": str(account_id),
            "jti": str(session_id),
            "iat": now,
            "exp": now + timedelta(seconds=SESSION_SECONDS),
        },
        secret,
        algorithm="HS256",
    )


def read_token(token: str, secret: str) -> tuple[UUID, UUID] | None:
    """验证签名和必要声明，成功时返回账号 ID 与会话 ID。"""
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["iss", "aud", "sub", "jti", "iat", "exp"], "strict_aud": True},
        )
        return UUID(claims["sub"]), UUID(claims["jti"])
    except (jwt.InvalidTokenError, ValueError):
        return None
