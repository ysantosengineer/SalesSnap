# Machine learning and forecasting standards

Demand Forecasting V1 predicts daily product demand, defined only as `SUM(sales.quantity)` per product and day. PostgreSQL performs the tenant-scoped aggregation; Pandas fills missing daily observations and builds features; scikit-learn trains and evaluates the model.

- Every forecast derives `company_id` from the authenticated user. A product from another tenant must look absent.
- Missing calendar days between the first and last sale are zero-filled. At least 30 continuous daily observations are required.
- Use chronological train/test splits only. Random shuffling is forbidden.
- Features use historical values only: lags and rolling values must shift before rolling. Tests must protect against data leakage.
- A naive seven-day rolling-mean baseline is mandatory. Select the ML model only when its validation MAE is no worse than the baseline.
- Report MAE, RMSE, and WAPE. WAPE is null when actual demand sums to zero.
- V1 uses `HistGradientBoostingRegressor` with `random_state=42`; forecast recursively and clamp negative values to zero.
- No LLM, deep learning, AutoML, confidence intervals, model persistence, automated retraining, queues, or model registry in V1.
