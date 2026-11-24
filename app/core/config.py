from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """读取应用设置，支持通过环境变量覆盖默认值。"""

    app_title: str = "卓工协会服务平台 API"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
