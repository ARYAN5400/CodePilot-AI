import base64
import hashlib
import secrets
from cryptography.fernet import Fernet

def new_secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)

def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge

def digest_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def encrypt_token(token: str, key: str) -> str:
    return Fernet(key.encode("ascii")).encrypt(token.encode("utf-8")).decode("ascii")

def decrypt_token(value: str, key: str) -> str:
    return Fernet(key.encode("ascii")).decrypt(value.encode("ascii")).decode("utf-8")
