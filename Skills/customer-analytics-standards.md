# Customer analytics and RFM standards

Customer Analytics V1 exposes RFM segmentation from persisted, company-scoped sales data. It is a descriptive customer-analysis module; it does not create forecasts, recommendations, anomaly findings, or AI insights.

- The authenticated user's company is the only tenant authority. Customer Analytics endpoints never accept a client-selected `company_id`.
- PostgreSQL and SQLAlchemy aggregate each customer's latest sale date, sale-record count, and revenue total. Sales rows without a customer are excluded from RFM because they cannot be attributed safely.
- RFM values are computed in the backend. The frontend presents API results and must not duplicate scoring or segment rules.
- Recency is measured in days from the latest scoped sale to a reference date. The default reference date is one day after the latest scoped sale; an explicit reference date must be later than that sale date.
- Frequency is the count of persisted sales records, not quantity and not orders. Monetary value is the sum of persisted `revenue` values and remains Decimal in backend calculations.
- Scores use deterministic percentile ranks from 1 to 5. Ties use Pandas `rank(method="average")`; a score is always bounded to the inclusive range 1–5.
- Segment precedence is part of the public analytical behavior: Champions, Loyal Customers, Potential Loyalists, New Customers, At Risk, Hibernating, then Need Attention as the fallback.
- Empty tenant populations return an empty customer collection and zero summary values rather than an error.
- Tests for this module must cover tenant isolation, ties, small populations, every supported segment, and PostgreSQL aggregation.

This module may use Pandas only for in-memory score calculation after the database has performed the tenant-scoped aggregation. Do not load raw sales into Pandas to replace SQL aggregation.
