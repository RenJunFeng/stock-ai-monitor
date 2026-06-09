from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Stock AI Monitor", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
        alias="CORS_ORIGINS",
    )
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")

    deepseek_enabled: bool = Field(default=False, alias="DEEPSEEK_ENABLED")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-v4-pro", alias="DEEPSEEK_MODEL")
    deepseek_timeout_seconds: int = Field(default=120, alias="DEEPSEEK_TIMEOUT_SECONDS")

    market_provider: str = Field(default="easyquotation", alias="MARKET_PROVIDER")
    market_allow_mock_fallback: bool = Field(default=False, alias="MARKET_ALLOW_MOCK_FALLBACK")

    smtp_host: str = Field(default="smtp.qq.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_sender: str = Field(default="", alias="SMTP_SENDER")
    alert_recipient: str = Field(default="", alias="ALERT_RECIPIENT")

    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_interval_minutes: int = Field(default=60, alias="SCHEDULER_INTERVAL_MINUTES")

    @property
    def cors_origins(self) -> List[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    @property
    def deepseek_ready(self) -> bool:
        return self.deepseek_enabled and bool(self.deepseek_api_key.strip())

    @property
    def smtp_ready(self) -> bool:
        required = [self.smtp_host, self.smtp_user, self.smtp_password, self.smtp_sender, self.alert_recipient]
        return all(bool(item.strip()) for item in required)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
