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

## Anomaly detection

Stage 8 detects unusual daily product demand, not causes. It reuses tenant-scoped `SUM(quantity)` and continuous demand series, evaluates each day with a past-only rolling median/MAD baseline, and combines that explainable signal with `IsolationForest(contamination="auto", random_state=42)`.

- A detection is confirmed when both signals flag it; a single signal is potential. Severity is deterministic from robust-score magnitude, with Isolation Forest-only results limited to low severity.
- The baseline and historical features must never include the target day. MAD-zero cases must remain finite and safe.
- Anomalies are computed on demand and never persisted in V1. There are no alerts or causal claims.
- Production labels are unavailable: do not claim accuracy, precision, recall, or F1. Use synthetic spikes/drops, leakage tests, and normal-variation sanity checks.
