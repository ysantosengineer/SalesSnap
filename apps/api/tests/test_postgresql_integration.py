import os
from datetime import date
from decimal import Decimal

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.tenant_data import get_product, get_products


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
        with Session(engine) as session:
            company_a = Company(name="PostgreSQL Company A")
            company_b = Company(name="PostgreSQL Company B")
            session.add_all([company_a, company_b])
            session.flush()
            dataset = Dataset(
                company_id=company_a.id,
                name="Integration dataset",
                source_type="csv",
                status="completed",
            )
            product_a = Product(company_id=company_a.id, external_id="SKU-1", name="Widget")
            product_b = Product(company_id=company_b.id, external_id="SKU-1", name="Widget")
            customer = Customer(company_id=company_a.id, external_id="CUSTOMER-1")
            session.add_all([dataset, product_a, product_b, customer])
            session.flush()
            session.add(
                Sale(
                    company_id=company_a.id,
                    dataset_id=dataset.id,
                    product_id=product_a.id,
                    customer_id=customer.id,
                    sale_date=date(2026, 1, 1),
                    quantity=Decimal("2"),
                    unit_price=Decimal("10.00"),
                    revenue=Decimal("20.00"),
                )
            )
            session.commit()

            assert get_products(session, company_a.id) == [product_a]
            assert get_product(session, company_a.id, product_b.id) is None
            session.add(Product(company_id=company_a.id, external_id="SKU-1", name="Duplicate"))
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
