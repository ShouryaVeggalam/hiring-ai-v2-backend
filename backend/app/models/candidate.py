"""Candidate, Resume, and TalentPool models."""
from __future__ import annotations

from sqlalchemy import Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CandidateStage
from app.database.base import Base, TimestampMixin, UUIDMixin


class Candidate(UUIDMixin, TimestampMixin, Base):
    """A person being evaluated for one or more roles."""

    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    stage: Mapped[CandidateStage] = mapped_column(
        Enum(CandidateStage, native_enum=False, length=32),
        default=CandidateStage.DISCOVERED,
        nullable=False,
        index=True,
    )

    years_experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    skills: Mapped[list | None] = mapped_column(JSON, default=list)
    education: Mapped[list | None] = mapped_column(JSON, default=list)
    experience: Mapped[list | None] = mapped_column(JSON, default=list)
    projects: Mapped[list | None] = mapped_column(JSON, default=list)

    # Agent outputs.
    discovery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    candidate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    qualification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dossier: Mapped[dict | None] = mapped_column(JSON, default=dict)
    insights: Mapped[dict | None] = mapped_column(JSON, default=dict)

    job_opening_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_openings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    talent_pool_id: Mapped[str | None] = mapped_column(
        ForeignKey("talent_pools.id", ondelete="SET NULL"), nullable=True, index=True
    )

    job_opening: Mapped["JobOpening | None"] = relationship(back_populates="candidates")  # noqa: F821
    talent_pool: Mapped["TalentPool | None"] = relationship(back_populates="candidates")
    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    references: Mapped[list["ReferenceCheck"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )
    offers: Mapped[list["Offer"]] = relationship(  # noqa: F821
        back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Candidate {self.full_name} ({self.stage})>"


class Resume(UUIDMixin, TimestampMixin, Base):
    """A raw + parsed resume document attached to a candidate."""

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(JSON, default=dict)
    parse_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")


class TalentPool(UUIDMixin, TimestampMixin, Base):
    """A curated pool of candidates discovered by the Talent Discovery Agent."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companys.id", ondelete="SET NULL"), nullable=True, index=True
    )
    candidates: Mapped[list["Candidate"]] = relationship(back_populates="talent_pool")
