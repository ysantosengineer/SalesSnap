from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db_session
from app.main import app
from app.models import Company, Dataset, InventorySnapshot, Product, Sale, User


def test_stock_risk_endpoints_are_tenant_scoped() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company_a, company_b = Company(name="A"), Company(name="B")
        user_a = User(
            company=company_a, email="a@test.com", password_hash=hash_password("password")
        )
        dataset_a = Dataset(company=company_a, name="a.csv", source_type="csv", status="completed")
        dataset_b = Dataset(company=company_b, name="b.csv", source_type="csv", status="completed")
        product_a = Product(company=company_a, external_id="P001", name="A product")
        product_b = Product(company=company_b, external_id="P001", name="B product")
        session.add_all([user_a, dataset_a, dataset_b, product_a, product_b])
        session.flush()
        for index in range(30):
            for company, dataset, product in (
                (company_a, dataset_a, product_a),
                (company_b, dataset_b, product_b),
            ):
                session.add(
                    Sale(
                        company_id=company.id,
                        dataset_id=dataset.id,
                        product_id=product.id,
                        sale_date=date(2026, 1, 1) + timedelta(days=index),
                        quantity=Decimal("10"),
                        unit_price=Decimal("1"),
                        revenue=Decimal("10"),
                    )
                )
        session.add(
            InventorySnapshot(
                company_id=company_a.id,
                product_id=product_a.id,
                snapshot_date=date(2026, 2, 1),
                quantity_on_hand=50,
            )
        )
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            headers = {"Authorization": f"Bearer {create_access_token(user_a.id)}"}
            listing = client.get("/api/v1/analytics/stock-risk?horizon=7", headers=headers)
            summary = client.get("/api/v1/analytics/stock-risk/summary?horizon=7", headers=headers)
            detail = client.get(
                f"/api/v1/analytics/stock-risk/products/{product_a.id}?horizon=7", headers=headers
            )
            forbidden = client.get(
                f"/api/v1/analytics/stock-risk/products/{product_b.id}", headers=headers
            )
        finally:
            app.dependency_overrides.clear()

    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["risk_level"] == "critical"
    assert summary.json()["critical"] == 1
    assert detail.json()["current_stock"] == "50"
    assert len(detail.json()["projection"]) == 7
    assert forbidden.status_code == 404
