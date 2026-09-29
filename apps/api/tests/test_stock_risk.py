from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models import Company, Dataset, InventorySnapshot, Product, Sale
from app.schemas.forecasting import ForecastPoint
from app.services.stock_risk import build_stock_risk_result, calculate_stock_risk


def forecast(values: list[str]) -> list[ForecastPoint]:
    start = date(2026, 10, 1)
    return [
        ForecastPoint(date=start + timedelta(days=index), predicted_quantity=Decimal(value))
        for index, value in enumerate(values)
    ]


def test_projection_stockout_and_shortage() -> None:
    result = calculate_stock_risk(100, forecast(["20", "20", "20", "20", "20"]))

    assert [point.projected_stock for point in result.projection] == [80, 60, 40, 20, 0]
    assert result.days_of_cover == 5
    assert result.expected_stockout_date == date(2026, 10, 5)
    assert result.projected_shortage == 0
    assert result.risk_level == "critical"


def test_shortage_safe_zero_stock_and_zero_demand_classification() -> None:
    shortage = calculate_stock_risk(100, forecast(["70", "70"]))
    safe = calculate_stock_risk(500, forecast(["50", "50"]))
    zero_stock = calculate_stock_risk(0, forecast(["1"]))
    zero_demand = calculate_stock_risk(0, forecast(["0", "0"]))

    assert shortage.projected_shortage == 40
    assert safe.expected_stockout_date is None
    assert safe.risk_level == "safe"
    assert zero_stock.risk_level == "critical"
    assert zero_demand.risk_level == "safe"


def test_high_medium_and_low_risk_boundaries() -> None:
    high = calculate_stock_risk(100, forecast(["12.5"] * 8))
    medium = calculate_stock_risk(100, forecast(["7"] * 15))
    low = calculate_stock_risk(100, forecast(["17"] * 5))

    assert high.risk_level == "high"
    assert medium.risk_level == "medium"
    assert low.expected_stockout_date is None
    assert low.risk_level == "low"


def test_stock_risk_distinguishes_missing_inventory_from_insufficient_data() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company = Company(name="A")
        dataset = Dataset(company=company, name="a.csv", source_type="csv", status="completed")
        forecastable = Product(company=company, external_id="P001", name="Forecastable")
        insufficient = Product(company=company, external_id="P002", name="Insufficient")
        session.add_all([company, dataset, forecastable, insufficient])
        session.flush()
        for index in range(30):
            session.add(
                Sale(
                    company_id=company.id,
                    dataset_id=dataset.id,
                    product_id=forecastable.id,
                    sale_date=date(2026, 1, 1) + timedelta(days=index),
                    quantity=Decimal("1"),
                    unit_price=Decimal("1"),
                    revenue=Decimal("1"),
                )
            )
        session.add(
            InventorySnapshot(
                company_id=company.id,
                product_id=insufficient.id,
                snapshot_date=date(2026, 2, 1),
                quantity_on_hand=10,
            )
        )
        session.commit()

        missing_inventory = build_stock_risk_result(session, company.id, forecastable, 7)
        insufficient_data = build_stock_risk_result(session, company.id, insufficient, 7)

    assert missing_inventory.status == "missing_inventory"
    assert insufficient_data.status == "insufficient_data"
