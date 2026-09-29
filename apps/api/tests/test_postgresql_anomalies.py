import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import Company, Dataset, Product, Sale
from app.services.anomalies import get_product_anomaly_series


@pytest.mark.postgres
def test_postgresql_anomaly_series_is_daily_aggregated_and_tenant_scoped() -> None:
    database_url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    directory = Path(__file__).parents[1]
    config = Config(str(directory / "alembic.ini"))
    config.set_main_option("script_location", str(directory / "alembic"))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with Session(create_engine(database_url)) as session:
            a, b = Company(name="A"), Company(name="B")
            session.add_all([a, b])
            session.flush()
            da, db = (
                Dataset(company=a, name="A", source_type="csv", status="completed"),
                Dataset(company=b, name="B", source_type="csv", status="completed"),
            )
            pa, pb = (
                Product(company=a, external_id="P", name="A"),
                Product(company=b, external_id="P", name="B"),
            )
            session.add_all([da, db, pa, pb])
            session.flush()
            session.add_all(
                [
                    Sale(
                        company_id=a.id,
                        dataset_id=da.id,
                        product_id=pa.id,
                        sale_date=date(2026, 1, 1),
                        quantity=Decimal("2"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("2"),
                    ),
                    Sale(
                        company_id=a.id,
                        dataset_id=da.id,
                        product_id=pa.id,
                        sale_date=date(2026, 1, 1),
                        quantity=Decimal("3"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("3"),
                    ),
                    Sale(
                        company_id=b.id,
                        dataset_id=db.id,
                        product_id=pb.id,
                        sale_date=date(2026, 1, 2),
                        quantity=Decimal("99"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("99"),
                    ),
                ]
            )
            session.commit()
            series = get_product_anomaly_series(session, a.id, pa.id)
        assert series["quantity"].tolist() == [5.0]
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
