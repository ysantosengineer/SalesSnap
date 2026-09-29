import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class AnomalyProduct(BaseModel):
    id: uuid.UUID
    external_id: str
    name: str


class DemandAnomaly(BaseModel):
    date: date
    product: AnomalyProduct
    actual_demand: Decimal
    expected_demand: Decimal
    deviation_percentage: Decimal | None
    direction: Literal["spike", "drop"]
    severity: Literal["low", "medium", "high", "critical"]
    robust_score: Decimal
    statistical_flag: bool
    isolation_forest_flag: bool
    confidence: Literal["confirmed", "potential"]


class DemandTimelinePoint(BaseModel):
    date: date
    quantity: Decimal


class AnomalyPage(BaseModel):
    status: Literal["ok", "insufficient_data"]
    items: list[DemandAnomaly] = []
    total: int = 0
    required_observations: int = 30
    available_observations: int = 0
    history: list[DemandTimelinePoint] = []


class AnomalySummary(BaseModel):
    total_anomalies: int
    critical: int
    high: int
    medium: int
    low: int
    spikes: int
    drops: int
