from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok", "service": "sales-snap-api"}


@router.get("/readiness")
def get_readiness(
    response: Response, session: Session = Depends(get_db_session)
) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "service": "sales-snap-api", "database": "unavailable"}
    return {"status": "ready", "service": "sales-snap-api", "database": "available"}
