import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import InventorySnapshot, Product
from app.schemas.forecasting import ForecastPoint, ProductForecast
from app.schemas.stock_risk import ProjectedInventoryPoint, StockRiskResult
from app.services.forecasting import create_product_forecast
from app.services.inventory_import import get_latest_inventory_snapshot


@dataclass(frozen=True)
class RiskCalculation:
    projection: list[ProjectedInventoryPoint]
    forecast_total: Decimal
    days_of_cover: int | None
    expected_stockout_date: date | None
    projected_shortage: Decimal
    risk_level: str


def calculate_stock_risk(
    current_stock: int | Decimal, forecast: list[ForecastPoint]
) -> RiskCalculation:
    stock = Decimal(str(current_stock))
    cumulative_demand = Decimal("0")
    projection: list[ProjectedInventoryPoint] = []
    expected_stockout_date: date | None = None
    days_of_cover: int | None = None

    for index, point in enumerate(forecast, start=1):
        cumulative_demand += Decimal(str(point.predicted_quantity))
        projected_stock = stock - cumulative_demand
        projection.append(
            ProjectedInventoryPoint(date=point.date, projected_stock=projected_stock)
        )
        if expected_stockout_date is None and projected_stock <= 0:
            expected_stockout_date = point.date
            days_of_cover = index

    projected_shortage = max(cumulative_demand - stock, Decimal("0"))
    risk_level = classify_stock_risk(
        current_stock=stock,
        remaining_stock=stock - cumulative_demand,
        days_of_cover=days_of_cover,
        forecast_total=cumulative_demand,
    )
    return RiskCalculation(
        projection=projection,
        forecast_total=cumulative_demand,
        days_of_cover=days_of_cover,
        expected_stockout_date=expected_stockout_date,
        projected_shortage=projected_shortage,
        risk_level=risk_level,
    )


def classify_stock_risk(
    current_stock: Decimal,
    remaining_stock: Decimal,
    days_of_cover: int | None,
    forecast_total: Decimal,
) -> str:
    if forecast_total == 0:
        return "safe"
    if current_stock == 0 or (days_of_cover is not None and days_of_cover <= 7):
        return "critical"
    if days_of_cover is not None and days_of_cover <= 14:
        return "high"
    if days_of_cover is not None and days_of_cover <= 30:
        return "medium"
    if remaining_stock <= current_stock * Decimal("0.2"):
        return "low"
    return "safe"


def build_stock_risk_result(
    session: Session,
    company_id: uuid.UUID,
    product: Product,
    horizon: int,
) -> StockRiskResult:
    forecast = create_product_forecast(session, company_id, product, horizon)
    if forecast.status == "insufficient_data":
        return StockRiskResult(status="insufficient_data", product=forecast.product)

    inventory = get_latest_inventory_snapshot(session, company_id, product.id)
    if inventory is None:
        return StockRiskResult(status="missing_inventory", product=forecast.product)
    return risk_result_from_forecast(inventory, forecast)


def risk_result_from_forecast(
    inventory: InventorySnapshot, forecast: ProductForecast
) -> StockRiskResult:
    calculation = calculate_stock_risk(inventory.quantity_on_hand, forecast.forecast)
    return StockRiskResult(
        status="success",
        product=forecast.product,
        current_stock=Decimal(inventory.quantity_on_hand),
        snapshot_date=inventory.snapshot_date,
        forecast_total=calculation.forecast_total,
        selected_model=forecast.evaluation.selected_model if forecast.evaluation else None,
        days_of_cover=calculation.days_of_cover,
        expected_stockout_date=calculation.expected_stockout_date,
        stockout_within_horizon=calculation.expected_stockout_date is not None,
        projected_shortage=calculation.projected_shortage,
        risk_level=calculation.risk_level,
        projection=calculation.projection,
    )
