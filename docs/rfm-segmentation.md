# Customer Analytics: RFM segmentation

Stage 6 adds a company-scoped RFM view for customers with persisted sales records. It is descriptive analytics: it classifies historical customer behavior and does not forecast demand, recommend actions, detect anomalies, or call an LLM.

## Data flow

```text
Authenticated user → company scope → PostgreSQL aggregation → Pandas score calculation → FastAPI response → Next.js presentation
```

The database aggregates the latest sale date, number of sales records, and total persisted revenue for each customer. Sales without a customer are excluded because they cannot be attributed to a customer segment. Pandas is used only after that aggregation to calculate deterministic scores.

## Metrics and scores

- **Recency:** calendar days between the reference date and a customer's latest sale. By default, the reference date is the day after the latest scoped sale.
- **Frequency:** count of persisted sales records; this is not item quantity or order count.
- **Monetary:** sum of persisted `revenue` values.
- **Scores:** R, F, and M are percentile-rank scores in the inclusive range 1–5. Ties use average ranks, producing stable results for equal values and small data populations.

The derived `fm_score` is the rounded average of F and M. Segment rules are evaluated in order so that a matching customer receives one stable segment.

## Supported segments

| Segment | Rule |
| --- | --- |
| Champions | R ≥ 4 and FM ≥ 4 |
| Loyal Customers | R ≥ 3 and FM ≥ 4 |
| Potential Loyalists | R ≥ 4 and FM 2–3 |
| New Customers | R = 5 and FM ≤ 2 |
| At Risk | R ≤ 2 and FM ≥ 3 |
| Hibernating | R ≤ 2 and FM ≤ 2 |
| Need Attention | fallback |

## API

Authenticated requests use the current user's company scope:

```text
GET /api/v1/analytics/rfm/summary
GET /api/v1/analytics/rfm/customers?segment=Champions
```

Date filters are inclusive. An explicit `reference_date` must be later than the latest sale in the selected population. An empty tenant population produces empty customer results and a zero-valued summary.

## Frontend

`/customers/segments` displays the segment summary and the customer-level RFM table. Filtering is performed by the backend API; the frontend does not calculate scores or segments.

## Limits

RFM is not a replacement for predictive models or human judgment. Its population is limited to customers connected to imported sales data, and score results are relative to the selected company's current filtered population.
