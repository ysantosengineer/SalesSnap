import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RowError(BaseModel):
    row: int
    field: str
    message: str


class DatasetImportResponse(BaseModel):
    dataset_id: uuid.UUID
    status: str
    rows_received: int
    rows_imported: int
    rows_rejected: int
    products_created: int
    customers_created: int
    sales_created: int
    errors: list[RowError] = Field(default_factory=list)


class DatasetSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
