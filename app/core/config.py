from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import secrets


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

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


settings = Settings()
