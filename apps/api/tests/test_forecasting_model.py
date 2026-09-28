from datetime import date

import pandas as pd

from app.services.forecasting import (
    FEATURE_COLUMNS,
    chronological_split,
    evaluate_predictions,
    fit_and_evaluate,
    naive_forecast,
    recursive_forecast,
    training_rows,
)


def demand_series(periods: int = 50) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range(date(2026, 1, 1), periods=periods, freq="D"),
            "quantity": [float((index % 9) + 1) for index in range(periods)],
        }
    )


def test_naive_forecast_uses_recent_seven_day_average() -> None:
    assert naive_forecast(pd.Series([1, 2, 3, 4, 5, 6, 7, 14])) == 41 / 7


def test_chronological_split_keeps_training_dates_before_test_dates() -> None:
    train, test = chronological_split(training_rows(demand_series()))

    assert train["date"].max() < test["date"].min()


def test_evaluation_metrics_and_zero_actual_wape_are_safe() -> None:
    actual = pd.Series([2.0, 4.0])
    predicted = pd.Series([1.0, 7.0])

    mae, rmse, wape = evaluate_predictions(actual, predicted)
    _, _, zero_wape = evaluate_predictions(pd.Series([0.0, 0.0]), pd.Series([1.0, 2.0]))

    assert mae == 2.0
    assert round(rmse, 4) == round((5.0**0.5), 4)
    assert wape == 2 / 3
    assert zero_wape is None


def test_model_is_reproducible_and_recursive_forecast_is_non_negative() -> None:
    series = demand_series()
    model, evaluation = fit_and_evaluate(series)
    repeat_model, repeat_evaluation = fit_and_evaluate(series)

    first = recursive_forecast(series, model, evaluation.selected_model, 7)
    second = recursive_forecast(series, repeat_model, repeat_evaluation.selected_model, 7)

    assert evaluation == repeat_evaluation
    assert first["predicted_quantity"].tolist() == second["predicted_quantity"].tolist()
    assert len(first) == 7
    assert first["predicted_quantity"].ge(0).all()


class NegativeModel:
    def predict(self, features: pd.DataFrame) -> list[float]:
        assert list(features.columns) == list(FEATURE_COLUMNS)
        return [-3.2]


def test_recursive_forecast_clamps_negative_predictions() -> None:
    forecast = recursive_forecast(demand_series(), NegativeModel(), "model", 1)  # type: ignore[arg-type]

    assert forecast["predicted_quantity"].tolist() == [0.0]
