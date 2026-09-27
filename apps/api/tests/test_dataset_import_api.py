import uuid
from asyncio import run

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.datasets import UPLOAD_READ_CHUNK_BYTES, read_limited_upload
from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db_session
from app.main import app
from app.models import Company, Dataset, User

CSV_CONTENT = (
    b"date,customer_id,product_id,product_name,quantity,unit_price\n"
    b"2026-09-01,C001,P001,Mouse,2,149.90\n"
)


class ChunkedUpload:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.read_calls = 0
        self.was_closed = False

    async def read(self, size: int) -> bytes:
        assert size == UPLOAD_READ_CHUNK_BYTES
        self.read_calls += 1
        return self.chunks.pop(0) if self.chunks else b""

    async def close(self) -> None:
        self.was_closed = True


def test_limited_upload_reader_stops_before_reading_remaining_file() -> None:
    upload = ChunkedUpload([b"four", b"x", b"unread"])

    with pytest.raises(HTTPException) as failure:
        run(read_limited_upload(upload, 4))  # type: ignore[arg-type]

    assert getattr(failure.value, "status_code", None) == 413
    assert upload.read_calls == 2
    assert upload.chunks == [b"unread"]
    assert upload.was_closed


def test_middleware_rejects_clearly_oversized_multipart_before_route_processing() -> None:
    oversized_content = b"x" * (10 * 1024 * 1024 + 64 * 1024 + 1)

    response = TestClient(app).post(
        "/api/v1/datasets/import",
        files={"file": ("sales.csv", oversized_content, "text/csv")},
    )

    assert response.status_code == 413


def create_session() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_authenticated_upload_uses_current_users_company() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        user = User(
            company=company,
            email="owner@acme.test",
            password_hash=hash_password("password"),
        )
        session.add(user)
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            response = TestClient(app).post(
                "/api/v1/datasets/import",
                headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
                files={"file": ("sales.csv", CSV_CONTENT, "text/csv")},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "completed"
        assert session.get(Dataset, uuid.UUID(body["dataset_id"])).company_id == company.id


def test_dataset_endpoint_prevents_cross_tenant_access() -> None:
    with create_session() as session:
        company_a = Company(name="Acme")
        company_b = Company(name="Beta")
        user_a = User(
            company=company_a, email="a@acme.test", password_hash=hash_password("password")
        )
        user_b = User(
            company=company_b, email="b@beta.test", password_hash=hash_password("password")
        )
        dataset = Dataset(
            company=company_a, name="sales.csv", source_type="csv", status="completed"
        )
        session.add_all([user_a, user_b, dataset])
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            response = TestClient(app).get(
                f"/api/v1/datasets/{dataset.id}",
                headers={"Authorization": f"Bearer {create_access_token(user_b.id)}"},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404


def test_import_rejects_non_csv_file_before_processing() -> None:
    with create_session() as session:
        company = Company(name="Acme")
        user = User(
            company=company,
            email="owner@acme.test",
            password_hash=hash_password("password"),
        )
        session.add(user)
        session.commit()
        app.dependency_overrides[get_db_session] = lambda: session
        try:
            response = TestClient(app).post(
                "/api/v1/datasets/import",
                headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
                files={"file": ("sales.xlsx", b"not a csv", "application/vnd.ms-excel")},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 415
