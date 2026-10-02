import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.auth import get_current_user
from app.db.session import Base, get_db_session
from app.integrations.openai_client import (
    AIProviderDisabledError,
    AIProviderUnavailableError,
    ChatProviderResponse,
    ChatToolCall,
)
from app.main import app
from app.models import ChatMessage, User
from app.services.auth import register_user


@pytest.fixture
def chat_api():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        owner = register_user(session, "A", "owner@a.test", "test-password")
        outsider = register_user(session, "B", "other@b.test", "test-password")
        colleague = User(
            company_id=owner.company_id,
            email="colleague@a.test",
            password_hash="unused",
        )
        session.add(colleague)
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: owner
        try:
            with TestClient(app) as client:
                yield client, session, owner, colleague, outsider
        finally:
            app.dependency_overrides.clear()
    engine.dispose()


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/conversations"),
        ("post", "/conversations"),
        ("get", f"/conversations/{uuid.uuid4()}"),
        ("post", f"/conversations/{uuid.uuid4()}/messages"),
    ],
)
def test_all_chat_endpoints_require_authentication(chat_api, method, path):
    client, *_ = chat_api
    app.dependency_overrides.pop(get_current_user)
    assert getattr(client, method)(f"/api/v1/chat{path}").status_code == 401


def test_conversation_message_roundtrip_and_evidence_reload(chat_api, monkeypatch):
    client, session, *_ = chat_api
    created = client.post("/api/v1/chat/conversations", json={})
    assert created.status_code == 201
    conversation = created.json()
    responses = iter(
        [
            ChatProviderResponse("", [ChatToolCall("c1", "get_sales_summary", {})]),
            ChatProviderResponse("Total revenue is zero.", []),
        ]
    )
    monkeypatch.setattr("app.services.ai_chat.generate_chat_response", lambda *_: next(responses))
    base = f"/api/v1/chat/conversations/{conversation['id']}"
    response = client.post(f"{base}/messages", json={"message": "  Revenue?  "})
    assert response.status_code == 200
    assert response.json()["tools_used"] == ["get_sales_summary"]
    assert any(item["label"] == "total_revenue" for item in response.json()["evidence"])
    loaded = client.get(base).json()
    assert [item["role"] for item in loaded["messages"]] == ["user", "assistant"]
    assert loaded["messages"][0]["content"] == "Revenue?"
    assert loaded["messages"][1]["evidence"] == response.json()["evidence"]
    assert loaded["title"] == "Revenue?"
    assert len(client.get("/api/v1/chat/conversations").json()) == 1
    assert session.query(ChatMessage).count() == 2


@pytest.mark.parametrize("identity", ["colleague", "outsider"])
def test_get_send_and_list_enforce_real_ownership(chat_api, identity):
    client, session, owner, colleague, outsider = chat_api
    created = client.post("/api/v1/chat/conversations", json={}).json()
    other = colleague if identity == "colleague" else outsider
    app.dependency_overrides[get_current_user] = lambda: other
    path = f"/api/v1/chat/conversations/{created['id']}"
    assert client.get(path).status_code == 404
    assert client.post(f"{path}/messages", json={"message": "secret?"}).status_code == 404
    assert client.get("/api/v1/chat/conversations").json() == []
    assert session.query(ChatMessage).count() == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": " \n "},
        {"message": "x" * 4001},
        {"message": "hello", "company_id": str(uuid.uuid4())},
        {"message": "hello", "role": "system"},
    ],
)
def test_invalid_messages_never_persist(chat_api, payload):
    client, session, *_ = chat_api
    created = client.post("/api/v1/chat/conversations", json={}).json()
    response = client.post(f"/api/v1/chat/conversations/{created['id']}/messages", json=payload)
    assert response.status_code == 422
    assert session.query(ChatMessage).count() == 0


@pytest.mark.parametrize(
    "error,detail",
    [
        (AIProviderDisabledError, "AI Chat is not configured for this environment."),
        (AIProviderUnavailableError, "I couldn't analyze your data right now."),
    ],
)
def test_failures_retain_question_and_return_safe_message(chat_api, monkeypatch, error, detail):
    client, session, *_ = chat_api
    created = client.post("/api/v1/chat/conversations", json={}).json()

    def fail(*_):
        raise error("sensitive transport detail")

    monkeypatch.setattr("app.services.ai_chat.generate_chat_response", fail)
    response = client.post(
        f"/api/v1/chat/conversations/{created['id']}/messages",
        json={"message": "Sales?"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": detail}
    assert [item.role for item in session.query(ChatMessage)] == ["user"]


def test_invalid_provider_tool_is_controlled_error_not_500(chat_api, monkeypatch):
    client, *_ = chat_api
    created = client.post("/api/v1/chat/conversations", json={}).json()
    monkeypatch.setattr(
        "app.services.ai_chat.generate_chat_response",
        lambda *_: ChatProviderResponse("", [ChatToolCall("c1", "execute_sql", {})]),
    )
    response = client.post(
        f"/api/v1/chat/conversations/{created['id']}/messages",
        json={"message": "Hi"},
    )
    assert response.status_code == 503


def test_conversation_listing_is_bounded_and_paginated(chat_api):
    client, *_ = chat_api
    for title in ("First", "Second", "Third"):
        assert client.post("/api/v1/chat/conversations", json={"title": title}).status_code == 201

    response = client.get("/api/v1/chat/conversations?limit=1&offset=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert client.get("/api/v1/chat/conversations?limit=101").status_code == 422
