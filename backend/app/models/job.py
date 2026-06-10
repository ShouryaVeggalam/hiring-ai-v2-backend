"""Job opening model."""
from __future__ import annotations

from sqlalchemy import Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobPriority, JobStatus, SeniorityLevel
from app.database.base import Base, TimestampMixin, UUIDMixin


class JobOpening(UUIDMixin, TimestampMixin, Base):
    """A requisition produced by the Job Intelligence Agent."""

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=32), default=JobStatus.DRAFT, nullable=False
    )
    priority: Mapped[JobPriority] = mapped_column(
        Enum(JobPriority, native_enum=False, length=16), default=JobPriority.MEDIUM, nullable=False
    )
    seniority: Mapped[SeniorityLevel] = mapped_column(
        Enum(SeniorityLevel, native_enum=False, length=16),
        default=SeniorityLevel.MID,
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # AI-generated artefacts (the "Job Blueprint").
    required_skills: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list | None] = mapped_column(JSON, default=list)
    responsibilities: Mapped[list | None] = mapped_column(JSON, default=list)
    job_blueprint: Mapped[dict | None] = mapped_column(JSON, default=dict)
    hiring_strategy: Mapped[dict | None] = mapped_column(JSON, default=dict)
    interview_plan: Mapped[dict | None] = mapped_column(JSON, default=dict)

    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_benchmark: Mapped[dict | None] = mapped_column(JSON, default=dict)

    min_experience_years: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education_requirement: Mapped[str | None] = mapped_column(String(128), nullable=True)

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companys.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hiring_manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        back_populates="job_opening"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobOpening {self.title} ({self.status})>"
