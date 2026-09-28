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
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.dashboard import get_revenue_series, get_summary, get_top_products


@pytest.mark.postgres
def test_postgresql_dashboard_aggregates_are_tenant_scoped() -> None:
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
            company_a, company_b = Company(name="A"), Company(name="B")
            dataset = Dataset(
                company=company_a, name="a.csv", source_type="csv", status="completed"
            )
            product = Product(company=company_a, external_id="P1", name="Mouse")
            customer = Customer(company=company_a, external_id="C1")
            session.add_all([company_a, company_b, dataset, product, customer])
            session.flush()
            session.add_all(
                [
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset.id,
                        product_id=product.id,
                        customer_id=customer.id,
                        sale_date=date(2026, 9, 1),
                        quantity=Decimal("2"),
                        unit_price=Decimal("100"),
                        revenue=Decimal("200"),
                    ),
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset.id,
                        product_id=product.id,
                        customer_id=customer.id,
                        sale_date=date(2026, 9, 2),
                        quantity=Decimal("3"),
                        unit_price=Decimal("150"),
                        revenue=Decimal("450"),
                    ),
                ]
            )
            session.commit()
            summary = get_summary(session, company_a.id, date(2026, 9, 1), date(2026, 9, 1))
            assert summary.total_revenue == Decimal("200.00")
            assert summary.active_customers == 1
            assert len(get_revenue_series(session, company_a.id, None, None)) == 2
            assert get_top_products(session, company_a.id, None, None, 10)[0].revenue == Decimal(
                "650.00"
            )
            assert get_summary(session, company_b.id, None, None).sales_records == 0
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
