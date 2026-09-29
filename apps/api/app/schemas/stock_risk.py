import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.schemas.forecasting import ForecastProduct

StockRiskStatus = Literal["success", "missing_inventory", "insufficient_data"]
RiskLevel = Literal["critical", "high", "medium", "low", "safe"]


class ProjectedInventoryPoint(BaseModel):
    date: date
    projected_stock: Decimal


class StockRiskResult(BaseModel):
    status: StockRiskStatus
    product: ForecastProduct
    current_stock: Decimal | None = None
    snapshot_date: date | None = None
    forecast_total: Decimal | None = None
    selected_model: str | None = None
    days_of_cover: int | None = None
    expected_stockout_date: date | None = None
    stockout_within_horizon: bool = False
    projected_shortage: Decimal | None = None
    risk_level: RiskLevel | None = None
    projection: list[ProjectedInventoryPoint] = []


class StockRiskSummary(BaseModel):
    total_products: int
    critical: int
    high: int
    medium: int
    low: int
    safe: int
    missing_inventory: int
    insufficient_data: int


class StockRiskPage(BaseModel):
    items: list[StockRiskResult]
    total: int
    limit: int
    offset: int


class StockRiskProductReference(BaseModel):
    id: uuid.UUID
    external_id: str
    name: str
