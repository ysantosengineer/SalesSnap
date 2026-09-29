
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import Company, InventorySnapshot, Product
from app.services.inventory_import import get_latest_inventory_snapshot, import_inventory_csv


def setup() -> tuple[Session, Company, Company, Product, Product]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    a, b = Company(name="A"), Company(name="B")
    pa, pb = (
        Product(company=a, external_id="P001", name="A"),
        Product(company=b, external_id="P001", name="B"),
    )
    session.add_all([a, b, pa, pb])
    session.commit()
    return session, a, b, pa, pb


def test_inventory_csv_validates_tenant_rows_and_upserts() -> None:
    session, a, b, pa, pb = setup()
    first = import_inventory_csv(
        session,
        a.id,
        b"snapshot_date,product_id,quantity_on_hand\n2026-09-29,P001,100\n2026-09-29,P999,2\n2026-99-99,P001,3\n",
    )
    second = import_inventory_csv(
        session, a.id, b"snapshot_date,product_id,quantity_on_hand\n2026-09-29,P001,120\n"
    )
    assert (first.rows_received, first.rows_imported, first.rows_rejected) == (3, 1, 2)
    assert "P999" in first.errors[0]
    assert second.snapshots_updated == 1
    assert session.query(InventorySnapshot).filter_by(company_id=a.id).count() == 1
    assert get_latest_inventory_snapshot(session, a.id, pa.id).quantity_on_hand == 120
    assert get_latest_inventory_snapshot(session, b.id, pb.id) is None


@pytest.mark.parametrize(
    "content",
    [
        b"snapshot_date,product_id\n2026-09-29,P001\n",
        b"snapshot_date,product_id,quantity_on_hand\n",
    ],
)
def test_inventory_csv_rejects_structural_errors(content: bytes) -> None:
    session, a, *_ = setup()
    with pytest.raises(ValueError):
        import_inventory_csv(session, a.id, content)
    assert session.query(InventorySnapshot).count() == 0


def test_latest_snapshot_does_not_sum_history_or_cross_tenants() -> None:
    session, a, b, pa, pb = setup()
    import_inventory_csv(
        session,
        a.id,
        b"snapshot_date,product_id,quantity_on_hand\n2026-09-28,P001,150\n2026-09-29,P001,110\n",
    )
    import_inventory_csv(
        session, b.id, b"snapshot_date,product_id,quantity_on_hand\n2026-09-30,P001,999\n"
    )
    assert get_latest_inventory_snapshot(session, a.id, pa.id).quantity_on_hand == 110
    assert get_latest_inventory_snapshot(session, b.id, pb.id).quantity_on_hand == 999
