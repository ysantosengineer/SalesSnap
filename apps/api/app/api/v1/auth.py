import uuid

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import cookie_secure, decode_token
from app.db.session import get_db_session
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, SessionResponse, UserResponse
from app.services.auth import authenticate_user, issue_session, register_user, revoke_refresh_token, rotate_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def to_user_response(user: User) -> UserResponse:
    return UserResponse.model_validate({"id": user.id, "email": user.email, "company": user.company})


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", secure=cookie_secure(), path="/api/v1/auth")


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), session: Session = Depends(get_db_session)) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(str(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from None
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    return user


def get_current_company_id(current_user: User = Depends(get_current_user)) -> uuid.UUID:
    return current_user.company_id


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, session: Session = Depends(get_db_session)) -> SessionResponse:
    try:
        user = register_user(session, payload.company_name, str(payload.email), payload.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from None
    access_token, refresh_token = issue_session(session, user)
    set_refresh_cookie(response, refresh_token)
    return SessionResponse(access_token=access_token, user=to_user_response(user))


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, response: Response, session: Session = Depends(get_db_session)) -> SessionResponse:
    user = authenticate_user(session, str(payload.email), payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token = issue_session(session, user)
    set_refresh_cookie(response, refresh_token)
    return SessionResponse(access_token=access_token, user=to_user_response(user))


@router.post("/refresh", response_model=SessionResponse)
def refresh(response: Response, refresh_token: str | None = Cookie(default=None), session: Session = Depends(get_db_session)) -> SessionResponse:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        refreshed = rotate_refresh_token(session, refresh_token)
    except jwt.PyJWTError:
        refreshed = None
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user, access_token, next_refresh_token = refreshed
    set_refresh_cookie(response, next_refresh_token)
    return SessionResponse(access_token=access_token, user=to_user_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, refresh_token: str | None = Cookie(default=None), session: Session = Depends(get_db_session)) -> Response:
    if refresh_token is not None:
        revoke_refresh_token(session, refresh_token)
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return response


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)
