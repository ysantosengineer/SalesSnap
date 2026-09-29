from datetime import date, timedelta
from decimal import Decimal

from app.schemas.forecasting import ForecastPoint
from app.services.stock_risk import calculate_stock_risk


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
