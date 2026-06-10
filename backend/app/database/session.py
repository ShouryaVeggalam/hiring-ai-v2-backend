"""Engine and session management."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _pool_kwargs() -> dict:
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if settings.is_production:
        kwargs.update(pool_size=5, max_overflow=5)
        if "postgresql" in settings.sqlalchemy_database_uri:
            kwargs["connect_args"] = {"connect_timeout": 10}
    else:
        kwargs.update(pool_size=10, max_overflow=20)
    return kwargs


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine (created lazily on first use)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.sqlalchemy_database_uri,
            echo=settings.SQL_ECHO,
            **_pool_kwargs(),
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the shared session factory (created lazily on first use)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _session_factory


def SessionLocal() -> Session:
    """Create a new database session."""
    return get_session_factory()()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def __getattr__(name: str):
    """Lazy module-level ``engine`` alias for backwards compatibility."""
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
