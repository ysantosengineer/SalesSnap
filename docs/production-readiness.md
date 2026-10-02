# Production readiness

SalesSnap has production-oriented configuration, security controls, observability, dependency gates, containers, and release validation. This document describes readiness of the codebase; it does not claim that a public environment is currently deployed.

## Runtime safeguards

- Production settings reject debug mode, placeholder JWT secrets, the default development database, wildcard or non-HTTPS CORS origins, and enabled AI without an OpenAI key.
- Access tokens are short lived; refresh tokens rotate, are stored only as hashes, and use HttpOnly cookies with `Secure` enabled in production.
- Authentication and expensive import, forecast, AI Insights, and AI Chat operations have configurable rate limits.
- Next.js applies a content security policy, clickjacking protection, MIME-sniffing protection, a restrictive permissions policy, and a strict referrer policy.
- Client errors are sanitized. Structured server logs contain request metadata and error types without credentials, prompts, uploaded data, or provider responses.

## Availability signals

`GET /api/v1/health` is a liveness signal for the API process. `GET /api/v1/readiness` executes a minimal database query and returns `503` with a sanitized response when PostgreSQL is unavailable. OpenAI is optional and is deliberately excluded from readiness.

## Data and performance

PostgreSQL is the source of truth. Alembic is the only schema-change path. Production indexes cover tenant-scoped dataset, sales, conversation, message, and common analytics access paths. Public collection endpoints use bounded pagination, and analytical queries aggregate in PostgreSQL before bounded in-memory processing.

The current rate limiter is process-local. Deploy the API as a single instance unless a future architectural decision introduces a shared limiter. AI requests are explicit, bounded by time, tool-call, history, evidence, and output limits; no automated background provider calls exist.

## Quality gates

GitHub Actions validates backend lint and tests, dependency audits, frontend dependency audit/lint/build, real PostgreSQL migrations and integration tests, production Docker builds, and tracked-secret patterns. The production smoke test covers authentication, ingestion, descriptive analytics, RFM, forecasting, anomalies, inventory, stock risk, disabled AI behavior, and logout.

## Known limitations

- No public cloud environment or managed database has been provisioned.
- Backups, TLS termination, DNS, monitoring retention, alert routing, and horizontal scaling are deployment-platform responsibilities.
- The in-memory rate limiter is not coordinated across API replicas.
- Forecasts, anomalies, stock risk, and AI output are decision support, not autonomous actions.
- AI is disabled unless explicitly configured.
