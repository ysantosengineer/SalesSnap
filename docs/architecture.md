# Architecture

SalesSnap is a modular monolith. The browser loads the Next.js application, which consumes the FastAPI REST API under `/api/v1`. FastAPI owns application orchestration and persists future data through SQLAlchemy to PostgreSQL.

```text
Browser → Next.js → FastAPI → PostgreSQL
```

Pandas, ML, and OpenAI are planned backend capabilities only; they are not active in Stage 1. The database has no domain tables yet.
