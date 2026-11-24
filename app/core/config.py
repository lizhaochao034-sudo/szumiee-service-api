"""读取本端应用和迁移配置。"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalSettings(BaseSettings):
    """接受环境变量及本地 .env，忽略属于其他命令的设置。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class Settings(LocalSettings):
    """读取应用设置，登录配置可以独立于健康检查提供。"""

    app_title: str = "卓工协会服务平台 API"
    database_url: SecretStr | None = None
    jwt_secret: SecretStr | None = None
    auth_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cookie_secure: bool = False


class MigrationSettings(LocalSettings):
    """读取迁移和 seed 使用的独立数据库连接。"""

    migration_database_url: SecretStr | None = None
