# Descriptive analytics standards

Dashboard V1 is descriptive analytics. PostgreSQL and SQLAlchemy perform SUM, COUNT, AVG, DISTINCT, GROUP BY, ordering, and date filtering; do not load all sales into Pandas or Python for these aggregates.

- Dashboard queries receive `company_id` from the authenticated user only.
- Money remains Decimal end-to-end in backend analytics; formatting belongs to the frontend.
- All dashboard endpoints apply the same optional inclusive `start_date` and `end_date` filters. Reject invalid ranges.
- Empty companies return zero summary values and empty collections, never an analytics error.
- `Sales Records` counts sales rows, not orders. `Average Sale Value` is not Average Ticket because there is no order identifier.
- Dashboard V1 reports historical descriptive values only. Do not add forecasts, ML, anomaly detection, recommendations, or AI insight logic to the dashboard. Customer RFM segmentation is a separate module governed by `customer-analytics-standards.md`.
