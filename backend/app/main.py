"""Celestra Hiring AI — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.database.base import Base
from app.database.session import SessionLocal, engine

# Import models so they register on Base.metadata.
import app.models  # noqa: F401

logger = get_logger(__name__)


def _seed_superuser() -> None:
    """Create the first admin user if none exists."""
    from app.core.constants import UserRole
    from app.core.security import hash_password
    from app.repositories.user import UserRepository

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL):
            return
        repo.create(
            email=settings.FIRST_SUPERUSER_EMAIL,
            hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
            full_name=settings.FIRST_SUPERUSER_NAME,
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
        )
        db.commit()
        logger.info("superuser_seeded", email=settings.FIRST_SUPERUSER_EMAIL)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info("startup", app=settings.APP_NAME, env=settings.APP_ENV, version=__version__)
    # Create tables in dev; production should use Alembic migrations.
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
    _seed_superuser()
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Celestra Hiring AI — Your AI Hiring Department. "
            "An autonomous hiring operating system that finds, evaluates, selects, "
            "hires, and onboards talent with minimal recruiter involvement."
        ),
        version=__version__,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # CORS
    origins = settings.BACKEND_CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Prometheus metrics at /metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_app()
