"""User management endpoints (admin-scoped)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserRead], dependencies=[Depends(require_admin)])
def list_users(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[UserRead]:
    repo = UserRepository(db)
    items = repo.list(offset=(page - 1) * page_size, limit=page_size)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in items],
        total=repo.count(),
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserRead, status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: DbSession) -> UserRead:
    repo = UserRepository(db)
    if repo.get_by_email(payload.email):
        raise ConflictError("A user with this email already exists")
    data = payload.model_dump(exclude={"password"})
    user = repo.create(**data, hashed_password=hash_password(payload.password))
    db.commit()
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def get_user(user_id: str, db: DbSession) -> UserRead:
    user = UserRepository(db).get(user_id)
    if not user:
        raise NotFoundError("User not found")
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user(user_id: str, payload: UserUpdate, db: DbSession) -> UserRead:
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    if payload.password:
        data["hashed_password"] = hash_password(payload.password)
    user = repo.update(user, data)
    db.commit()
    return UserRead.model_validate(user)
