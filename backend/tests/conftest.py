"""Pytest fixtures — in-memory SQLite for fast, isolated tests."""
from __future__ import annotations

import os

# Must be set before any app imports so settings pick up test config.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("LLM_OFFLINE_MODE", "true")
os.environ.setdefault("APP_ENV", "development")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app
from app.models.user import User
from app.core.constants import UserRole

# Import models to register metadata.
import app.models  # noqa: F401


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine) -> Session:
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    def _override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("Test@12345"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client: TestClient, admin_user: User) -> dict[str, str]:
    resp = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "admin@test.com", "password": "Test@12345"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
