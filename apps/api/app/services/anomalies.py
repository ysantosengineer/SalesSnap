import uuid

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.schemas.anomalies import AnomalyProduct, DemandAnomaly
from app.services.forecasting import (
    RANDOM_STATE,
    build_continuous_demand_series,
    get_daily_product_demand,
)

MINIMUM_ANOMALY_OBSERVATIONS = 30
ANOMALY_FEATURE_COLUMNS = (
    "quantity",
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "rolling_mean_28",
    "rolling_std_7",
    "day_of_week",
)


def build_anomaly_features(series: pd.DataFrame, lookback: int = 28) -> pd.DataFrame:
    frame = series.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    past = frame["quantity"].shift(1)
    frame["lag_1"] = past
    frame["lag_7"] = frame["quantity"].shift(7)
    frame["rolling_mean_7"] = past.rolling(7, min_periods=7).mean()
    frame["rolling_mean_28"] = past.rolling(lookback, min_periods=7).mean()
    frame["rolling_std_7"] = past.rolling(7, min_periods=7).std().fillna(0)
    frame["expected_demand"] = past.rolling(lookback, min_periods=7).median()
    frame["mad"] = past.rolling(lookback, min_periods=7).apply(
        lambda values: np.median(np.abs(values - np.median(values))), raw=True
    )
    frame["day_of_week"] = frame["date"].dt.dayofweek
    return frame


def classify_severity(score: float, isolation_flag: bool) -> str | None:
    magnitude = abs(score)
    if magnitude >= 7:
        return "critical"
    if magnitude >= 5:
        return "high"
    if magnitude >= 4:
        return "medium"
    if magnitude >= 3 or isolation_flag:
        return "low"
    return None


def get_product_anomaly_series(
    session, company_id: uuid.UUID, product_id: uuid.UUID
) -> pd.DataFrame:
    return build_continuous_demand_series(get_daily_product_demand(session, company_id, product_id))


def detect_anomaly_rows(series: pd.DataFrame, lookback: int = 28) -> pd.DataFrame:
    frame = build_anomaly_features(series, lookback)
    valid = frame.dropna(subset=ANOMALY_FEATURE_COLUMNS)
    frame["isolation_forest_flag"] = False
    if len(valid) >= 7:
        detector = IsolationForest(contamination="auto", random_state=RANDOM_STATE)
        flags = detector.fit_predict(valid[list(ANOMALY_FEATURE_COLUMNS)]) == -1
        flags = flags & (
            (valid["quantity"] - valid["rolling_mean_7"]).abs()
            > valid["rolling_std_7"].fillna(0) * 3
        )
        frame.loc[valid.index, "isolation_forest_flag"] = flags
    expected = frame["expected_demand"]
    mad = frame["mad"]
    difference = frame["quantity"] - expected
    score = pd.Series(0.0, index=frame.index)
    nonzero_mad = mad > 0
    score.loc[nonzero_mad] = 0.6745 * difference.loc[nonzero_mad] / mad.loc[nonzero_mad]
    zero_mad_difference = (mad == 0) & difference.ne(0)
    score.loc[zero_mad_difference] = np.sign(difference.loc[zero_mad_difference]) * 8.0
    frame["robust_score"] = score
    frame["statistical_flag"] = score.abs() >= 3
    frame["severity"] = [
        classify_severity(item_score, bool(item_flag))
        for item_score, item_flag in zip(score, frame["isolation_forest_flag"], strict=True)
    ]
    frame["direction"] = np.where(difference > 0, "spike", np.where(difference < 0, "drop", None))
    frame["deviation_percentage"] = np.where(expected.ne(0), difference / expected * 100, np.nan)
    frame["confidence"] = np.where(
        frame["statistical_flag"] & frame["isolation_forest_flag"], "confirmed", "potential"
    )
    return frame[(frame["severity"].notna()) & (frame["direction"].notna())].copy()


def product_anomalies(
    session, company_id: uuid.UUID, product, lookback: int
) -> tuple[list[DemandAnomaly], int]:
    series = get_product_anomaly_series(session, company_id, product.id)
    if len(series) < MINIMUM_ANOMALY_OBSERVATIONS:
        return [], len(series)
    rows = detect_anomaly_rows(series, lookback)
    items = [
        DemandAnomaly(
            date=row.date.date(),
            product=AnomalyProduct(
                id=product.id, external_id=product.external_id, name=product.name
            ),
            actual_demand=row.quantity,
            expected_demand=row.expected_demand,
            deviation_percentage=None
            if pd.isna(row.deviation_percentage)
            else row.deviation_percentage,
            direction=row.direction,
            severity=row.severity,
            robust_score=row.robust_score,
            statistical_flag=bool(row.statistical_flag),
            isolation_forest_flag=bool(row.isolation_forest_flag),
            confidence=row.confidence,
        )
        for row in rows.itertuples()
    ]
    return items, len(series)
