import uuid

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Product, Sale

MINIMUM_OBSERVATIONS = 30
SUPPORTED_HORIZONS = (7, 14, 30)
FEATURE_COLUMNS = (
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_std_7",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
)


def get_forecast_product(
    session: Session, company_id: uuid.UUID, product_id: uuid.UUID
) -> Product | None:
    return session.scalar(
        select(Product).where(Product.id == product_id, Product.company_id == company_id)
    )


def get_daily_product_demand(
    session: Session, company_id: uuid.UUID, product_id: uuid.UUID
) -> pd.DataFrame:
    rows = session.execute(
        select(Sale.sale_date, func.sum(Sale.quantity))
        .where(Sale.company_id == company_id, Sale.product_id == product_id)
        .group_by(Sale.sale_date)
        .order_by(Sale.sale_date.asc())
    )
    return pd.DataFrame(rows.all(), columns=["date", "quantity"])


def build_continuous_demand_series(daily_demand: pd.DataFrame) -> pd.DataFrame:
    if daily_demand.empty:
        return pd.DataFrame(columns=["date", "quantity"])

    series = daily_demand.copy()
    series["date"] = pd.to_datetime(series["date"])
    series["quantity"] = pd.to_numeric(series["quantity"])
    dates = pd.date_range(series["date"].min(), series["date"].max(), freq="D")
    return (
        series.set_index("date")
        .reindex(dates, fill_value=0)
        .rename_axis("date")
        .reset_index()
        .assign(quantity=lambda frame: frame["quantity"].astype(float))
    )


def observation_count(daily_demand: pd.DataFrame) -> int:
    return len(build_continuous_demand_series(daily_demand))


def build_demand_features(series: pd.DataFrame) -> pd.DataFrame:
    frame = series.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    history = frame["quantity"].shift(1)
    frame["lag_1"] = history
    frame["lag_7"] = frame["quantity"].shift(7)
    frame["lag_14"] = frame["quantity"].shift(14)
    frame["rolling_mean_7"] = history.rolling(7).mean()
    frame["rolling_mean_14"] = history.rolling(14).mean()
    frame["rolling_std_7"] = history.rolling(7).std().fillna(0)
    frame["day_of_week"] = frame["date"].dt.dayofweek
    frame["day_of_month"] = frame["date"].dt.day
    frame["month"] = frame["date"].dt.month
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype(int)
    return frame


def training_rows(series: pd.DataFrame) -> pd.DataFrame:
    return build_demand_features(series).dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
