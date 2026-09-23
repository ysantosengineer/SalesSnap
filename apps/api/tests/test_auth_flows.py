import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.auth import get_current_company_id
from app.core.security import create_access_token
from app.db.session import Base, get_db_session
from app.main import app
from app.models import RefreshToken
from app.services.auth import (
    issue_session,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)


def create_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_refresh_rotation_rejects_reused_and_revoked_tokens() -> None:
    with create_session() as session:
        user = register_user(session, "Acme", "owner@acme.com", "secure-password")
        _, original_refresh_token = issue_session(session, user)

        rotated = rotate_refresh_token(session, original_refresh_token)
        assert rotated is not None
        _, _, rotated_refresh_token = rotated
        assert rotated_refresh_token != original_refresh_token
        assert rotate_refresh_token(session, original_refresh_token) is None

        revoke_refresh_token(session, rotated_refresh_token)
        assert rotate_refresh_token(session, rotated_refresh_token) is None


def test_logout_revokes_cookie_token_and_clears_cookie() -> None:
    with create_session() as session:
        user = register_user(session, "Acme", "owner@acme.com", "secure-password")
        _, refresh_token = issue_session(session, user)

        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            client.cookies.set("refresh_token", refresh_token, path="/api/v1/auth")
            response = client.post("/api/v1/auth/logout")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 204
        assert "max-age=0" in response.headers["set-cookie"].lower()
        stored_token = session.query(RefreshToken).one()
        assert stored_token.revoked_at is not None
        assert rotate_refresh_token(session, refresh_token) is None


def test_authenticated_user_keeps_its_company_context() -> None:
    with create_session() as session:
        acme_user = register_user(session, "Acme", "owner@acme.com", "secure-password")
        beta_user = register_user(session, "Beta", "owner@beta.com", "secure-password")

        app.dependency_overrides[get_db_session] = lambda: session
        try:
            client = TestClient(app)
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {create_access_token(acme_user.id)}"},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["company"]["id"] == str(acme_user.company_id)
        assert response.json()["company"]["id"] != str(beta_user.company_id)
        assert get_current_company_id(acme_user) == uuid.UUID(response.json()["company"]["id"])
