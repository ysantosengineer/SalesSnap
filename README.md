# SalesSnap

SalesSnap is a modular SaaS application for sales intelligence. It currently provides tenant-aware authentication, validated sales CSV ingestion, descriptive sales analytics, and customer RFM segmentation. Forecasting, machine learning, and generative AI are planned for later stages.

## Current capabilities

- Next.js frontend with login, registration, protected dashboard, and CSV import page.
- FastAPI REST API under `/api/v1`.
- Company-scoped authentication with JWT access tokens and rotating HttpOnly refresh tokens.
- PostgreSQL, SQLAlchemy, and Alembic migrations.
- Sales CSV V1 ingestion with Pandas, Decimal money handling, partial row rejection, and import summaries.
- Tenant-scoped descriptive sales dashboard with KPI cards, date filters, revenue history, and top products.
- Tenant-scoped Customer Analytics RFM summary and segmentation page, calculated from persisted sales data.
- Tenant-scoped daily product demand forecasting with evaluated baseline and ML-model selection.
- Tenant-scoped explainable sales anomaly detection for unusual demand spikes and drops.

## Architecture

```text
Browser → Next.js → FastAPI → PostgreSQL
                         └── Pandas CSV processing
```

SalesSnap is a modular monolith. Every persisted business record belongs to a company; the API derives the tenant from the authenticated user and never accepts a client-provided `company_id` as its authority.

## CSV import

Authenticated users can upload a CSV at `POST /api/v1/datasets/import` or through `/import` in the frontend.

```csv
date,customer_id,product_id,product_name,quantity,unit_price
2026-09-01,C001,P001,Mouse Logitech,2,149.90
```

The maximum default file size is 10 MB (`MAX_UPLOAD_SIZE_MB`). Clearly oversized multipart requests are rejected from `Content-Length` before FastAPI parses the form body. Remaining uploads are read in 64 KiB chunks and stop as soon as the actual file exceeds the configured limit; the application does not call an unbounded `read()` for an upload.

See [CSV format documentation](./docs/sales-csv-format.md) and [data ingestion architecture](./docs/data-ingestion.md) for validation rules, lifecycle, and limitations.

## Customer Analytics

Authenticated users can view customer segments at `/customers/segments`. The API provides company-scoped RFM results at `GET /api/v1/analytics/rfm/summary` and `GET /api/v1/analytics/rfm/customers`.

RFM is descriptive analysis of persisted customer sales: recency, sales-record frequency, and revenue. It does not perform demand forecasting, anomaly detection, recommendations, or AI analysis. See [RFM segmentation](./docs/rfm-segmentation.md) for scoring rules and API behavior.

## Demand forecasting

Authenticated users can open `/forecast` to select a product and a 7-, 14-, or 30-day horizon. Forecasting uses historical daily `SUM(quantity)`, not revenue. See [demand forecasting](./docs/demand-forecasting.md) for the model, metrics, and limitations.

## Sales anomalies

`/anomalies` presents tenant-scoped unusual-demand events detected by past-only robust statistics and Isolation Forest. The system identifies behavior, not its cause. See [anomaly detection](./docs/anomaly-detection.md).

## Local development

Copy `.env.example` to `.env` and provide a local high-entropy `JWT_SECRET_KEY`. Never commit `.env` or real secrets.

```powershell
docker compose up -d postgres

cd apps/api
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload

cd ../web
npm install
npm run dev
```

The API documentation is available at `http://localhost:8000/docs`; the frontend runs at `http://localhost:3000`.

## Validation

```powershell
cd apps/api
python -m pytest
python -m ruff check .

cd ../web
npm run lint
npm run build
```

PostgreSQL integration tests use `POSTGRES_TEST_DATABASE_URL` and are skipped only when that local environment variable is not configured.

## Engineering rules

Read every Markdown file in [Skills](./Skills) before changing the project. These documents are the permanent record of architecture, security, data-ingestion, testing, and Git workflow decisions.

## Roadmap

Completed: Project Foundation, Database & Multi-tenancy, Authentication & Tenant Context, CSV Import & Data Ingestion, Sales Dashboard, RFM Segmentation, and Demand Forecasting.

See [docs/roadmap.md](./docs/roadmap.md) for the planned stages.
