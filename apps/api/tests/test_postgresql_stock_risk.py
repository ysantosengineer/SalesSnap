import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import Company, Dataset, InventorySnapshot, Product, Sale
from app.services.forecasting import get_forecast_product
from app.services.stock_risk import build_stock_risk_result


@pytest.mark.postgres
def test_stock_risk_uses_latest_tenant_inventory_on_postgres() -> None:
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    directory = Path(__file__).parents[1]
    config = Config(str(directory / "alembic.ini"))
    config.set_main_option("script_location", str(directory / "alembic"))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with Session(create_engine(url)) as session:
            company_a, company_b = Company(name="A"), Company(name="B")
            dataset_a = Dataset(
                company=company_a, name="a.csv", source_type="csv", status="completed"
            )
            dataset_b = Dataset(
                company=company_b, name="b.csv", source_type="csv", status="completed"
            )
            product_a = Product(company=company_a, external_id="P001", name="A product")
            product_b = Product(company=company_b, external_id="P001", name="B product")
            session.add_all([company_a, company_b, dataset_a, dataset_b, product_a, product_b])
            session.flush()
            for index in range(30):
                for company, dataset, product in (
                    (company_a, dataset_a, product_a),
                    (company_b, dataset_b, product_b),
                ):
                    session.add(
                        Sale(
                            company_id=company.id,
                            dataset_id=dataset.id,
                            product_id=product.id,
                            sale_date=date(2026, 1, 1) + timedelta(days=index),
                            quantity=Decimal("10"),
                            unit_price=Decimal("1"),
                            revenue=Decimal("10"),
                        )
                    )
            session.add_all(
                [
                    InventorySnapshot(
                        company_id=company_a.id,
                        product_id=product_a.id,
                        snapshot_date=date(2026, 9, 28),
                        quantity_on_hand=150,
                    ),
                    InventorySnapshot(
                        company_id=company_a.id,
                        product_id=product_a.id,
                        snapshot_date=date(2026, 9, 29),
                        quantity_on_hand=110,
                    ),
                    InventorySnapshot(
                        company_id=company_b.id,
                        product_id=product_b.id,
                        snapshot_date=date(2026, 9, 29),
                        quantity_on_hand=999,
                    ),
                ]
            )
            session.commit()

            result = build_stock_risk_result(session, company_a.id, product_a, 7)

            assert result.status == "success"
            assert result.current_stock == 110
            assert get_forecast_product(session, company_a.id, product_b.id) is None
    finally:
        command.downgrade(config, "base")
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
