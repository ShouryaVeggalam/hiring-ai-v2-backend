"""Job opening schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import JobPriority, JobStatus, SeniorityLevel
from app.schemas.common import TimestampedSchema


class JobBase(BaseModel):
    title: str
    description: str | None = None
    priority: JobPriority = JobPriority.MEDIUM
    seniority: SeniorityLevel = SeniorityLevel.MID
    location: str | None = None
    employment_type: str | None = None
    headcount: int = 1
    salary_min: int | None = None
    salary_max: int | None = None
    min_experience_years: float = 0.0
    education_requirement: str | None = None
    company_id: str | None = None
    department_id: str | None = None
    hiring_manager_id: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: JobStatus | None = None
    priority: JobPriority | None = None
    seniority: SeniorityLevel | None = None
    location: str | None = None
    headcount: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    required_skills: list | None = None
    preferred_skills: list | None = None


class JobRead(TimestampedSchema):
    title: str
    description: str | None = None
    status: JobStatus
    priority: JobPriority
    seniority: SeniorityLevel
    location: str | None = None
    employment_type: str | None = None
    headcount: int
    required_skills: list = Field(default_factory=list)
    preferred_skills: list = Field(default_factory=list)
    responsibilities: list = Field(default_factory=list)
    job_blueprint: dict | None = None
    hiring_strategy: dict | None = None
    interview_plan: dict | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_benchmark: dict | None = None
    min_experience_years: float
    education_requirement: str | None = None
    company_id: str | None = None
    department_id: str | None = None
    hiring_manager_id: str | None = None


class JobBlueprintRequest(BaseModel):
    """Inputs to the Job Intelligence Agent."""

    title: str
    seniority: SeniorityLevel = SeniorityLevel.MID
    department: str | None = None
    location: str | None = None
    context: str | None = Field(default=None, description="Free-form hiring context")
    must_have_skills: list[str] = Field(default_factory=list)
