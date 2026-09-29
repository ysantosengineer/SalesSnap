import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.stock_risk import StockRiskPage, StockRiskResult, StockRiskSummary
from app.services.forecasting import SUPPORTED_HORIZONS, get_forecast_product
from app.services.stock_risk import build_stock_risk_result, list_stock_risk_results

router = APIRouter(prefix="/analytics/stock-risk", tags=["analytics"])


def validate_horizon(horizon: int) -> None:
    if horizon not in SUPPORTED_HORIZONS:
        raise HTTPException(422, "horizon must be one of 7, 14, or 30")


@router.get("", response_model=StockRiskPage)
def stock_risk(
    horizon: int = Query(default=30),
    risk_level: str | None = None,
    limit: int = Query(default=25, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> StockRiskPage:
    validate_horizon(horizon)
    if risk_level not in {None, "critical", "high", "medium", "low", "safe"}:
        raise HTTPException(422, "Invalid risk_level")
    if risk_level is None:
        items, total = list_stock_risk_results(
            session, current_user.company_id, horizon, limit, offset
        )
    else:
        all_items, _ = list_stock_risk_results(session, current_user.company_id, horizon)
        filtered_items = [item for item in all_items if item.risk_level == risk_level]
        total = len(filtered_items)
        items = filtered_items[offset : offset + limit]
    return StockRiskPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/summary", response_model=StockRiskSummary)
def stock_risk_summary(
    horizon: int = Query(default=30),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> StockRiskSummary:
    validate_horizon(horizon)
    items, total = list_stock_risk_results(session, current_user.company_id, horizon)
    return StockRiskSummary(
        total_products=total,
        critical=sum(item.risk_level == "critical" for item in items),
        high=sum(item.risk_level == "high" for item in items),
        medium=sum(item.risk_level == "medium" for item in items),
        low=sum(item.risk_level == "low" for item in items),
        safe=sum(item.risk_level == "safe" for item in items),
        missing_inventory=sum(item.status == "missing_inventory" for item in items),
        insufficient_data=sum(item.status == "insufficient_data" for item in items),
    )


@router.get("/products/{product_id}", response_model=StockRiskResult)
def stock_risk_product(
    product_id: uuid.UUID,
    horizon: int = Query(default=30),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> StockRiskResult:
    validate_horizon(horizon)
    product = get_forecast_product(session, current_user.company_id, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    return build_stock_risk_result(session, current_user.company_id, product, horizon)
