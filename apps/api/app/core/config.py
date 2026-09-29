from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from environment variables."""

    app_name: str = "SalesSnap"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://sales_snap:sales_snap@localhost:5432/sales_snap"
    frontend_url: str = "http://localhost:3000"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    max_upload_size_mb: int = 10
    anomaly_lookback_days: int = 28
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    ai_insights_enabled: bool = False
    ai_insights_timeout_seconds: int = 30
    ai_insights_max_items_per_section: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
