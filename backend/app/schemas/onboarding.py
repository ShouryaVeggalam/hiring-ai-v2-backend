"""Onboarding schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import OnboardingStatus
from app.schemas.common import TimestampedSchema


class OnboardingBase(BaseModel):
    candidate_id: str
    offer_id: str | None = None
    start_date: datetime | None = None


class OnboardingCreate(OnboardingBase):
    pass


class OnboardingUpdate(BaseModel):
    status: OnboardingStatus | None = None
    documents: list | None = None
    training_modules: list | None = None
    checklist: list | None = None


class OnboardingRead(TimestampedSchema):
    status: OnboardingStatus
    start_date: datetime | None = None
    completed_at: datetime | None = None
    documents: list = Field(default_factory=list)
    training_modules: list = Field(default_factory=list)
    checklist: list = Field(default_factory=list)
    workflow: dict | None = None
    onboarding_score: float | None = None
    completion_percentage: float
    candidate_id: str
    offer_id: str | None = None
