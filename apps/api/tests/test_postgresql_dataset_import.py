import os
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import Company, Customer, Dataset, Product, Sale
from app.services.dataset_import import get_dataset, import_sales_dataset

CSV_HEADER = b"date,customer_id,product_id,product_name,quantity,unit_price\n"


@pytest.mark.postgres
def test_csv_import_persists_tenant_scoped_postgres_records() -> None:
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
            company_a = Company(name="Import company A")
            company_b = Company(name="Import company B")
            session.add_all([company_a, company_b])
            session.commit()

            result_a = import_sales_dataset(
                session,
                company_a.id,
                "sales-a.csv",
                CSV_HEADER + b"2026-09-01,C001,P001,Mouse,2,149.90\n",
            )
            result_b = import_sales_dataset(
                session,
                company_b.id,
                "sales-b.csv",
                CSV_HEADER + b"2026-09-02,C001,P001,Mouse,1,99.99\n",
            )

            assert result_a.status == result_b.status == "completed"
            assert session.query(Dataset).count() == 2
            assert session.query(Product).count() == 2
            assert session.query(Customer).count() == 2
            sales = session.query(Sale).order_by(Sale.sale_date).all()
            assert len(sales) == 2
            assert sales[0].revenue == Decimal("299.80")
            assert sales[1].revenue == Decimal("99.99")
            assert sales[0].company_id != sales[1].company_id
            assert get_dataset(session, company_a.id, result_b.dataset_id) is None
            assert get_dataset(session, company_b.id, result_a.dataset_id) is None
    finally:
        command.downgrade(config, "base")
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
