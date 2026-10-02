from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db_session
from app.main import app

client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sales-snap-api"}
    assert response.headers["x-request-id"]


def test_request_id_is_propagated_or_replaced() -> None:
    propagated = client.get("/api/v1/health", headers={"X-Request-ID": "portfolio-check-1"})
    replaced = client.get("/api/v1/health", headers={"X-Request-ID": "invalid id with spaces"})

    assert propagated.headers["x-request-id"] == "portfolio-check-1"
    assert replaced.headers["x-request-id"] != "invalid id with spaces"


def test_readiness_reports_database_availability_without_details() -> None:
    class ReadySession:
        def execute(self, _statement):
            return None

    app.dependency_overrides[get_db_session] = lambda: ReadySession()
    try:
        response = client.get("/api/v1/readiness")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "sales-snap-api",
        "database": "available",
    }


def test_readiness_sanitizes_database_failure() -> None:
    class FailedSession:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, Exception("private database detail"))

    app.dependency_overrides[get_db_session] = lambda: FailedSession()
    try:
        response = client.get("/api/v1/readiness")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "sales-snap-api",
        "database": "unavailable",
    }
    assert "private database detail" not in response.text
