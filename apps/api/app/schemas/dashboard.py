import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_revenue: Decimal
    units_sold: Decimal
    sales_records: int
    active_customers: int
    average_sale_value: Decimal


class RevenueSeriesPoint(BaseModel):
    date: date
    revenue: Decimal
    units_sold: Decimal
    sales_records: int


class TopProduct(BaseModel):
    product_id: uuid.UUID
    external_id: str
    name: str
    revenue: Decimal
    units_sold: Decimal
    sales_records: int


class LatestDataset(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime


class DashboardOverview(BaseModel):
    best_product_by_revenue: TopProduct | None
    best_product_by_units: TopProduct | None
    highest_revenue_day: RevenueSeriesPoint | None
    latest_dataset: LatestDataset | None
