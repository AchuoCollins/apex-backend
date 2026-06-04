from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import secrets


def _normalize_database_url(url: str) -> str:
    """Make any standard Postgres URL compatible with SQLAlchemy + asyncpg.

    - Render/Heroku expose URLs as ``postgres://`` which SQLAlchemy rejects.
    - asyncpg does not understand libpq query params like ``sslmode`` or
      ``channel_binding`` — they raise ``InvalidArgumentError`` at connect time.
    """
    if not url:
        return url
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    # Strip libpq-only query params that asyncpg rejects.
    drop = {"sslmode", "channel_binding", "gssencmode", "target_session_attrs"}
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in drop]
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "APEX — AI Physique Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | production | testing

    # ── API ──────────────────────────────────────────────
    API_V1_PREFIX: str = "/api"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://apex:apex_pass@localhost:5432/apex_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── JWT ──────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Security ─────────────────────────────────────────
    BCRYPT_ROUNDS: int = 12

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        return _normalize_database_url(v)

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
