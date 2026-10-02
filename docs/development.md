# Local development

Requirements: Docker Desktop, Node.js 24+, and Python 3.12+.

Copy `.env.example` to `.env` and adjust values if needed. Start PostgreSQL with `docker compose up -d postgres`. Run the API from `apps/api` with `python -m pip install -e ".[dev]"` then `python -m uvicorn app.main:app --reload`. Open FastAPI docs at `http://localhost:8000/docs`.

Run the frontend from `apps/web` with `npm install` then `npm run dev`; open `http://localhost:3000`.

Validation commands: `python -m ruff check apps/api`, `python -m pytest apps/api`, `npm run lint` (in `apps/web`), and `npm run build` (in `apps/web`).

After applying the Alembic migration, seed two small isolated development tenants from `apps/api` with `python scripts/seed_development.py`. The seed creates Company A and Company B only when they do not already exist, so it is safe to run repeatedly.

AI Insights and AI Chat are opt-in locally. Set `OPENAI_API_KEY`, choose `OPENAI_MODEL`, and set `AI_INSIGHTS_ENABLED=true`. Chat additionally uses `AI_CHAT_HISTORY_MESSAGES`, `AI_CHAT_MAX_TOOL_CALLS`, and `AI_CHAT_MAX_OUTPUT_TOKENS`. Automated tests never call OpenAI; they use provider mocks.

For PostgreSQL integration tests, point `POSTGRES_TEST_DATABASE_URL` to a dedicated disposable test database. These tests migrate down to `base`, upgrade to `head`, validate persistence and isolation, then downgrade for cleanup. Never point this variable to a development or production database.
