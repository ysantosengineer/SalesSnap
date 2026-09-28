import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.forecasting import ForecastProduct, ProductForecast
from app.services.forecasting import (
    SUPPORTED_HORIZONS,
    create_product_forecast,
    get_forecast_product,
    list_forecast_products,
)

router = APIRouter(prefix="/analytics/forecast", tags=["analytics"])


@router.get("/products", response_model=list[ForecastProduct])
def products(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[ForecastProduct]:
    return list_forecast_products(session, current_user.company_id)


@router.get("/products/{product_id}", response_model=ProductForecast)
def forecast_product(
    product_id: uuid.UUID,
    horizon: int = Query(default=30),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ProductForecast:
    if horizon not in SUPPORTED_HORIZONS:
        raise HTTPException(status_code=422, detail="horizon must be one of 7, 14, or 30")
    product = get_forecast_product(session, current_user.company_id, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return create_product_forecast(session, current_user.company_id, product, horizon)
