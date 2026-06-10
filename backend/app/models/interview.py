"""Interview model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import InterviewRecommendation, InterviewStatus, InterviewType
from app.database.base import Base, TimestampMixin, UUIDMixin


class Interview(UUIDMixin, TimestampMixin, Base):
    """A scheduled or completed interview managed by the Interview Agent."""

    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=False, length=32),
        default=InterviewType.SCREENING,
        nullable=False,
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, native_enum=False, length=32),
        default=InterviewStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(nullable=True)
    interviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI artefacts.
    plan: Mapped[dict | None] = mapped_column(JSON, default=dict)
    questions: Mapped[list | None] = mapped_column(JSON, default=list)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, default=dict)
    insights: Mapped[dict | None] = mapped_column(JSON, default=dict)

    interview_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[InterviewRecommendation | None] = mapped_column(
        Enum(InterviewRecommendation, native_enum=False, length=32), nullable=True
    )

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_opening_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate: Mapped["Candidate"] = relationship(back_populates="interviews")  # noqa: F821
