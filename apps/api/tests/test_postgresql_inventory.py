import os
from datetime import date
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import get_settings
from app.models import Company, InventorySnapshot, Product
from app.services.inventory_import import get_latest_inventory_snapshot, import_inventory_csv


@pytest.mark.postgres
def test_inventory_snapshots_migrate_persist_upsert_and_isolate_postgres() -> None:
    url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if url is None:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    directory = Path(__file__).parents[1]
    config = Config(str(directory / "alembic.ini"))
    config.set_main_option("script_location", str(directory / "alembic"))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with Session(create_engine(url)) as session:
            a, b = Company(name="A"), Company(name="B")
            pa, pb = (
                Product(company=a, external_id="P", name="A"),
                Product(company=b, external_id="P", name="B"),
            )
            session.add_all([a, b, pa, pb])
            session.commit()
            import_inventory_csv(
                session,
                a.id,
                b"snapshot_date,product_id,quantity_on_hand\n2026-09-28,P,150\n2026-09-29,P,110\n",
            )
            import_inventory_csv(
                session, b.id, b"snapshot_date,product_id,quantity_on_hand\n2026-09-29,P,999\n"
            )
            assert get_latest_inventory_snapshot(session, a.id, pa.id).quantity_on_hand == 110
            assert get_latest_inventory_snapshot(session, b.id, pb.id).quantity_on_hand == 999
            session.add(
                InventorySnapshot(
                    company_id=a.id,
                    product_id=pa.id,
                    snapshot_date=date(2026, 9, 29),
                    quantity_on_hand=-1,
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
    finally:
        command.downgrade(config, "base")
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
