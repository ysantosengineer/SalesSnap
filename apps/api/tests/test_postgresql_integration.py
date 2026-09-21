import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


@pytest.mark.postgres
def test_alembic_migrates_empty_postgres_database() -> None:
    database_url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")

    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config("alembic.ini")
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        assert {"companies", "datasets", "products", "customers", "sales"} <= set(
            inspect(engine).get_table_names()
        )
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
