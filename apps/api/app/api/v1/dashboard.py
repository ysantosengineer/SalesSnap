from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.dashboard import (
    DashboardOverview,
    DashboardSummary,
    RevenueSeriesPoint,
    TopProduct,
)
from app.services.dashboard import get_overview, get_revenue_series, get_summary, get_top_products

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )


@router.get("/summary", response_model=DashboardSummary)
def summary(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardSummary:
    validate_date_range(start_date, end_date)
    return get_summary(session, current_user.company_id, start_date, end_date)


@router.get("/revenue-series", response_model=list[RevenueSeriesPoint])
def revenue_series(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[RevenueSeriesPoint]:
    validate_date_range(start_date, end_date)
    return get_revenue_series(session, current_user.company_id, start_date, end_date)


@router.get("/top-products", response_model=list[TopProduct])
def top_products(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[TopProduct]:
    validate_date_range(start_date, end_date)
    return get_top_products(session, current_user.company_id, start_date, end_date, limit)


@router.get("/overview", response_model=DashboardOverview)
def overview(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DashboardOverview:
    validate_date_range(start_date, end_date)
    return get_overview(session, current_user.company_id, start_date, end_date)
