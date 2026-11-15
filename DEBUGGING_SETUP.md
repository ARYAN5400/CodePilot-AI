# Gemini debugging API

The root `api/debug.js` function adds `POST /api/debug` to the Vite project on Vercel. It uses Node built-ins and the Gemini REST API; there are no new packages. The separate Python service in `backend/` is not required for this endpoint and is unchanged.

## Configure and deploy

1. Create a Gemini API key in a Google project you control. Set a restrictive provider quota and billing alerts before exposing this endpoint. Restrict the credential to the appropriate Gemini API where available. Never paste the key into chat, source code, browser storage, or a client-side variable.
2. Import this repository into a Vercel project, with this directory as the root. Keep the Vite preset, build command `npm run build` and output directory `dist`. Use a supported Node runtime (Node 22 or newer is recommended). Vercel should detect root `api/*.js` functions alongside the static build. No change to `vercel.json` or `package.json` is needed.
3. In Vercel Project Settings > Environment Variables, add server-only `GEMINI_API_KEY`. Optionally add `GEMINI_MODEL`; the default is `gemini-2.5-flash`. Use a model available to your account that supports structured JSON responses. Select the intended Preview and/or Production environments. Do not prefix either variable with `VITE_`. Review who can access preview deployments and their credentials.
4. Deploy or redeploy after saving environment variables. Confirm Vercel lists the `/api/debug` function and its duration limit exceeds the endpoint's 25-second provider deadline. A static-only host or a Vite-only development server will not serve this function.
5. Smoke-test a harmless snippet on the deployed site's debugging form, then inspect the Network response for `verification: "not_run"`. Confirm cross-origin browser calls are rejected, invalid input fails cleanly, and the key is absent from browser bundles, requests to this endpoint, and logs. Tests below are mocked and do not establish that a real key, deployment routing, provider quota, or a chosen model works.

For local integration, use Vercel's development server (`vercel dev` if the CLI is installed). Put local server values in an untracked `.env.local`, not `.env.example`. Check Git ignores local secret files before adding one. Never commit actual credentials. The app's existing `npm run dev` serves Vite only and is not an API emulator.

## Request and response

Send `Content-Type: application/json` with exactly these fields:

```json
{"language":"javascript","code":"function total(items) { return items.length; }","issue":"The function should sum prices instead of counting items."}
```

Accepted language IDs: javascript, typescript, python, java, c, cpp, csharp, go, rust, ruby, php, swift, kotlin, html, css, sql. IDs are case-sensitive. Code must contain 1–32,000 characters and the issue 1–4,000 characters; whitespace-only values are rejected. The entire JSON body is limited to 48,000 UTF-8 bytes. Multibyte characters may hit the byte limit before a character limit. Compressed bodies are rejected. Vercel may parse a body before calling the function; these application bounds are not a replacement for platform ingress limits.

Successful responses contain only:

```json
{"summary":"Likely issue","rootCause":"Reasoning based on the supplied snippet","fixedCode":"Proposed source code","explanation":["What changed and why"],"suggestedTests":["A test to write and run"],"verification":"not_run"}
```

Output validation requires exactly these fields: summary up to 2,000 characters, rootCause up to 4,000, fixedCode up to 48,000, and 1–12 nonempty strings of up to 2,000 characters in each list. The provider HTTP body is capped at 196,608 bytes. Truncated, blocked, malformed, oversized, or unexpected provider results are rejected rather than displayed as successful fixes. These are structural checks, not proof that the reasoning or code is correct.

Errors use `{"error":{"code":"…","message":"…"}}` with HTTP 400 for invalid inputs, 403 for cross-origin browser requests, 405 for wrong methods, 413 for size limits, 415 for unsupported content, 429 for local throttling (with Retry-After), 503 for missing/invalid server configuration or provider throttling, 502 for provider failures/unusable results, and 504 for the provider deadline. Responses are marked no-store. Raw provider errors and credentials are never returned or logged by this function.

## Security and current limitations

This is a public, unauthenticated endpoint. Same-origin checks and no CORS opt-in stop ordinary cross-origin browser use; they do not authenticate a caller. Scripts can omit or forge Origin and Fetch Metadata headers. No-origin requests are allowed for CLI clients. Browser Origin must match the request host exactly, use HTTPS except on localhost, and Fetch Metadata must be same-origin or none when supplied. Review custom proxy/host behavior if deploying outside Vercel.

There is a best-effort in-memory rate limiter: 5 requests per client and 30 total requests in a fixed 60-second window **per running instance**, with at most 1,000 tracked client hashes. All admitted attempts, including invalid requests, count. On Vercel the client identity uses the platform forwarding header; outside Vercel it uses the socket address. Only trust forwarding headers set by your deployment platform. Client addresses are hashed for the short-lived map and never logged here. Restarts, cold starts, and parallel instances reset or multiply these limits. This is not a distributed limiter and cannot reliably prevent quota or cost abuse. Add authentication, persistent per-user/distributed quotas, deployment protection where appropriate, and provider-side spending controls before broad public use. Existing provider accounts may have their own limits; billing alerts alone are not a hard spend cap.

User code and issue text are sent to Google Gemini. Do not submit credentials, personal data, or private source you are not allowed to share with the provider. The function does not deliberately persist source or results, but the hosting provider and Google have their own processing and retention policies. Review them and update the product privacy notice before accepting real user code.

The system prompt treats source, comments, strings, and issue text as untrusted data and explicitly rejects embedded instructions. No tools, network browsing, shell commands, repository writes, or code execution are available to the model through this endpoint. Prompt injection can still affect a model's advice: never trust a proposed fix without review. Render all returned text/code as text, never as HTML. This endpoint does not run tests or use an execution sandbox. `verification` is always `not_run`; suggested tests are instructions for a person to review and run in an appropriate isolated environment, not evidence that a fix works.

## Tests

From the project root:

```sh
node --test tests/debug-api.test.js
```

The suite uses Node's built-in test runner and mocked HTTP providers. It covers input/output shape and length checks, byte limits including streamed bodies, methods, browser origins, safe provider errors, bad/truncated/blocked provider responses, configurable models, deadlines, header-only credentials, and per-instance throttling. No live Gemini request or submitted-source execution occurs. No deployment was performed as part of implementing these files.
