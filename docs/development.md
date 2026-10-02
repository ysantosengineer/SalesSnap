# Local development

## Requirements

- Python 3.12 or newer
- Node.js 24 or newer and npm
- PostgreSQL 17, locally or through Docker
- Docker Desktop only when using the provided Compose services or building images

## Environment

Copy the tracked template and keep the resulting file untracked:

```powershell
Copy-Item .env.example .env
```

Set a high-entropy local `JWT_SECRET_KEY`. The default `DATABASE_URL` targets PostgreSQL on `localhost:5432`; code running inside Compose must use `postgres` as the database hostname. Never commit `.env`, database passwords, JWT secrets, or OpenAI keys.

## Database and API

```powershell
docker compose up -d postgres
cd apps/api
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`. The API exposes liveness at `/api/v1/health` and database readiness at `/api/v1/readiness`.

The optional development seed runs after migrations:

```powershell
python scripts/seed_development.py
```

It creates two isolated example companies and sales records only when those named companies do not exist. It intentionally does not create login credentials; create a local account through `/register` or `POST /api/v1/auth/register`.

## Frontend

```powershell
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`. The default browser API URL is `http://localhost:8000/api/v1`.

## AI configuration

AI Insights and AI Chat are opt-in. Set `OPENAI_API_KEY`, choose `OPENAI_MODEL`, and set `AI_INSIGHTS_ENABLED=true`. Chat also observes the bounded `AI_CHAT_HISTORY_MESSAGES`, `AI_CHAT_MAX_TOOL_CALLS`, and `AI_CHAT_MAX_OUTPUT_TOKENS` settings. Tests always mock or disable the provider; they never make real OpenAI calls.

## Validation

```powershell
cd apps/api
python -m ruff check .
python -m pytest -m "not postgres"
python -m pip_audit

cd ../web
npm audit --omit=dev --audit-level=high
npm run lint -- --max-warnings=0
npm run build
```

PostgreSQL integration tests require a dedicated disposable database:

```powershell
$env:POSTGRES_TEST_DATABASE_URL="postgresql+psycopg://sales_snap:<password>@localhost:5432/sales_snap_test"
python -m pytest -m postgres
```

These tests migrate the dedicated database, validate persistence, constraints, isolation, indexes, and migration cycles, then clean up. Never point `POSTGRES_TEST_DATABASE_URL` to development or production data.

## Production-like build

```powershell
docker build --tag sales-snap-api:local apps/api
docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 --tag sales-snap-web:local apps/web
```

For the complete production-oriented Compose flow, see [deployment](./deployment.md).
