import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class RfmCustomer(BaseModel):
    customer_id: uuid.UUID
    external_id: str
    recency: int
    frequency: int
    monetary: Decimal
    r_score: int
    f_score: int
    m_score: int
    fm_score: int
    segment: str


class RfmSegmentSummary(BaseModel):
    segment: str
    customers: int
    percentage: Decimal
    revenue: Decimal
    revenue_percentage: Decimal


class RfmSummary(BaseModel):
    total_customers: int
    reference_date: date | None
    segments: list[RfmSegmentSummary]


class RfmCustomerPage(BaseModel):
    items: list[RfmCustomer]
    total: int
