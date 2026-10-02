from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models import (
    ChatConversation,
    Company,
    Dataset,
    InventorySnapshot,
    Product,
    User,
)
from app.services.ai_chat import get_conversation
from app.services.dataset_import import get_dataset
from app.services.forecasting import get_forecast_product
from app.services.inventory_import import get_latest_inventory_snapshot


def test_tenant_owned_resources_reject_foreign_ids_and_external_id_collisions() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company_a, company_b = Company(name="A"), Company(name="B")
        user_a = User(company=company_a, email="a@example.test", password_hash="unused")
        user_b = User(company=company_b, email="b@example.test", password_hash="unused")
        dataset_b = Dataset(
            company=company_b,
            name="foreign.csv",
            source_type="csv",
            status="completed",
        )
        product_a = Product(company=company_a, external_id="P001", name="A product")
        product_b = Product(company=company_b, external_id="P001", name="B product")
        conversation_b = ChatConversation(company=company_b, user=user_b, title="Private")
        session.add_all(
            [user_a, user_b, dataset_b, product_a, product_b, conversation_b]
        )
        session.flush()
        session.add(
            InventorySnapshot(
                company=company_b,
                product=product_b,
                snapshot_date=date(2026, 10, 2),
                quantity_on_hand=99,
            )
        )
        session.commit()

        assert get_dataset(session, company_a.id, dataset_b.id) is None
        assert get_forecast_product(session, company_a.id, product_b.id) is None
        assert get_latest_inventory_snapshot(session, company_a.id, product_b.id) is None
        assert get_conversation(session, company_a.id, user_a.id, conversation_b.id) is None
        assert product_a.external_id == product_b.external_id
    engine.dispose()
