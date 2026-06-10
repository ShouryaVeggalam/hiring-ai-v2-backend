"""Hiring report model."""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ReportType
from app.database.base import Base, TimestampMixin, UUIDMixin


class HiringReport(UUIDMixin, TimestampMixin, Base):
    """A generated report (hiring, candidate, executive, etc.)."""

    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, native_enum=False, length=32), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict | None] = mapped_column(JSON, default=dict)
    period_start: Mapped[str | None] = mapped_column(String(32), nullable=True)
    period_end: Mapped[str | None] = mapped_column(String(32), nullable=True)
    generated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companys.id", ondelete="SET NULL"), nullable=True, index=True
    )
