"""Candidate / Resume / TalentPool schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import CandidateStage
from app.schemas.common import TimestampedSchema


class CandidateBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    source: str | None = None
    linkedin_url: str | None = None
    years_experience: float = 0.0
    skills: list = Field(default_factory=list)
    education: list = Field(default_factory=list)
    experience: list = Field(default_factory=list)
    projects: list = Field(default_factory=list)
    job_opening_id: str | None = None
    talent_pool_id: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    stage: CandidateStage | None = None
    years_experience: float | None = None
    skills: list | None = None
    job_opening_id: str | None = None


class CandidateRead(TimestampedSchema):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    source: str | None = None
    linkedin_url: str | None = None
    stage: CandidateStage
    years_experience: float
    skills: list = Field(default_factory=list)
    education: list = Field(default_factory=list)
    experience: list = Field(default_factory=list)
    projects: list = Field(default_factory=list)
    discovery_score: float | None = None
    candidate_score: float | None = None
    qualification_score: float | None = None
    match_score: float | None = None
    dossier: dict | None = None
    insights: dict | None = None
    job_opening_id: str | None = None
    talent_pool_id: str | None = None


class ResumeRead(TimestampedSchema):
    filename: str
    file_type: str
    parse_status: str
    raw_text: str | None = None
    parsed_data: dict | None = None
    candidate_id: str


class TalentPoolBase(BaseModel):
    name: str
    description: str | None = None
    tags: list = Field(default_factory=list)
    company_id: str | None = None


class TalentPoolCreate(TalentPoolBase):
    pass


class TalentPoolRead(TimestampedSchema, TalentPoolBase):
    size: int = 0


class TalentDiscoveryRequest(BaseModel):
    """Inputs to the Talent Discovery Agent."""

    job_opening_id: str | None = None
    query: str | None = None
    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    limit: int = Field(default=20, ge=1, le=200)
