"""Offer model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OfferStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class Offer(UUIDMixin, TimestampMixin, Base):
    """A compensation offer produced by the Offer Agent."""

    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, native_enum=False, length=32),
        default=OfferStatus.DRAFT,
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI outputs.
    offer_package: Mapped[dict | None] = mapped_column(JSON, default=dict)
    compensation_analysis: Mapped[dict | None] = mapped_column(JSON, default=dict)
    negotiation_notes: Mapped[list | None] = mapped_column(JSON, default=list)
    offer_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    acceptance_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_opening_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate: Mapped["Candidate"] = relationship(back_populates="offers")  # noqa: F821
    onboarding: Mapped["Onboarding | None"] = relationship(  # noqa: F821
        back_populates="offer", uselist=False
    )
