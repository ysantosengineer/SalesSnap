# Sales dashboard

The authenticated dashboard uses tenant-scoped PostgreSQL aggregates.

Endpoints: `GET /api/v1/dashboard/summary`, `/revenue-series`, `/top-products`, and `/overview`. Each accepts optional inclusive `start_date` and `end_date`; top products accepts `limit` from 1 to 50.

Metrics: Total Revenue is `SUM(revenue)`; Units Sold is `SUM(quantity)`; Sales Records is `COUNT(sales.id)`; Active Customers is `COUNT(DISTINCT customer_id)`; Average Sale Value is `AVG(revenue)`.

Sales Records are not Orders, and Average Sale Value is not Average Ticket: the current source data has no `order_id`.

The frontend presents KPI cards, daily historical revenue, top products, filters, loading/error states, and an empty state linking to CSV import. It contains no forecasts or ML output.
