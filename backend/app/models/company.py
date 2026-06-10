"""Company, Department, and Role (org structure) models."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Company(UUIDMixin, TimestampMixin, Base):
    """A tenant organisation that hires talent."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    culture_values: Mapped[dict | None] = mapped_column(JSON, default=dict)

    users: Mapped[list["User"]] = relationship(back_populates="company")  # noqa: F821
    departments: Mapped[list["Department"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Department(UUIDMixin, TimestampMixin, Base):
    """A department/team within a company."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_headcount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # AI-derived workload / capacity metrics maintained by the workforce agent.
    capacity_metrics: Mapped[dict | None] = mapped_column(JSON, default=dict)

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companys.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped["Company"] = relationship(back_populates="departments")
    roles: Mapped[list["Role"]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )


class Role(UUIDMixin, TimestampMixin, Base):
    """A job role/title defined within a department (org chart entity)."""

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_competencies: Mapped[dict | None] = mapped_column(JSON, default=dict)
    salary_band_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_band_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department: Mapped["Department"] = relationship(back_populates="roles")
