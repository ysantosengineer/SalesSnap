from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db_session
from app.main import app
from app.models import Company, User


def test_ai_insights_endpoint_requires_authentication_and_handles_disabled_provider(
    monkeypatch,
) -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        company = Company(name="A")
        user = User(company=company, email="a@test.com", password_hash=hash_password("password"))
        session.add_all([company, user])
        session.commit()
        monkeypatch.setenv("AI_INSIGHTS_ENABLED", "false")
        get_settings.cache_clear()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            unauthenticated = client.post("/api/v1/analytics/ai-insights/generate", json={})
            disabled = client.post(
                "/api/v1/analytics/ai-insights/generate",
                json={},
                headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
            )
        finally:
            app.dependency_overrides.clear()
            get_settings.cache_clear()
    assert unauthenticated.status_code == 401
    assert disabled.status_code == 503
