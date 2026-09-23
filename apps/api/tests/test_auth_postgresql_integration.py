import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.core.security import hash_password
from app.models import Company, RefreshToken, User


@pytest.mark.postgres
def test_authentication_migration_persists_and_constrains_postgres_data() -> None:
    database_url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")

    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    api_directory = Path(__file__).parents[1]
    config = Config(str(api_directory / "alembic.ini"))
    config.set_main_option("script_location", str(api_directory / "alembic"))

    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        assert {"users", "refresh_tokens"} <= set(inspect(engine).get_table_names())

        with Session(engine) as session:
            company = Company(name="Authentication integration company")
            user = User(
                company=company,
                email="owner@integration.test",
                password_hash=hash_password("secure-password"),
            )
            session.add(user)
            session.flush()
            refresh_token = RefreshToken(
                user_id=user.id,
                token_hash="a" * 64,
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
            session.add(refresh_token)
            session.commit()

            assert session.get(User, user.id).company_id == company.id
            assert session.get(RefreshToken, refresh_token.id).user_id == user.id

            session.add(
                User(
                    company_id=company.id,
                    email=user.email,
                    password_hash=hash_password("another-password"),
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            session.add(
                RefreshToken(
                    user_id=user.id,
                    token_hash="a" * 64,
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
