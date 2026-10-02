from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration read from environment variables."""

    app_name: str = "SalesSnap"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://sales_snap:sales_snap@localhost:5432/sales_snap"
    cors_allowed_origins: str = "http://localhost:3000"
    jwt_secret_key: str = "change-me-use-a-long-random-local-value"
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    anomaly_lookback_days: int = 28
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    ai_insights_enabled: bool = False
    ai_insights_timeout_seconds: int = 30
    ai_insights_max_items_per_section: int = 5
    ai_chat_history_messages: int = Field(default=10, ge=1, le=40)
    ai_chat_max_tool_calls: int = Field(default=5, ge=1, le=10)
    ai_chat_max_output_tokens: int = Field(default=800, ge=64, le=4000)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        origins = self.cors_origins
        if not origins or "*" in origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must contain an explicit origin allowlist")
        if self.environment != "production":
            return self
        if self.debug:
            raise ValueError("DEBUG must be false in production")
        if len(self.jwt_secret_key) < 32 or self.jwt_secret_key.startswith("change-me"):
            raise ValueError("JWT_SECRET_KEY must be a high-entropy production secret")
        if self.database_url.endswith("sales_snap:sales_snap@localhost:5432/sales_snap"):
            raise ValueError("DATABASE_URL must be explicitly configured for production")
        if any(not origin.startswith("https://") for origin in origins):
            raise ValueError("Production CORS origins must use HTTPS")
        if self.ai_insights_enabled and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI is enabled")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
