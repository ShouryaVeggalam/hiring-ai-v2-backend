"""Interview schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import InterviewRecommendation, InterviewStatus, InterviewType
from app.schemas.common import TimestampedSchema


class InterviewBase(BaseModel):
    interview_type: InterviewType = InterviewType.SCREENING
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    interviewer_name: str | None = None
    candidate_id: str
    job_opening_id: str | None = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    status: InterviewStatus | None = None
    scheduled_at: datetime | None = None
    interviewer_name: str | None = None
    transcript: str | None = None


class InterviewRead(TimestampedSchema):
    interview_type: InterviewType
    status: InterviewStatus
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    interviewer_name: str | None = None
    plan: dict | None = None
    questions: list = Field(default_factory=list)
    transcript: str | None = None
    feedback: dict | None = None
    insights: dict | None = None
    interview_score: float | None = None
    confidence_score: float | None = None
    recommendation: InterviewRecommendation | None = None
    candidate_id: str
    job_opening_id: str | None = None


class InterviewPlanRequest(BaseModel):
    candidate_id: str
    job_opening_id: str | None = None
    interview_type: InterviewType = InterviewType.TECHNICAL
    focus_areas: list[str] = Field(default_factory=list)


class TranscriptAnalysisRequest(BaseModel):
    transcript: str
