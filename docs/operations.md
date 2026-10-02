# Operations guide

## Health and logs

- Liveness: `GET /api/v1/health`
- Readiness: `GET /api/v1/readiness`
- API logs: JSON on standard output with `timestamp`, `level`, `event`, `request_id`, method, path, status, and latency.
- Request correlation: preserve an incoming valid `X-Request-ID`, or use the generated response header.

Alert on sustained readiness failures, repeated HTTP 5xx responses, authentication or expensive-operation rate-limit spikes, database saturation, disk pressure, and failed migration jobs. Do not log or forward authorization headers, cookies, request bodies, CSV content, prompts, customer identifiers, secrets, or provider responses.

## PostgreSQL

Use automated encrypted backups with retention appropriate to the deployment. Periodically restore a backup into an isolated environment and run migrations plus smoke validation. Monitor storage, active connections, slow queries, locks, and backup age.

Before a release:

```powershell
python -m alembic current
python -m alembic heads
python -m alembic upgrade head
```

Run these commands from `apps/api` with the target `DATABASE_URL`. Never aim test or downgrade commands at production.

## Incident triage

1. Capture the time range, deployment commit, affected endpoint, status code, and request ID.
2. Check readiness and database health.
3. Review sanitized structured logs around the request ID.
4. Disable optional AI with `AI_INSIGHTS_ENABLED=false` if the provider is degraded; deterministic analytics remain available.
5. Roll back the application image if the latest release caused the incident.
6. Restore PostgreSQL only from a verified backup and only when data integrity requires it.

## Routine validation

Run the full backend suite, PostgreSQL integration suite, Ruff, frontend lint/build, dependency audits, secret scan, and production image builds before release. Rotate JWT, database, and OpenAI secrets through the deployment platform without committing them. Rebuild images after dependency or base-image security updates.
