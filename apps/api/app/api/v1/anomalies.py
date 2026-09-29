import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.schemas.anomalies import AnomalyPage, AnomalySummary, DemandAnomaly
from app.services.anomalies import MINIMUM_ANOMALY_OBSERVATIONS, product_anomalies
from app.services.forecasting import get_forecast_product, list_forecast_products

router = APIRouter(prefix="/analytics/anomalies", tags=["analytics"])


def all_anomalies(session: Session, user: User) -> list[DemandAnomaly]:
    lookback = get_settings().anomaly_lookback_days
    items: list[DemandAnomaly] = []
    for item in list_forecast_products(session, user.company_id):
        product = get_forecast_product(session, user.company_id, item.id)
        if product is not None:
            detected, _ = product_anomalies(session, user.company_id, product, lookback)
            items.extend(detected)
    return sorted(items, key=lambda item: (item.date, item.severity), reverse=True)


@router.get("", response_model=AnomalyPage)
def anomalies(
    severity: str | None = None,
    direction: str | None = None,
    product_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AnomalyPage:
    if severity not in {None, "low", "medium", "high", "critical"} or direction not in {
        None,
        "spike",
        "drop",
    }:
        raise HTTPException(400, "Invalid anomaly filter")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "start_date must be before end_date")
    items = all_anomalies(session, current_user)
    items = [
        item
        for item in items
        if (severity is None or item.severity == severity)
        and (direction is None or item.direction == direction)
        and (product_id is None or item.product.id == product_id)
        and (start_date is None or item.date >= start_date)
        and (end_date is None or item.date <= end_date)
    ]
    return AnomalyPage(status="ok", items=items[offset : offset + limit], total=len(items))


@router.get("/summary", response_model=AnomalySummary)
def summary(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> AnomalySummary:
    items = all_anomalies(session, current_user)
    return AnomalySummary(
        total_anomalies=len(items),
        critical=sum(item.severity == "critical" for item in items),
        high=sum(item.severity == "high" for item in items),
        medium=sum(item.severity == "medium" for item in items),
        low=sum(item.severity == "low" for item in items),
        spikes=sum(item.direction == "spike" for item in items),
        drops=sum(item.direction == "drop" for item in items),
    )


@router.get("/products/{product_id}", response_model=AnomalyPage)
def product_detail(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AnomalyPage:
    product = get_forecast_product(session, current_user.company_id, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    items, observations = product_anomalies(
        session, current_user.company_id, product, get_settings().anomaly_lookback_days
    )
    return AnomalyPage(
        status="ok" if observations >= MINIMUM_ANOMALY_OBSERVATIONS else "insufficient_data",
        items=items,
        total=len(items),
        available_observations=observations,
    )
