# Architecture

SalesSnap is a modular monolith. The browser loads the Next.js application, which consumes the FastAPI REST API under `/api/v1`. FastAPI owns application orchestration and persists company-scoped data through SQLAlchemy to PostgreSQL.

```text
Browser → Next.js → FastAPI → PostgreSQL
```

The current application includes tenant-aware authentication, CSV sales ingestion, descriptive sales analytics, and RFM customer segmentation. PostgreSQL performs data aggregation; Pandas is used for CSV parsing and the in-memory RFM score calculation after aggregation. Machine learning and OpenAI capabilities remain planned future stages.
