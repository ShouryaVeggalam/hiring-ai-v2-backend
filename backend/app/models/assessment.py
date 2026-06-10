"""Assessment model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AssessmentStatus, AssessmentType
from app.database.base import Base, TimestampMixin, UUIDMixin


class Assessment(UUIDMixin, TimestampMixin, Base):
    """A skills assessment evaluated by the Assessment Agent."""

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(AssessmentType, native_enum=False, length=32),
        default=AssessmentType.CODING,
        nullable=False,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, native_enum=False, length=32),
        default=AssessmentStatus.PENDING,
        nullable=False,
        index=True,
    )
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI outputs.
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    skill_breakdown: Mapped[dict | None] = mapped_column(JSON, default=dict)
    risk_areas: Mapped[list | None] = mapped_column(JSON, default=list)
    analytics: Mapped[dict | None] = mapped_column(JSON, default=dict)

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_opening_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate: Mapped["Candidate"] = relationship(back_populates="assessments")  # noqa: F821
