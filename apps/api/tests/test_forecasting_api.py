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


def test_forecast_endpoints_are_tenant_scoped_and_handle_insufficient_history() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company_a, company_b = Company(name="A"), Company(name="B")
        user_a = User(
            company=company_a, email="a@test.com", password_hash=hash_password("password")
        )
        dataset_a = Dataset(company=company_a, name="A.csv", source_type="csv", status="completed")
        dataset_b = Dataset(company=company_b, name="B.csv", source_type="csv", status="completed")
        product_a = Product(company=company_a, external_id="A", name="A product")
        product_b = Product(company=company_b, external_id="B", name="B product")
        session.add_all([user_a, dataset_a, dataset_b, product_a, product_b])
        session.flush()
        for index in range(30):
            session.add(
                Sale(
                    company_id=company_a.id,
                    dataset_id=dataset_a.id,
                    product_id=product_a.id,
                    sale_date=date(2026, 1, 1) + timedelta(days=index),
                    quantity=Decimal(index % 5 + 1),
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
                quantity=Decimal("1"),
                unit_price=Decimal("1"),
                revenue=Decimal("1"),
            )
        )
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            headers = {"Authorization": f"Bearer {create_access_token(user_a.id)}"}
            products = client.get("/api/v1/analytics/forecast/products", headers=headers)
            forecast = client.get(
                f"/api/v1/analytics/forecast/products/{product_a.id}?horizon=7", headers=headers
            )
            forbidden = client.get(
                f"/api/v1/analytics/forecast/products/{product_b.id}", headers=headers
            )
            invalid_horizon = client.get(
                f"/api/v1/analytics/forecast/products/{product_a.id}?horizon=5", headers=headers
            )
        finally:
            app.dependency_overrides.clear()

    assert products.status_code == 200
    assert products.json() == [
        {
            "id": str(product_a.id),
            "external_id": "A",
            "name": "A product",
            "observations": 30,
            "forecast_available": True,
        }
    ]
    assert forecast.status_code == 200, forecast.text
    assert forecast.json()["status"] == "ok"
    assert len(forecast.json()["forecast"]) == 7
    assert forbidden.status_code == 404
    assert invalid_horizon.status_code == 422
