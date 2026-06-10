"""Hiring recommendation model."""
from __future__ import annotations

from sqlalchemy import Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AgentName, RecommendationType
from app.database.base import Base, TimestampMixin, UUIDMixin


class HiringRecommendation(UUIDMixin, TimestampMixin, Base):
    """An actionable recommendation emitted by any agent."""

    recommendation_type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType, native_enum=False, length=32), nullable=False, index=True
    )
    source_agent: Mapped[AgentName] = mapped_column(
        Enum(AgentName, native_enum=False, length=32), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, default=dict)
    is_acted_on: Mapped[bool] = mapped_column(default=False, nullable=False)

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companys.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidate_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_opening_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), nullable=True, index=True
    )
