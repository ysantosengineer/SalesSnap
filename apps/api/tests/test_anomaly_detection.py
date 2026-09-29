from datetime import date

import pandas as pd

from app.services.anomalies import build_anomaly_features, classify_severity, detect_anomaly_rows


def series(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"date": pd.date_range(date(2026, 1, 1), periods=len(values)), "quantity": values}
    )


def test_baseline_uses_past_only_values() -> None:
    data = series([30.0] * 28 + [150.0])
    features = build_anomaly_features(data)

    assert features.loc[28, "expected_demand"] == 30
    assert features.loc[28, "expected_demand"] != data.loc[28, "quantity"]


def test_detects_synthetic_spike_and_drop_with_direction() -> None:
    spike = detect_anomaly_rows(series([30.0] * 29 + [150.0]))
    drop = detect_anomaly_rows(series([50.0] * 29 + [2.0]))

    assert spike.iloc[-1]["direction"] == "spike"
    assert spike.iloc[-1]["statistical_flag"]
    assert drop.iloc[-1]["direction"] == "drop"
    assert drop.iloc[-1]["severity"] == "critical"


def test_constant_series_is_safe_and_small_noise_is_not_anomaly() -> None:
    assert detect_anomaly_rows(series([30.0, 31.0, 29.0, 30.0] * 10)).empty
    assert classify_severity(0.0, False) is None
    assert classify_severity(3.5, False) == "low"
    assert classify_severity(8.0, False) == "critical"
