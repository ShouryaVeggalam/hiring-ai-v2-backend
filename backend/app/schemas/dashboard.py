"""Dashboard and analytics schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationRead


class ActivityItem(BaseModel):
    id: str
    action: str
    description: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: str


class HiringHealth(BaseModel):
    """Output of the Hiring Health Engine."""

    hiring_health_score: float
    time_to_hire_days: float
    interview_success_rate: float
    offer_acceptance_rate: float
    candidate_quality_score: float
    hiring_velocity: float
    breakdown: dict = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Aggregated payload for the single /dashboard endpoint."""

    open_roles: int
    candidates_discovered: int
    candidates_qualified: int
    interviews_active: int
    offers_sent: int
    hiring_velocity: float
    hiring_health_score: float
    candidate_quality_score: float
    top_recommendations: list[RecommendationRead] = Field(default_factory=list)
    recent_activity: list[ActivityItem] = Field(default_factory=list)
    health: HiringHealth | None = None
