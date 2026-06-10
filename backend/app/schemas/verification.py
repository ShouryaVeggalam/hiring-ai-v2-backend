"""Reference verification schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import ReferenceStatus
from app.schemas.common import TimestampedSchema


class ReferenceBase(BaseModel):
    referee_name: str | None = None
    referee_contact: str | None = None
    relationship_type: str | None = None
    claims_to_validate: list = Field(default_factory=list)
    candidate_id: str


class ReferenceCreate(ReferenceBase):
    pass


class ReferenceSubmit(BaseModel):
    response: str


class ReferenceRead(TimestampedSchema):
    referee_name: str | None = None
    referee_contact: str | None = None
    relationship_type: str | None = None
    status: ReferenceStatus
    response: str | None = None
    claims_to_validate: list = Field(default_factory=list)
    employment_verified: bool | None = None
    education_verified: bool | None = None
    verification_score: float | None = None
    trust_score: float | None = None
    risk_alerts: list = Field(default_factory=list)
    analysis: dict | None = None
    candidate_id: str
