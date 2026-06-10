"""Hiring recommendation schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import AgentName, RecommendationType
from app.schemas.common import TimestampedSchema


class RecommendationRead(TimestampedSchema):
    recommendation_type: RecommendationType
    source_agent: AgentName
    title: str
    rationale: str | None = None
    confidence: float | None = None
    priority: int
    payload: dict | None = None
    is_acted_on: bool
    company_id: str | None = None
    candidate_id: str | None = None
    job_opening_id: str | None = None


class RecommendationCreate(BaseModel):
    recommendation_type: RecommendationType
    source_agent: AgentName
    title: str
    rationale: str | None = None
    confidence: float | None = None
    priority: int = 0
    payload: dict = Field(default_factory=dict)
    company_id: str | None = None
    candidate_id: str | None = None
    job_opening_id: str | None = None
