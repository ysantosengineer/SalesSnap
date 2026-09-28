# Demand forecasting

Stage 7 forecasts daily product demand for the authenticated company. The target is **daily demand = SUM(quantity)**, never revenue. PostgreSQL aggregates product/day history, Pandas zero-fills missing days and creates lag/calendar features, and scikit-learn evaluates a `HistGradientBoostingRegressor` against a naive seven-day rolling-mean baseline.

Training uses available continuous history with a chronological 80/20 split. The model receives `lag_1`, `lag_7`, `lag_14`, rolling mean/std features, weekday, day of month, month, and weekend flag. Rolling features are shifted first, so they never include the target being predicted. MAE, RMSE, and WAPE are returned; WAPE is null for an all-zero evaluation target. The selected forecast is ML only when its MAE is no worse than the baseline.

At least 30 continuous observations are required. Forecasting is recursive, point-only, and clamps negative predictions to zero. The API returns up to 90 history points for charts while training uses all available history.

## Model card

- **Purpose:** product-level daily demand prediction.
- **Training data:** tenant-scoped persisted sales quantity, zero-filled by calendar day.
- **Target:** daily quantity sum.
- **Evaluation:** chronological holdout with MAE, RMSE, and WAPE.
- **Known limits:** no holidays, promotions, prices, weather, external variables, cross-product effects, confidence intervals, persistence, or automatic retraining.

Endpoints: `GET /api/v1/analytics/forecast/products` and `GET /api/v1/analytics/forecast/products/{product_id}?horizon=7|14|30`.
