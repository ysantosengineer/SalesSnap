from pydantic import BaseModel


class InventoryImportSummary(BaseModel):
    rows_received: int
    rows_imported: int
    rows_rejected: int
    snapshots_created: int
    snapshots_updated: int
    errors: list[str] = []
