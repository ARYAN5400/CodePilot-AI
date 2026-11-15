from functools import lru_cache
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"
    api_base_url: str = "http://localhost:8000"
    github_client_id: str = ""
    github_client_secret: SecretStr = SecretStr("")
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "codepilot"
    fernet_key: SecretStr = SecretStr("")
    session_ttl_seconds: int = 28800
    state_ttl_seconds: int = 600

    @field_validator("frontend_origin", "api_base_url")
    @classmethod
    def require_origin(cls, value: str) -> str:
        value = value.rstrip("/")
        if not value.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("Origin must be HTTPS (HTTP is allowed only for local development)")
        return value

@lru_cache
def get_settings() -> Settings:
    return Settings()
