## Student debugging workspace update

Open `/#workspace` for code input, file import, prepared practice examples, AI explanations, before/after code review, and fix downloads. The new `/api/debug` Vercel function needs a server-only Gemini API key. See [DEBUGGING_SETUP.md](DEBUGGING_SETUP.md). No submitted code is executed. The landing page agent animation and dashboard remain illustrative.

# CodePilot AI

Live frontend: https://codepilot-ai-wheat.vercel.app (static Vercel Drop; Git auto-deploy is not connected).


A student-focused AI software-engineering product concept: learn debugging by tracing bugs, exploring suggested fixes, and understanding tests.

## Website

React 19 + Vite 6. The responsive frontend contains a product overview, clearly labelled illustrative dashboard, interactive agent walkthrough, patch/test tabs, and informational demo dialogs.

```powershell
npm install
npm run dev
npm run build
```

## Backend scaffold

See [`backend/README.md`](backend/README.md) and [`BACKEND_PLAN.md`](BACKEND_PLAN.md). The FastAPI scaffold outlines GitHub App sign-in with state + PKCE, encrypted server-side sessions, and read-only repository metadata access. It requires a real GitHub App, MongoDB, and secrets to be configured before it can run with user data.

## Current status

This is a frontend preview and backend starter, not a live AI engineering service. Authentication, GitHub connection, code execution, Docker test runner, and account UI remain unconnected. This branch adds a source-analysis workspace and a Gemini-backed API that requires server-side configuration and deployment. Dashboard numbers, repository names, patches, and test results are illustrative. No change is made to a repository by this demo.

## Safety notes

Never commit `.env` or any API keys, GitHub tokens, Vercel tokens, MongoDB credentials, private keys, or encryption keys. Keep GitHub access read-only until the product's write workflow has been reviewed and explicitly approved. Do not run untrusted repository code in the API service.
