# Authentication standards

SalesSnap uses company-scoped local accounts. A registration creates one company and its first user; every authenticated request derives its company context from the access token's user.

- Passwords are hashed with Argon2 through `pwdlib`; plaintext passwords are never persisted or logged.
- Access tokens are short-lived JWTs. Refresh tokens are opaque JWT values stored only as SHA-256 hashes in the database.
- Refresh tokens rotate on every successful refresh. The previous token is revoked, and logout revokes the presented token and clears the HttpOnly cookie.
- The refresh cookie is HttpOnly, `SameSite=Lax`, scoped to `/api/v1/auth`, and only marked `Secure` in production.
- `JWT_SECRET_KEY` is an environment variable. It must be a high-entropy secret outside version control and never be exposed to frontend code.
- Authentication endpoints live under `/api/v1/auth`. Protected backend capabilities must depend on the current authenticated user/company context rather than accepting a tenant identifier from the client.
- Authentication tests cover registration, login, token rotation, logout revocation, and tenant context. PostgreSQL migration validation covers persistence and uniqueness constraints.

Do not add role-based authorization, password reset, email verification, social login, or external identity providers until a dedicated stage defines their requirements.
