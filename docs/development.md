# Local development

Requirements: Docker Desktop, Node.js 24+, and Python 3.12+.

Copy `.env.example` to `.env` and adjust values if needed. Start PostgreSQL with `docker compose up -d postgres`. Run the API from `apps/api` with `python -m pip install -e ".[dev]"` then `python -m uvicorn app.main:app --reload`. Open FastAPI docs at `http://localhost:8000/docs`.

Run the frontend from `apps/web` with `npm install` then `npm run dev`; open `http://localhost:3000`.

Validation commands: `python -m ruff check apps/api`, `python -m pytest apps/api`, `npm run lint` (in `apps/web`), and `npm run build` (in `apps/web`).
