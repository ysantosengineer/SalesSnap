import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.schemas.anomalies import AnomalyPage, AnomalySummary, DemandAnomaly, DemandTimelinePoint
from app.services.anomalies import (
    MINIMUM_ANOMALY_OBSERVATIONS,
    get_product_anomaly_series,
    product_anomalies,
)
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


def filter_items(
    items: list[DemandAnomaly],
    severity: str | None,
    direction: str | None,
    product_id: uuid.UUID | None,
    start_date: date | None,
    end_date: date | None,
) -> list[DemandAnomaly]:
    return [
        item
        for item in items
        if (severity is None or item.severity == severity)
        and (direction is None or item.direction == direction)
        and (product_id is None or item.product.id == product_id)
        and (start_date is None or item.date >= start_date)
        and (end_date is None or item.date <= end_date)
    ]


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
    items = filter_items(items, severity, direction, product_id, start_date, end_date)
    return AnomalyPage(status="ok", items=items[offset : offset + limit], total=len(items))


@router.get("/summary", response_model=AnomalySummary)
def summary(
    severity: str | None = None,
    direction: str | None = None,
    product_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AnomalySummary:
    items = filter_items(
        all_anomalies(session, current_user), severity, direction, product_id, start_date, end_date
    )
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
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> AnomalyPage:
    product = get_forecast_product(session, current_user.company_id, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    items, observations = product_anomalies(
        session, current_user.company_id, product, get_settings().anomaly_lookback_days
    )
    series = get_product_anomaly_series(session, current_user.company_id, product_id)
    if start_date:
        series = series[series["date"].dt.date >= start_date]
    if end_date:
        series = series[series["date"].dt.date <= end_date]
    items = filter_items(items, None, None, None, start_date, end_date)
    return AnomalyPage(
        status="ok" if observations >= MINIMUM_ANOMALY_OBSERVATIONS else "insufficient_data",
        items=items,
        total=len(items),
        available_observations=observations,
        history=[
            DemandTimelinePoint(date=row.date.date(), quantity=row.quantity)
            for row in series.itertuples()
        ],
    )
