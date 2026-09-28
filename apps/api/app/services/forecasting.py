import uuid
from dataclasses import dataclass
from math import sqrt

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
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
MODEL_NAME = "hist_gradient_boosting"
MODEL_VERSION = "hist_gradient_boosting_v1"
RANDOM_STATE = 42


@dataclass(frozen=True)
class EvaluationResult:
    selected_model: str
    model_mae: float
    model_rmse: float
    model_wape: float | None
    baseline_mae: float
    baseline_rmse: float
    baseline_wape: float | None


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


def chronological_split(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = max(1, int(len(rows) * 0.8))
    return rows.iloc[:split_index].copy(), rows.iloc[split_index:].copy()


def naive_forecast(values: pd.Series, window: int = 7) -> float:
    return float(values.tail(window).mean())


def evaluate_predictions(
    actual: pd.Series, predicted: pd.Series
) -> tuple[float, float, float | None]:
    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(sqrt(mean_squared_error(actual, predicted)))
    actual_total = float(actual.sum())
    wape = float((actual - predicted).abs().sum() / actual_total) if actual_total else None
    return mae, rmse, wape


def fit_and_evaluate(
    series: pd.DataFrame,
) -> tuple[HistGradientBoostingRegressor, EvaluationResult]:
    rows = training_rows(series)
    train, test = chronological_split(rows)
    model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    model.fit(train[list(FEATURE_COLUMNS)], train["quantity"])
    model_prediction = pd.Series(model.predict(test[list(FEATURE_COLUMNS)]), index=test.index)
    baseline_prediction = test["rolling_mean_7"]
    model_metrics = evaluate_predictions(test["quantity"], model_prediction)
    baseline_metrics = evaluate_predictions(test["quantity"], baseline_prediction)
    selected_model = (
        MODEL_VERSION if model_metrics[0] <= baseline_metrics[0] else "naive_rolling_mean_7"
    )
    return model, EvaluationResult(
        selected_model=selected_model,
        model_mae=model_metrics[0],
        model_rmse=model_metrics[1],
        model_wape=model_metrics[2],
        baseline_mae=baseline_metrics[0],
        baseline_rmse=baseline_metrics[1],
        baseline_wape=baseline_metrics[2],
    )


def recursive_forecast(
    series: pd.DataFrame,
    model: HistGradientBoostingRegressor,
    selected_model: str,
    horizon: int,
) -> pd.DataFrame:
    future = series[["date", "quantity"]].copy()
    predictions: list[dict[str, object]] = []
    for _ in range(horizon):
        next_date = pd.Timestamp(future["date"].iloc[-1]) + pd.DateOffset(days=1)
        candidate = pd.concat(
            [future, pd.DataFrame({"date": [next_date], "quantity": [0.0]})], ignore_index=True
        )
        features = build_demand_features(candidate).iloc[-1]
        prediction = (
            naive_forecast(future["quantity"])
            if selected_model == "naive_rolling_mean_7"
            else float(model.predict(pd.DataFrame([features[list(FEATURE_COLUMNS)]]))[0])
        )
        prediction = max(prediction, 0.0)
        future.loc[len(future)] = {"date": next_date, "quantity": prediction}
        predictions.append({"date": next_date, "predicted_quantity": prediction})
    return pd.DataFrame(predictions)
