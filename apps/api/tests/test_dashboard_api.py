from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db_session
from app.main import app
from app.models import Company, Customer, Dataset, Product, Sale, User


def create_session() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_sale(session: Session, company: Company, revenue: str) -> None:
    dataset = Dataset(company=company, name="sales.csv", source_type="csv", status="completed")
    product = Product(company=company, external_id="P1", name="Mouse")
    customer = Customer(company=company, external_id="C1")
    session.add_all([dataset, product, customer])
    session.flush()
    session.add(
        Sale(
            company_id=company.id,
            dataset_id=dataset.id,
            product_id=product.id,
            customer_id=customer.id,
            sale_date=date(2026, 9, 1),
            quantity=Decimal("1"),
            unit_price=Decimal(revenue),
            revenue=Decimal(revenue),
        )
    )


def test_dashboard_api_uses_authenticated_tenant_and_validates_dates() -> None:
    with create_session() as session:
        company_a = Company(name="Acme")
        company_b = Company(name="Beta")
        user_a = User(
            company=company_a, email="a@acme.test", password_hash=hash_password("password")
        )
        session.add_all([user_a, company_b])
        session.flush()
        seed_sale(session, company_a, "100")
        seed_sale(session, company_b, "900")
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            headers = {"Authorization": f"Bearer {create_access_token(user_a.id)}"}
            summary = client.get("/api/v1/dashboard/summary?company_id=ignored", headers=headers)
            invalid_range = client.get(
                "/api/v1/dashboard/summary?start_date=2026-10-01&end_date=2026-09-01",
                headers=headers,
            )
        finally:
            app.dependency_overrides.clear()

        assert summary.status_code == 200
        assert summary.json()["total_revenue"] == "100.00"
        assert invalid_range.status_code == 400
