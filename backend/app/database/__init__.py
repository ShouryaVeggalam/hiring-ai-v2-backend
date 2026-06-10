"""Database package: engine, session factory, and declarative base."""
from app.database.base import Base
from app.database.session import SessionLocal, get_db, get_engine

__all__ = ["Base", "SessionLocal", "get_db", "get_engine"]

# Backwards-compatible lazy alias.
def __getattr__(name: str):
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
