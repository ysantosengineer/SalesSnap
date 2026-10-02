# Deployment guide

SalesSnap ships provider-neutral production containers through `docker-compose.prod.yml`. A platform may run the same web and API images separately, but PostgreSQL must remain durable and migrations must run exactly once before the API starts.

## Required configuration

Create an untracked `.env.production` file or configure equivalent platform secrets:

```env
POSTGRES_DB=sales_snap
POSTGRES_USER=sales_snap
POSTGRES_PASSWORD=<strong-database-password>
DATABASE_URL=postgresql+psycopg://sales_snap:<url-encoded-password>@postgres:5432/sales_snap
JWT_SECRET_KEY=<high-entropy-secret-at-least-32-characters>
CORS_ALLOWED_ORIGINS=https://app.example.com
NEXT_PUBLIC_API_URL=https://api.example.com/api/v1
API_PORT=8000
WEB_PORT=3000
LOG_LEVEL=INFO
AI_INSIGHTS_ENABLED=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

`NEXT_PUBLIC_API_URL` is embedded during the frontend build and is public. Never put secrets in a `NEXT_PUBLIC_*` variable. Use HTTPS origins in production and URL-encode special characters in database credentials.

## Container deployment

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

The compose flow waits for PostgreSQL, executes `alembic upgrade head` in the one-shot `migrate` service, starts the API after migration success, waits for readiness, and then starts the web application. Both application images run as non-root users.

Verify:

```powershell
Invoke-RestMethod https://api.example.com/api/v1/health
Invoke-RestMethod https://api.example.com/api/v1/readiness
```

Then register a disposable verification tenant and execute the documented smoke path. Delete disposable production verification data only through an approved operational procedure.

## Release sequence

1. Confirm the target commit passed every GitHub Actions job.
2. Back up PostgreSQL and verify the backup is readable.
3. Build immutable images from that commit.
4. Run `alembic upgrade head` once.
5. Start the API and verify readiness.
6. Start the web application and run the smoke flow.
7. Observe structured logs and error rates before declaring the release healthy.

## Rollback

Prefer rolling back application images while keeping a backward-compatible migrated schema. If a migration is not backward compatible, stop the application and restore the verified pre-release database backup. Do not improvise an Alembic downgrade against production data; rehearse and review any downgrade separately.
