"""User account model."""
from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import UserRole
from app.database.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """An authenticated platform user with an RBAC role."""

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=32),
        default=UserRole.VIEWER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companys.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company: Mapped["Company | None"] = relationship(back_populates="users")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} ({self.role})>"
