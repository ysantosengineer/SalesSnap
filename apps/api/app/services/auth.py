import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import Company, RefreshToken, User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(session: Session, company_name: str, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    if session.scalar(select(User).where(User.email == normalized_email)) is not None:
        raise ValueError("Email already registered")
    company = Company(name=company_name.strip())
    user = User(company=company, email=normalized_email, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def issue_session(session: Session, user: User) -> tuple[str, str]:
    refresh_token, expires_at = create_refresh_token(user.id)
    session.add(
        RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires_at)
    )
    session.commit()
    return create_access_token(user.id), refresh_token


def rotate_refresh_token(session: Session, refresh_token: str) -> tuple[User, str, str] | None:
    from app.core.security import decode_token

    payload = decode_token(refresh_token, "refresh")
    token = session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    if token is None or token.revoked_at is not None or is_expired(token.expires_at):
        return None
    user = session.scalar(
        select(User)
        .options(joinedload(User.company))
        .where(User.id == uuid.UUID(str(payload["sub"])))
    )
    if user is None or not user.is_active:
        return None
    token.revoked_at = datetime.now(UTC)
    access_token, new_refresh_token = issue_session(session, user)
    return user, access_token, new_refresh_token


def is_expired(expires_at: datetime) -> bool:
    """Compare refresh expiry timestamps from databases with different timezone support."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime.now(UTC)


def revoke_refresh_token(session: Session, refresh_token: str) -> None:
    token = session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        session.commit()
