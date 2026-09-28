from datetime import date

import pandas as pd

from app.services.forecasting import FEATURE_COLUMNS, build_demand_features, training_rows


def demand_series() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range(date(2026, 1, 1), periods=20, freq="D"),
            "quantity": list(range(1, 21)),
        }
    )


def test_demand_features_include_lags_rollings_and_calendar_values() -> None:
    features = build_demand_features(demand_series())
    row = features.iloc[14]

    assert set(FEATURE_COLUMNS) <= set(features.columns)
    assert row["lag_1"] == 14
    assert row["lag_7"] == 8
    assert row["lag_14"] == 1
    assert row["rolling_mean_7"] == 11
    assert row["rolling_mean_14"] == 7.5
    assert row["day_of_week"] == 3
    assert row["day_of_month"] == 15
    assert row["month"] == 1
    assert row["is_weekend"] == 0


def test_rolling_features_use_only_values_before_current_target() -> None:
    series = demand_series()
    features = build_demand_features(series)
    target_row = 14

    assert features.loc[target_row, "rolling_mean_7"] == series.loc[7:13, "quantity"].mean()
    assert features.loc[target_row, "rolling_mean_7"] != series.loc[8:14, "quantity"].mean()


def test_training_rows_drop_observations_without_required_history() -> None:
    rows = training_rows(demand_series())

    assert len(rows) == 6
    assert rows["date"].min() == pd.Timestamp("2026-01-15")
