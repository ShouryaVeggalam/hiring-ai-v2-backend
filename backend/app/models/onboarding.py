"""Onboarding model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OnboardingStatus
from app.database.base import Base, TimestampMixin, UUIDMixin


class Onboarding(UUIDMixin, TimestampMixin, Base):
    """A new-hire onboarding workflow managed by the Onboarding Agent."""

    status: Mapped[OnboardingStatus] = mapped_column(
        Enum(OnboardingStatus, native_enum=False, length=32),
        default=OnboardingStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    documents: Mapped[list | None] = mapped_column(JSON, default=list)
    training_modules: Mapped[list | None] = mapped_column(JSON, default=list)
    checklist: Mapped[list | None] = mapped_column(JSON, default=list)
    workflow: Mapped[dict | None] = mapped_column(JSON, default=dict)

    onboarding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offer_id: Mapped[str | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    offer: Mapped["Offer | None"] = relationship(back_populates="onboarding")  # noqa: F821
