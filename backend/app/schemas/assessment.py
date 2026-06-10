"""Assessment schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import AssessmentStatus, AssessmentType
from app.schemas.common import TimestampedSchema


class AssessmentBase(BaseModel):
    title: str
    assessment_type: AssessmentType = AssessmentType.CODING
    prompt: str | None = None
    due_at: datetime | None = None
    candidate_id: str
    job_opening_id: str | None = None


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentSubmit(BaseModel):
    submission: str


class AssessmentRead(TimestampedSchema):
    title: str
    assessment_type: AssessmentType
    status: AssessmentStatus
    prompt: str | None = None
    submission: str | None = None
    due_at: datetime | None = None
    submitted_at: datetime | None = None
    score: float | None = None
    max_score: float
    skill_breakdown: dict | None = None
    risk_areas: list = Field(default_factory=list)
    analytics: dict | None = None
    candidate_id: str
    job_opening_id: str | None = None
