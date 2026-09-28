from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.rfm import RfmCustomerPage, RfmSegmentSummary, RfmSummary
from app.services.rfm import SEGMENTS, analyze_rfm

router = APIRouter(prefix="/analytics/rfm", tags=["analytics"])


def result(
    session: Session, user: User, start: date | None, end: date | None, reference: date | None
):
    if start and end and start > end:
        raise HTTPException(400, "start_date must be before end_date")
    try:
        return analyze_rfm(session, user.company_id, start, end, reference)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@router.get("/summary", response_model=RfmSummary)
def summary(
    start_date: date | None = None,
    end_date: date | None = None,
    reference_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> RfmSummary:
    items, reference = result(session, current_user, start_date, end_date, reference_date)
    total_revenue = sum((item.monetary for item in items), Decimal("0"))
    segments = [
        RfmSegmentSummary(
            segment=name,
            customers=len(group),
            percentage=Decimal(len(group) * 100) / len(items),
            revenue=sum((item.monetary for item in group), Decimal("0")),
            revenue_percentage=(
                sum((item.monetary for item in group), Decimal("0")) * 100 / total_revenue
                if total_revenue
                else Decimal("0")
            ),
        )
        for name in SEGMENTS
        if (group := [item for item in items if item.segment == name])
    ]
    return RfmSummary(total_customers=len(items), reference_date=reference, segments=segments)


@router.get("/customers", response_model=RfmCustomerPage)
def customers(
    start_date: date | None = None,
    end_date: date | None = None,
    reference_date: date | None = None,
    segment: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> RfmCustomerPage:
    if segment and segment not in SEGMENTS:
        raise HTTPException(400, "Invalid segment")
    items, _ = result(session, current_user, start_date, end_date, reference_date)
    filtered = [item for item in items if segment is None or item.segment == segment]
    return RfmCustomerPage(
        items=sorted(filtered, key=lambda item: item.monetary, reverse=True)[
            offset : offset + limit
        ],
        total=len(filtered),
    )
