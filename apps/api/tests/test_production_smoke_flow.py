from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.db.session import Base, get_db_session
from app.main import app


def sales_csv(days: int = 35) -> bytes:
    rows = ["date,customer_id,product_id,product_name,quantity,unit_price"]
    start = date(2026, 1, 1)
    for index in range(days):
        sale_date = start + timedelta(days=index)
        rows.append(f"{sale_date.isoformat()},C001,P001,Demo Product,{index % 5 + 1},10.00")
    return ("\n".join(rows) + "\n").encode()


def test_authenticated_product_smoke_flow_with_ai_disabled(monkeypatch) -> None:
    """Exercise the production-facing happy path without external provider calls."""

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setenv("AI_INSIGHTS_ENABLED", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    rate_limiter.clear()

    with Session(engine) as session:
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            with TestClient(app) as client:
                registration = client.post(
                    "/api/v1/auth/register",
                    json={
                        "company_name": "Production Smoke",
                        "email": "owner@smoke.example",
                        "password": "smoke-password",
                    },
                )
                assert registration.status_code == 201, registration.text
                assert client.post("/api/v1/auth/logout").status_code == 204

                login = client.post(
                    "/api/v1/auth/login",
                    json={"email": "owner@smoke.example", "password": "smoke-password"},
                )
                assert login.status_code == 200, login.text
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                imported = client.post(
                    "/api/v1/datasets/import",
                    headers=headers,
                    files={"file": ("sales.csv", sales_csv(), "text/csv")},
                )
                assert imported.status_code == 201, imported.text
                assert imported.json()["rows_imported"] == 35

                summary = client.get("/api/v1/dashboard/summary", headers=headers)
                assert summary.status_code == 200
                assert summary.json()["sales_records"] == 35

                rfm = client.get("/api/v1/analytics/rfm/summary", headers=headers)
                assert rfm.status_code == 200
                assert rfm.json()["total_customers"] == 1

                products = client.get("/api/v1/analytics/forecast/products", headers=headers)
                assert products.status_code == 200
                product_id = products.json()[0]["id"]
                forecast = client.get(
                    f"/api/v1/analytics/forecast/products/{product_id}?horizon=7",
                    headers=headers,
                )
                assert forecast.status_code == 200, forecast.text
                assert forecast.json()["status"] == "ok"

                anomalies = client.get("/api/v1/analytics/anomalies", headers=headers)
                assert anomalies.status_code == 200, anomalies.text

                inventory = client.post(
                    "/api/v1/inventory/import",
                    headers=headers,
                    files={
                        "file": (
                            "inventory.csv",
                            b"snapshot_date,product_id,quantity_on_hand\n2026-02-05,P001,25\n",
                            "text/csv",
                        )
                    },
                )
                assert inventory.status_code == 200, inventory.text
                assert inventory.json()["rows_imported"] == 1

                stock_risk = client.get(
                    f"/api/v1/analytics/stock-risk/products/{product_id}?horizon=7",
                    headers=headers,
                )
                assert stock_risk.status_code == 200, stock_risk.text
                assert stock_risk.json()["status"] == "success"

                insights = client.post(
                    "/api/v1/analytics/ai-insights/generate", json={}, headers=headers
                )
                assert insights.status_code == 503

                conversation = client.post(
                    "/api/v1/chat/conversations", json={}, headers=headers
                )
                assert conversation.status_code == 201
                chat = client.post(
                    f"/api/v1/chat/conversations/{conversation.json()['id']}/messages",
                    json={"message": "Summarize my sales."},
                    headers=headers,
                )
                assert chat.status_code == 503
                assert chat.json()["detail"] == "AI Chat is not configured for this environment."

                assert client.post("/api/v1/auth/logout").status_code == 204
                assert client.post("/api/v1/auth/refresh").status_code == 401
        finally:
            app.dependency_overrides.clear()
            get_settings.cache_clear()
            rate_limiter.clear()
