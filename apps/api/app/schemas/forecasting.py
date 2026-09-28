import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ForecastProduct(BaseModel):
    id: uuid.UUID
    external_id: str
    name: str
    observations: int
    forecast_available: bool


class DemandHistoryPoint(BaseModel):
    date: date
    quantity: Decimal


class ForecastPoint(BaseModel):
    date: date
    predicted_quantity: Decimal


class ForecastEvaluation(BaseModel):
    selected_model: str
    model_name: str
    model_version: str
    mae: Decimal
    rmse: Decimal
    wape: Decimal | None
    baseline_mae: Decimal
    baseline_rmse: Decimal
    baseline_wape: Decimal | None


class ProductForecast(BaseModel):
    status: Literal["ok", "insufficient_data"]
    product: ForecastProduct
    history: list[DemandHistoryPoint] = []
    forecast: list[ForecastPoint] = []
    evaluation: ForecastEvaluation | None = None
    horizon_days: int
    required_observations: int
    available_observations: int
