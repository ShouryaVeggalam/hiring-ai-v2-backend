"""Celestra Hiring AI — FastAPI application entry point."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app import __version__
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

_db_setup_lock = asyncio.Lock()
_db_setup_done = False


def _run_db_setup() -> None:
    """Create tables and seed admin user (runs in a thread)."""
    from app.database.base import Base
    from app.database.session import SessionLocal, get_engine

    import app.models  # noqa: F401 — register ORM metadata

    if settings.AUTO_CREATE_TABLES or not settings.is_production:
        Base.metadata.create_all(bind=get_engine())
        logger.info("database_tables_ready")

    from app.core.constants import UserRole
    from app.core.security import hash_password
    from app.repositories.user import UserRepository

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if not repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL):
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


async def _init_db_background() -> None:
    """Run DB setup without blocking the server from binding to PORT."""
    global _db_setup_done
    async with _db_setup_lock:
        if _db_setup_done:
            return
        try:
            await asyncio.to_thread(_run_db_setup)
            _db_setup_done = True
        except Exception as exc:
            logger.error("database_setup_failed", error=str(exc), exc_info=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Non-blocking startup so Render health checks pass immediately."""
    logger.info(
        "startup",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        version=__version__,
    )
    # Fire-and-forget — do NOT await. Render requires PORT binding quickly.
    asyncio.create_task(_init_db_background())
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    """Application factory (used by uvicorn --factory)."""
    from app.api.router import api_router

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

    origins = settings.cors_origins
    allow_all = origins == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.mount("/metrics", make_asgi_app())
    return app
