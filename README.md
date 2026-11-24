# 卓工协会服务平台 API

项目使用 Python 3.14、FastAPI 和 uv。字段表见[字段表说明](docs/field-specs/README.md)。

## 在 Ubuntu（WSL）启动

安装 uv 后，在仓库根目录运行以下命令。

```bash
uv sync --locked
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8002
```

- [健康检查](http://localhost:8002/health) 返回 HTTP 200 和 `{"status":"ok"}`。
- [Swagger UI](http://localhost:8002/docs) 提供交互式接口文档。
- 如需设置应用标题，可将 [环境变量示例](.env.example) 复制为 `.env`，再修改 `APP_TITLE`。

## 目录与注释规范

- [应用入口](app/main.py) 创建 FastAPI 应用并注册路由。
- [接口目录](app/api/) 放置路由。
- [配置目录](app/core/) 管理环境配置。
- Python 代码采用 Google 风格中文 docstring。先用中文概括职责，按需使用 `Args:`、`Returns:`、`Raises:` 说明参数、返回值和异常。

## 本地登录联调

先由数据库管理员在 PostgreSQL szumiee_login 创建 service_auth schema 并交给同名迁移角色，再创建 service_login 运行角色。应用使用 DATABASE_URL，迁移和种子命令使用 MIGRATION_DATABASE_URL。JWT_SECRET 至少 32 字节，两端使用不同的随机值。

~~~bash
uv run --locked alembic upgrade head
read -rsp '测试账号密码：' SEED_PASSWORD
printf '\n'
SEED_PASSWORD="$SEED_PASSWORD" uv run --locked python -m app.seed --username demo-student --name 联调账号 --role student
unset SEED_PASSWORD
~~~

种子命令按登录名写入一个账号，重复执行保留账号 ID 并撤销旧会话。支持 student、ta 和 mgmt。角色按数组保存，当前接口返回第一项。

- POST /api/auth/login 接受 {"username": "…", "password": "…"}，成功返回 {id,name,role}。
- GET /api/auth/me 校验当前会话，成功返回相同结构。
- POST /api/auth/logout 撤销当前会话、清除本端 Cookie，成功返回 204。
- 凭据或会话无效时返回 401。认证配置不完整或数据库查询失败时返回 503。

POST 请求的 Origin 必须命中 AUTH_ORIGINS，否则返回 403。前端开发代理应原样转发该头。多个来源用逗号分隔。会话使用 service_session HttpOnly Cookie，有效期 30 分钟。同一账号的新登录会撤销旧会话。HTTPS 部署时设置 COOKIE_SECURE=true。
