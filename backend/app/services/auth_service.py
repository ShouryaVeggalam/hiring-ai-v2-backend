"""Authentication service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, Token


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: RegisterRequest) -> User:
        if self.users.get_by_email(data.email):
            raise ConflictError("A user with this email already exists")
        user = self.users.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            company_id=data.company_id,
        )
        self.db.commit()
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    def login(self, email: str, password: str) -> Token:
        user = self.authenticate(email, password)
        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token, expected_type="refresh")
        user = self.users.get(payload.get("sub", ""))
        if not user or not user.is_active:
            raise AuthenticationError("Invalid refresh token")
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> Token:
        claims = {"role": user.role.value, "email": user.email}
        return Token(
            access_token=create_access_token(user.id, claims),
            refresh_token=create_refresh_token(user.id),
        )
