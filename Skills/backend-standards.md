# Backend standards

Use Python type hints, FastAPI, Pydantic schemas and settings, SQLAlchemy persistence, and Alembic migrations. Version APIs under `/api/v1`. Keep functions small, use English names, handle errors explicitly, and read configuration from environment variables. Never commit secrets. Avoid premature abstractions.

When needed, separate API, services, and persistence. Suggested layout:

```text
apps/api/app/
  main.py
  api/v1/
  core/
  db/
  models/
  schemas/
  services/
```

Do not create empty directories solely to satisfy this suggestion.
