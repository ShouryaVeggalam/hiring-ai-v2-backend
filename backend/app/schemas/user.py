"""User schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import UserRole
from app.schemas.common import TimestampedSchema


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.VIEWER
    company_id: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    company_id: str | None = None


class UserRead(TimestampedSchema):
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    company_id: str | None = None
