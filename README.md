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
