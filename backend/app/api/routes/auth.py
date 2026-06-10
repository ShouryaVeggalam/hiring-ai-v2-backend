"""Authentication endpoints: register, login, refresh, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, Token
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: DbSession) -> UserRead:
    user = AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: DbSession) -> Token:
    return AuthService(db).login(payload.email, payload.password)


@router.post("/login/oauth", response_model=Token)
def login_oauth(
    db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """OAuth2 password-flow login (enables the Swagger 'Authorize' button)."""
    return AuthService(db).login(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: DbSession) -> Token:
    return AuthService(db).refresh(payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
