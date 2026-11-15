# CodePilot API scaffold

This is an early backend scaffold, not a live connected service. It implements a GitHub App OAuth callback and cookie session in the intended shape; no real OAuth client, database, or encryption key is configured.

## Local development

1. Install Python 3.11+ and MongoDB locally or use a TLS-enabled development cluster.
2. Copy `.env.example` to `.env` and configure local values privately.
3. Register a GitHub App, use `http://localhost:8000/auth/github/callback` as the callback URL, and grant only read-only repository metadata and contents permissions. Do not grant contents write, pull request write, administration, or Actions permissions in this phase.
4. Generate a Fernet key with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
5. Set `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `MONGODB_URI`, `MONGODB_DATABASE`, `FERNET_KEY`, `API_BASE_URL=http://localhost:8000`, and `FRONTEND_ORIGIN=http://localhost:5173` in `.env`.
6. Install: `python -m pip install -e ".[test]"`; run: `uvicorn app.main:app --reload --port 8000`.
7. Tests: `pytest -q`.

## API routes

- `GET /health`
- `GET /auth/github/start` — generates one-time state and PKCE challenge.
- `GET /auth/github/callback` — checks state, exchanges the short-lived code, encrypts the token, and sets an HttpOnly session cookie.
- `GET /api/me` — returns minimal GitHub identity data.
- `GET /api/repositories` — returns repository metadata (read-only, no code changes).
- `POST /auth/logout` — revokes the local session cookie and session record.

The API currently does not request offline refresh tokens, so a GitHub authorization may need to be repeated after expiry. Cross-site production cookies require HTTPS and `SameSite=None`; set the exact frontend CORS origin. Prefer a same-origin reverse proxy for cookies and CSRF safety where possible.

## Before production

Create a vetted threat model; add server-side rate limiting, CSRF controls, origin checks, OAuth app ownership/review, user-token revocation and reconnect, account deletion/disconnect, audit logging without secrets, dependency/security scanning, monitoring, and tests against a real temporary MongoDB. Set retention, consent, and privacy disclosures. Never run repository code in this API process. A separately isolated, constrained runner is required before any code execution is offered.
