# CodePilot AI backend — phase 1 plan

## Goal
Add a separate FastAPI service for GitHub sign-in and repository discovery. Keep the React/Vite marketing site static. Do not execute source code, write to repositories, create branches, or open pull requests in phase 1.

## Recommended architecture
- React/Vite frontend on Vercel; separate FastAPI API deployment.
- GitHub App web-application authorization flow, not a long-lived personal access token.
- Register only fine-grained, read-only GitHub App permissions for repository metadata and contents. Do not ask for write, pull-request, administration, or workflow permissions in phase 1.
- Auth-code flow validates one-time `state`, uses PKCE (S256), exchanges codes on the server, and keeps client secrets server-only.
- Opaque, random, HttpOnly, Secure (in production), SameSite=Lax session cookie. Store only a SHA-256 digest of the session secret in MongoDB; short session lifetime and TTL cleanup.
- Encrypt GitHub tokens at rest with a dedicated Fernet key from the host's secret manager. Never put tokens, OAuth codes, session IDs, or secrets in frontend storage, URLs, logs, or Git.
- Restrict CORS to the configured frontend origin. Use fixed GitHub API hosts, timeouts, response validation, and safe error messages.
- Repository-list endpoint returns minimal metadata for repositories the user's GitHub authorization and app permissions allow. Verify authorization against the selected repository before later analysis; never trust a client-supplied owner/name without a server-side access check.

## Implemented scaffold in this phase
- OAuth start/callback routes with one-time state bound to an HttpOnly browser cookie, PKCE (S256), and form-encoded code exchange.
- GitHub identity and read-only repository listing routes.
- MongoDB-backed expiring state and sessions, encrypted stored tokens; production startup fails closed for missing secrets and requires TLS MongoDB.
- `.env.example` with placeholders only; no secrets included.
- Initial security tests for state/PKCE/token encryption helpers.

## Not implemented yet
- A registered GitHub App, real OAuth credentials, MongoDB cluster, deployed API, frontend connection, account UI, revocation/disconnect, rate limiting, security monitoring, or legal/compliance review.
- Running untrusted repository code. That requires an isolated execution service with resource limits, outbound network restrictions, short-lived credentials, and an explicit threat model.
- Write access. Any later patch/PR flow should create a branch and draft PR, require human review, and request only narrowly scoped write permissions after the user explicitly chooses that capability.

## Rollout checklist
1. Confirm an owned GitHub repository and create a private project repo (or confirm an existing target).
2. Create/configure the GitHub App in the user's account; use the exact callback URL after API hosting is selected; publish a clear privacy notice and verified domain.
3. Create MongoDB with TLS, least-privilege credentials, backups, network restrictions, and TTL indexes.
4. Generate OAuth client secret and Fernet key directly in the hosting provider's secret manager; do not paste them into chat or commit them.
5. Deploy the API; set exact frontend origin and production cookie settings; test auth, session expiration, repository allow-listing, disconnect/revocation, CORS, and error handling.
6. Connect frontend buttons only after API endpoints and privacy disclosures are verified.
7. Import the private GitHub repo into Vercel; review framework/build/root output settings and verify the production URL.
