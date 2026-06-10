"""Reference / background verification model."""
from __future__ import annotations

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ReferenceStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class ReferenceCheck(UUIDMixin, TimestampMixin, Base):
    """A reference / background check handled by the Verification Agent."""

    referee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referee_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    relationship_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[ReferenceStatus] = mapped_column(
        Enum(ReferenceStatus, native_enum=False, length=32),
        default=ReferenceStatus.PENDING,
        nullable=False,
        index=True,
    )

    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    claims_to_validate: Mapped[list | None] = mapped_column(JSON, default=list)

    # AI outputs.
    employment_verified: Mapped[bool | None] = mapped_column(nullable=True)
    education_verified: Mapped[bool | None] = mapped_column(nullable=True)
    verification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trust_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_alerts: Mapped[list | None] = mapped_column(JSON, default=list)
    analysis: Mapped[dict | None] = mapped_column(JSON, default=dict)

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate: Mapped["Candidate"] = relationship(back_populates="references")  # noqa: F821
