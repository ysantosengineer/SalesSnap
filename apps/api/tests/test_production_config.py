import pytest
from pydantic import ValidationError

from app.core.config import Settings

PRODUCTION_VALUES = {
    "environment": "production",
    "database_url": "postgresql+psycopg://app:secret@postgres:5432/sales_snap",
    "jwt_secret_key": "a-production-secret-with-at-least-32-characters",
    "cors_allowed_origins": "https://sales.example.com, https://admin.example.com",
}


def test_production_configuration_accepts_explicit_safe_values() -> None:
    settings = Settings(_env_file=None, **PRODUCTION_VALUES)

    assert settings.debug is False
    assert settings.cors_origins == ["https://sales.example.com", "https://admin.example.com"]


@pytest.mark.parametrize(
    "override",
    [
        {"jwt_secret_key": "change-me"},
        {"database_url": "postgresql+psycopg://sales_snap:sales_snap@localhost:5432/sales_snap"},
        {"cors_allowed_origins": "*"},
        {"cors_allowed_origins": "http://sales.example.com"},
        {"debug": True},
        {"ai_insights_enabled": True, "openai_api_key": None},
    ],
)
def test_production_configuration_rejects_unsafe_values(override: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(PRODUCTION_VALUES | override))


def test_development_configuration_keeps_explicit_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.cors_origins == ["http://localhost:3000"]
