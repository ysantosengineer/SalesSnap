import io
import uuid
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventorySnapshot, Product
from app.schemas.inventory import InventoryImportSummary

REQUIRED_COLUMNS = {"snapshot_date", "product_id", "quantity_on_hand"}


def import_inventory_csv(
    session: Session, company_id: uuid.UUID, content: bytes
) -> InventoryImportSummary:
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype={"product_id": str})
    except Exception as error:
        raise ValueError("Invalid inventory CSV") from error
    if not REQUIRED_COLUMNS <= set(frame.columns) or frame.empty:
        raise ValueError(
            "CSV must contain snapshot_date, product_id, quantity_on_hand and data rows"
        )
    products = {
        item.external_id: item
        for item in session.scalars(select(Product).where(Product.company_id == company_id))
    }
    created = updated = rejected = 0
    errors: list[str] = []
    for row_number, row in frame.iterrows():
        try:
            external_id = str(row["product_id"]).strip()
            product = products.get(external_id)
            if product is None:
                raise ValueError(f"Unknown product external_id: {external_id}")
            snapshot_date = date.fromisoformat(str(row["snapshot_date"]))
            raw_quantity = str(row["quantity_on_hand"])
            if not raw_quantity.isdigit():
                raise ValueError("quantity_on_hand must be a non-negative integer")
            quantity = int(raw_quantity)
            snapshot = session.scalar(
                select(InventorySnapshot).where(
                    InventorySnapshot.company_id == company_id,
                    InventorySnapshot.product_id == product.id,
                    InventorySnapshot.snapshot_date == snapshot_date,
                )
            )
            if snapshot is None:
                session.add(
                    InventorySnapshot(
                        company_id=company_id,
                        product_id=product.id,
                        snapshot_date=snapshot_date,
                        quantity_on_hand=quantity,
                    )
                )
                created += 1
            else:
                snapshot.quantity_on_hand = quantity
                updated += 1
        except ValueError as error:
            rejected += 1
            if len(errors) < 100:
                errors.append(f"Row {row_number + 2}: {error}")
    session.commit()
    return InventoryImportSummary(
        rows_received=len(frame),
        rows_imported=len(frame) - rejected,
        rows_rejected=rejected,
        snapshots_created=created,
        snapshots_updated=updated,
        errors=errors,
    )
