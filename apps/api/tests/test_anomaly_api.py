from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db_session
from app.main import app
from app.models import Company, Dataset, Product, Sale, User


def test_anomaly_endpoints_are_tenant_scoped() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company_a, company_b = Company(name="A"), Company(name="B")
        user = User(
            company=company_a, email="a@example.test", password_hash=hash_password("password")
        )
        dataset_a = Dataset(company=company_a, name="A", source_type="csv", status="completed")
        dataset_b = Dataset(company=company_b, name="B", source_type="csv", status="completed")
        product_a = Product(company=company_a, external_id="A", name="A")
        product_b = Product(company=company_b, external_id="B", name="B")
        session.add_all([user, dataset_a, dataset_b, product_a, product_b])
        session.flush()
        for index in range(30):
            session.add(
                Sale(
                    company_id=company_a.id,
                    dataset_id=dataset_a.id,
                    product_id=product_a.id,
                    sale_date=date(2026, 1, 1) + timedelta(days=index),
                    quantity=Decimal("150" if index == 29 else "30"),
                    unit_price=Decimal("1"),
                    revenue=Decimal("1"),
                )
            )
        session.add(
            Sale(
                company_id=company_b.id,
                dataset_id=dataset_b.id,
                product_id=product_b.id,
                sale_date=date(2026, 1, 1),
                quantity=Decimal("999"),
                unit_price=Decimal("1"),
                revenue=Decimal("1"),
            )
        )
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
            detail = client.get(
                f"/api/v1/analytics/anomalies/products/{product_a.id}", headers=headers
            )
            summary = client.get("/api/v1/analytics/anomalies/summary", headers=headers)
            forbidden = client.get(
                f"/api/v1/analytics/anomalies/products/{product_b.id}", headers=headers
            )
        finally:
            app.dependency_overrides.clear()
    assert detail.status_code == 200
    assert detail.json()["items"][-1]["direction"] == "spike"
    assert summary.json()["spikes"] >= 1
    assert forbidden.status_code == 404
