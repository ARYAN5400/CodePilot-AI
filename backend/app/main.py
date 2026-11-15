import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import InvalidToken
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pymongo import AsyncMongoClient

from .config import get_settings
from .github import GitHubClient, GitHubError
from .security import decrypt_token, digest_secret, encrypt_token, new_secret, pkce_pair

settings = get_settings()
client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    if settings.environment == "production":
        missing = [key for key, val in {"GITHUB_CLIENT_ID": settings.github_client_id, "GITHUB_CLIENT_SECRET": settings.github_client_secret.get_secret_value(), "MONGODB_URI": settings.mongodb_uri, "FERNET_KEY": settings.fernet_key.get_secret_value()}.items() if not val or val.startswith("replace-") or "generate-a" in val]
        if missing:
            raise RuntimeError("Missing required production configuration: " + ", ".join(missing))
        mongo_uri = settings.mongodb_uri.lower()
        if not (mongo_uri.startswith("mongodb+srv://") or "tls=true" in mongo_uri):
            raise RuntimeError("Production MongoDB connections must use TLS")
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]
    await db.states.create_index("expires_at", expireAfterSeconds=0)
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    yield
    if client:
        await client.close()

app = FastAPI(title="CodePilot API", version="0.1.0", lifespan=lifespan, docs_url=None if settings.environment == "production" else "/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

def _cookie_secure() -> bool:
    return settings.environment == "production"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "codepilot-api"}

@app.get("/auth/github/start")
async def github_start():
    if not settings.github_client_id or not settings.github_client_secret.get_secret_value() or not settings.fernet_key.get_secret_value():
        raise HTTPException(503, "GitHub sign-in is not configured")
    state = new_secret(32)
    verifier, challenge = pkce_pair()
    await db.states.insert_one({"_id": digest_secret(state), "verifier": verifier, "expires_at": datetime.now(timezone.utc) + timedelta(seconds=settings.state_ttl_seconds)})
    params = {"client_id": settings.github_client_id, "redirect_uri": settings.api_base_url + "/auth/github/callback", "state": state, "code_challenge": challenge, "code_challenge_method": "S256", "scope": ""}
    response = RedirectResponse("https://github.com/login/oauth/authorize?" + urlencode(params), status_code=302)
    response.set_cookie("cp_oauth_state", state, httponly=True, secure=_cookie_secure(), samesite="lax", max_age=settings.state_ttl_seconds, path="/auth/github/callback")
    return response

@app.get("/auth/github/callback")
async def github_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error or not code or not state:
        raise HTTPException(400, "GitHub authorization was cancelled or incomplete")
    browser_state = request.cookies.get("cp_oauth_state")
    if not browser_state or not secrets.compare_digest(browser_state, state):
        raise HTTPException(400, "Invalid authorization state")
    state_doc = await db.states.find_one_and_delete({"_id": digest_secret(state), "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not state_doc:
        raise HTTPException(400, "Invalid or expired authorization state")
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=False) as http:
        response = await http.post("https://github.com/login/oauth/access_token", headers={"Accept": "application/json"}, data={"client_id": settings.github_client_id, "client_secret": settings.github_client_secret.get_secret_value(), "code": code, "redirect_uri": settings.api_base_url + "/auth/github/callback", "code_verifier": state_doc["verifier"]})
        if response.is_error:
            raise HTTPException(502, "GitHub authorization could not be completed")
        payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise HTTPException(502, "GitHub did not authorize the connection")
    session_secret = new_secret(32)
    await db.sessions.insert_one({"_id": digest_secret(session_secret), "token_ciphertext": encrypt_token(token, settings.fernet_key.get_secret_value()), "expires_at": datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)})
    response = RedirectResponse(settings.frontend_origin + "/?github=connected", status_code=303)
    response.delete_cookie("cp_oauth_state", httponly=True, secure=_cookie_secure(), samesite="lax", path="/auth/github/callback")
    secure_cookie = _cookie_secure()
    response.set_cookie("cp_session", session_secret, httponly=True, secure=secure_cookie, samesite="none" if secure_cookie else "lax", max_age=settings.session_ttl_seconds, path="/")
    return response

async def _github_client(request: Request) -> GitHubClient:
    secret = request.cookies.get("cp_session")
    if not secret:
        raise HTTPException(401, "Sign-in required")
    doc = await db.sessions.find_one({"_id": digest_secret(secret), "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not doc:
        raise HTTPException(401, "Session expired")
    try:
        token = decrypt_token(doc["token_ciphertext"], settings.fernet_key.get_secret_value())
    except (InvalidToken, KeyError):
        raise HTTPException(401, "Session could not be validated")
    return GitHubClient(token)

@app.get("/api/me")
async def me(request: Request):
    github = await _github_client(request)
    try:
        return await github.identity()
    except GitHubError as exc:
        raise HTTPException(502, str(exc))
    finally:
        await github.close()

@app.get("/api/repositories")
async def repositories(request: Request):
    github = await _github_client(request)
    try:
        return {"repositories": await github.repositories(), "permissions": "read-only"}
    except GitHubError as exc:
        raise HTTPException(502, str(exc))
    finally:
        await github.close()

@app.post("/auth/logout")
async def logout(request: Request):
    secret = request.cookies.get("cp_session")
    if secret:
        await db.sessions.delete_one({"_id": digest_secret(secret)})
    response = RedirectResponse(settings.frontend_origin, status_code=303)
    secure_cookie = _cookie_secure()
    response.delete_cookie("cp_session", httponly=True, secure=secure_cookie, samesite="none" if secure_cookie else "lax", path="/")
    return response
