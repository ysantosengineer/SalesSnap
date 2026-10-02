# Production standards

SalesSnap remains a modular monolith deployed as separate web and API containers with PostgreSQL as the persistent source of truth. Production readiness must improve operability without introducing microservices, queues, distributed caches, or provider-specific infrastructure without a demonstrated need.

- `ENVIRONMENT=production` must fail fast for debug mode, placeholder JWT secrets, the default local database URL, non-HTTPS CORS origins, wildcard CORS, or enabled AI without an OpenAI key.
- Secrets belong in the deployment platform or an untracked environment file. Never place credentials, tokens, production URLs containing passwords, or API keys in Git, build arguments, frontend variables, logs, tests, or documentation.
- `/api/v1/health` is process liveness. `/api/v1/readiness` verifies the database dependency and returns a sanitized failure. OpenAI is optional and must not block readiness.
- API request logs are structured JSON and include request ID, method, path, status, and latency. They must not include authorization headers, cookies, prompts, imported content, provider responses, credentials, or personal data.
- Rate limits protect authentication by client IP and expensive authenticated operations by user. The current in-memory limiter is suitable only for a single API instance; a future multi-instance deployment requires an explicitly designed shared limiter.
- Production images use multi-stage builds, minimal runtime contents, non-root users, health checks, and deterministic dependency installation. Database migrations run as a separate one-shot step before the API starts.
- Deployments must back up PostgreSQL before schema changes, run `alembic upgrade head` once, verify readiness and a smoke flow, and retain a tested rollback path. Never run destructive downgrades against production data without a reviewed recovery plan.
- CI must pass Ruff, backend tests, real PostgreSQL migration/integration tests, frontend lint/build, dependency audits, secret scanning, and production image builds before integration into `main`.
- Dependency updates require lockfile or constraint updates, audit results, tests, and production builds. Do not ignore a high or critical production vulnerability without documenting the accepted risk.
- Production errors exposed to clients remain stable and sanitized. Internal exception types and tracebacks belong only in server logs.
- No cloud provider or deployment platform is the architectural default. Provider-specific decisions require an explicit future change and corresponding Skill update.
