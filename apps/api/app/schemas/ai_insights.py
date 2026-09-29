import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

InsightCategory = Literal["sales", "customers", "forecast", "anomaly", "inventory", "cross_signal"]
InsightPriority = Literal["low", "medium", "high", "critical"]


class AIInsight(BaseModel):
    id: str = Field(min_length=1)
    category: InsightCategory
    priority: InsightPriority
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1, max_length=5)
    recommended_action: str = Field(min_length=1)
    related_product_id: uuid.UUID | None = None


class AIInsightsRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class AIInsightsResponse(BaseModel):
    generated_at: datetime
    insights: list[AIInsight] = Field(max_length=7)
