"""Engine and session management."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Smaller pool for free-tier hosts (Render, Railway, …).
_pool_kwargs: dict = {"pool_pre_ping": True, "future": True}
if settings.is_production:
    _pool_kwargs.update(pool_size=5, max_overflow=5)
    if "postgresql" in settings.sqlalchemy_database_uri:
        _pool_kwargs["connect_args"] = {"connect_timeout": 10}
else:
    _pool_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.SQL_ECHO,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
