"""Application configuration loaded from environment variables.

Uses pydantic-settings so configuration is typed, validated, and
documented in a single place.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- Application ----
    APP_NAME: str = "Celestra Hiring AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me-super-secret-key-please-rotate-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # ---- Database ----
    POSTGRES_USER: str = "celestra"
    POSTGRES_PASSWORD: str = "celestra"
    POSTGRES_DB: str = "celestra_hiring"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    SQL_ECHO: bool = False
    # Create tables on startup (handy for free PaaS without a migration step).
    AUTO_CREATE_TABLES: bool = True

    # ---- Redis / Celery ----
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---- AI / LLM ----
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048
    LLM_OFFLINE_MODE: bool = True

    # ---- First superuser ----
    FIRST_SUPERUSER_EMAIL: str = "admin@celestra.ai"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@12345"
    FIRST_SUPERUSER_NAME: str = "Celestra Admin"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @staticmethod
    def _normalize_db_url(url: str) -> str:
        """Normalise provider-supplied URLs to a psycopg2 driver URL.

        Managed hosts (Render, Heroku, Railway, …) hand out URLs like
        ``postgres://`` or ``postgresql://``; SQLAlchemy needs an explicit
        driver, so we coerce them to ``postgresql+psycopg2://``. SQLite URLs
        are passed through untouched.
        """
        if url.startswith("sqlite"):
            return url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Resolve the SQLAlchemy connection URI.

        Honours an explicit ``DATABASE_URL`` when provided, otherwise builds
        one from the individual Postgres settings.
        """
        if self.DATABASE_URL:
            return self._normalize_db_url(self.DATABASE_URL)
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
