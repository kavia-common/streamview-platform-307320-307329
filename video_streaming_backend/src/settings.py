"""Application configuration (env-driven).

Environment variables required (set via .env by orchestrator/deployment):
- DATABASE_URL
- JWT_SECRET

Other optional variables:
- JWT_ALG (default HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES (default 15)
- REFRESH_TOKEN_EXPIRE_DAYS (default 30)
- CORS_ORIGINS (comma-separated list, or "*" for all)
- BACKEND_BASE_URL (optional)
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL", description="PostgreSQL connection URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET", description="Secret used to sign JWTs")

    jwt_alg: str = Field("HS256", alias="JWT_ALG", description="JWT signing algorithm")

    access_token_expire_minutes: int = Field(
        15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Access token expiration window in minutes",
    )
    refresh_token_expire_days: int = Field(
        30,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
        description="Refresh token expiration window in days",
    )

    cors_origins: str = Field(
        "*",
        alias="CORS_ORIGINS",
        description='Comma-separated list of allowed origins or "*"',
    )

    backend_base_url: str | None = Field(
        None, alias="BACKEND_BASE_URL", description="Public base URL for the backend (optional)"
    )

    def parsed_cors_origins(self) -> List[str]:
        """Return CORS origins as a list compatible with CORSMiddleware."""
        raw = (self.cors_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor (safe to call from anywhere)."""
    return Settings()
