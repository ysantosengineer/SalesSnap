import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import Base
from app.services.auth import authenticate_user, register_user


def test_password_hashing_and_jwt_types() -> None:
    password_hash = hash_password("secure-password")
    assert password_hash != "secure-password"
    assert verify_password("secure-password", password_hash)
    assert not verify_password("wrong-password", password_hash)
    user_id = uuid.uuid4()
    assert decode_token(create_access_token(user_id), "access")["sub"] == str(user_id)
    refresh_token, _ = create_refresh_token(user_id)
    assert decode_token(refresh_token, "refresh")["sub"] == str(user_id)


def test_registration_normalizes_email_and_authenticates() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = register_user(session, "Acme", "Owner@Acme.COM", "secure-password")
        assert user.email == "owner@acme.com"
        assert user.company.name == "Acme"
        assert authenticate_user(session, "OWNER@ACME.COM", "secure-password") == user
        assert authenticate_user(session, "owner@acme.com", "wrong-password") is None
        user.is_active = False
        session.commit()
        assert authenticate_user(session, "owner@acme.com", "secure-password") is None
