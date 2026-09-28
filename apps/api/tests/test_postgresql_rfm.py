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
from app.services.rfm import analyze_rfm


@pytest.mark.postgres
def test_rfm_aggregates_sales_in_postgresql_per_company() -> None:
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
        with Session(engine) as session:
            company_a = Company(name="RFM Company A")
            company_b = Company(name="RFM Company B")
            session.add_all([company_a, company_b])
            session.flush()

            dataset = Dataset(
                company_id=company_a.id,
                name="RFM integration dataset",
                source_type="csv",
                status="completed",
            )
            dataset_b = Dataset(
                company_id=company_b.id,
                name="Other company dataset",
                source_type="csv",
                status="completed",
            )
            product_a = Product(company_id=company_a.id, external_id="SKU-A", name="Widget")
            product_b = Product(company_id=company_b.id, external_id="SKU-B", name="Other")
            customer_a = Customer(company_id=company_a.id, external_id="CUSTOMER-A")
            customer_b = Customer(company_id=company_b.id, external_id="CUSTOMER-B")
            session.add_all([dataset, dataset_b, product_a, product_b, customer_a, customer_b])
            session.flush()
            session.add_all(
                [
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset.id,
                        product_id=product_a.id,
                        customer_id=customer_a.id,
                        sale_date=date(2026, 9, 28),
                        quantity=Decimal("2"),
                        unit_price=Decimal("10.00"),
                        revenue=Decimal("20.00"),
                    ),
                    Sale(
                        company_id=company_a.id,
                        dataset_id=dataset.id,
                        product_id=product_a.id,
                        customer_id=customer_a.id,
                        sale_date=date(2026, 9, 30),
                        quantity=Decimal("1"),
                        unit_price=Decimal("50.00"),
                        revenue=Decimal("50.00"),
                    ),
                    Sale(
                        company_id=company_b.id,
                        dataset_id=dataset_b.id,
                        product_id=product_b.id,
                        customer_id=customer_b.id,
                        sale_date=date(2026, 10, 1),
                        quantity=Decimal("1"),
                        unit_price=Decimal("999.00"),
                        revenue=Decimal("999.00"),
                    ),
                ]
            )
            session.commit()

            customers, reference_date = analyze_rfm(session, company_a.id)

        assert reference_date == date(2026, 10, 1)
        assert len(customers) == 1
        assert customers[0].external_id == "CUSTOMER-A"
        assert customers[0].frequency == 2
        assert customers[0].monetary == Decimal("70.00")
        assert customers[0].recency == 1
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
