from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.rate_limit import InMemoryRateLimiter, rate_limiter
from app.db.session import Base, get_db_session
from app.main import app


def test_rate_limiter_isolates_subjects_and_categories() -> None:
    now = [0.0]
    limiter = InMemoryRateLimiter(clock=lambda: now[0], window_seconds=60)

    assert limiter.consume("ai", "user-a", 2) is None
    assert limiter.consume("ai", "user-a", 2) is None
    assert limiter.consume("ai", "user-a", 2) == 61
    assert limiter.consume("ai", "user-b", 2) is None
    assert limiter.consume("import", "user-a", 2) is None

    now[0] = 61
    assert limiter.consume("ai", "user-a", 2) is None


def test_auth_endpoint_returns_429_with_retry_after(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        app.dependency_overrides[get_db_session] = lambda: session
        settings = get_settings()
        monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 2)
        rate_limiter.clear()
        try:
            client = TestClient(app)
            payload = {"email": "unknown@example.com", "password": "invalid-password"}
            assert client.post("/api/v1/auth/login", json=payload).status_code == 401
            assert client.post("/api/v1/auth/login", json=payload).status_code == 401
            blocked = client.post("/api/v1/auth/login", json=payload)
        finally:
            rate_limiter.clear()
            app.dependency_overrides.clear()
    engine.dispose()

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Request rate limit exceeded. Please try again later."
    assert int(blocked.headers["retry-after"]) >= 1
