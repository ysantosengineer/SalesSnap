# Sales anomaly detection

Stage 8 detects unusual daily product demand (`SUM(quantity)` per product/day) for the authenticated company. PostgreSQL aggregates demand; the Stage 7 continuous-series utility fills missing days with zero.

The explainable baseline uses a past-only rolling median and MAD (median absolute deviation). A robust score classifies the magnitude and direction: above expected is a spike, below is a drop. MAD-zero periods remain finite; an unexpected value after a constant period is treated as a strong deviation. `IsolationForest(contamination="auto", random_state=42)` evaluates a small feature set: quantity, lags, rolling means/std, and weekday.

Both signals create a **confirmed** anomaly; one creates a **potential** anomaly. Severity thresholds are low ≥3, medium ≥4, high ≥5, and critical ≥7 robust-score magnitude; Isolation Forest-only results are low. At least 30 continuous observations are needed.

Production anomaly labels are unavailable. Therefore accuracy, precision, recall, and F1 are not reported as real-world quality metrics. V1 validation uses unit tests, synthetic spikes/drops, leakage tests, and stable-series sanity checks.

There is no causal analysis, promotion/holiday calendar, alerting, persisted anomaly history, feedback loop, labeled production dataset, or LLM explanation in V1.

The anomaly dashboard supports inclusive `start_date`/`end_date`, product, severity, and direction filters. Summary, list, and selected-product timeline use the same requested period. Timeline markers are returned anomaly payloads; the frontend never recalculates detection.
