"""Shared API dependencies: DB session, auth, and RBAC."""
from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ROLE_RANK, UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


DbSession = Annotated[Session, Depends(get_db_session)]


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise AuthenticationError("Not authenticated")
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token subject")
    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """Dependency factory enforcing that the user holds one of ``roles``
    (or any role of higher privilege rank)."""

    min_rank = min(ROLE_RANK[r] for r in roles) if roles else 0

    def _checker(current_user: CurrentUser) -> User:
        if current_user.is_superuser:
            return current_user
        if ROLE_RANK.get(current_user.role, 0) < min_rank:
            raise AuthorizationError("Insufficient permissions for this action")
        return current_user

    return _checker


# Convenience role guards.
require_admin = require_roles(UserRole.ADMIN)
require_manager = require_roles(UserRole.HR_MANAGER)
require_recruiter = require_roles(UserRole.RECRUITER)
