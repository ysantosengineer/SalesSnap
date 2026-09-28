from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.forecasting import router as forecasting_router
from app.api.v1.health import router as health_router
from app.api.v1.rfm import router as rfm_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(datasets_router)
api_router.include_router(dashboard_router)
api_router.include_router(forecasting_router)
api_router.include_router(rfm_router)
