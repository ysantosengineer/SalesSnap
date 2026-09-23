# Authentication

Stage 3 provides the local account foundation for SalesSnap. `POST /api/v1/auth/register` creates a company and its first user. `POST /api/v1/auth/login` creates an authenticated browser session.

The API returns a short-lived access token in the response body and stores a refresh token in an HttpOnly cookie. The frontend restores a session through `POST /api/v1/auth/refresh`; every refresh rotates the token. `POST /api/v1/auth/logout` revokes the current refresh token and clears the cookie. `GET /api/v1/auth/me` requires a Bearer access token.

The backend never stores plaintext passwords or raw refresh tokens. Set `JWT_SECRET_KEY` locally before running the API. Use a unique high-entropy value in every deployed environment; do not put it in `.env.example`, source code, commits, browser variables, or logs.

The web app has `/register`, `/login`, and a protected `/dashboard` route. It treats the backend as the authority for session restoration and company identity.
