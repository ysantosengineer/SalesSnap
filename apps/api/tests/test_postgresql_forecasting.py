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
from app.services.forecasting import get_daily_product_demand


@pytest.mark.postgres
def test_postgresql_aggregates_daily_product_demand_per_tenant() -> None:
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
        with Session(create_engine(database_url)) as session:
            company_a, company_b = Company(name="Forecast A"), Company(name="Forecast B")
            session.add_all([company_a, company_b])
            session.flush()
            dataset_a = Dataset(company=company_a, name="A", source_type="csv", status="completed")
            dataset_b = Dataset(company=company_b, name="B", source_type="csv", status="completed")
            product_a = Product(company=company_a, external_id="P1", name="A")
            product_b = Product(company=company_b, external_id="P1", name="B")
            session.add_all([dataset_a, dataset_b, product_a, product_b])
            session.flush()
            session.add_all(
                [
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset_a.id,
                        product_id=product_a.id,
                        sale_date=date(2026, 9, 1),
                        quantity=Decimal("2"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("2"),
                    ),
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset_a.id,
                        product_id=product_a.id,
                        sale_date=date(2026, 9, 1),
                        quantity=Decimal("3"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("3"),
                    ),
                    Sale(
                        company_id=company_b.id,
                        dataset_id=dataset_b.id,
                        product_id=product_b.id,
                        sale_date=date(2026, 9, 1),
                        quantity=Decimal("99"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("99"),
                    ),
                ]
            )
            session.commit()
            demand = get_daily_product_demand(session, company_a.id, product_a.id)
        assert demand.to_dict("records") == [
            {"date": date(2026, 9, 1), "quantity": Decimal("5.000")}
        ]
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
