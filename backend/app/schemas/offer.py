"""Offer schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import OfferStatus
from app.schemas.common import TimestampedSchema


class OfferBase(BaseModel):
    title: str | None = None
    base_salary: int | None = None
    bonus: int | None = None
    equity: str | None = None
    currency: str = "USD"
    start_date: datetime | None = None
    expires_at: datetime | None = None
    candidate_id: str
    job_opening_id: str | None = None


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    status: OfferStatus | None = None
    base_salary: int | None = None
    bonus: int | None = None
    equity: str | None = None
    expires_at: datetime | None = None


class OfferRead(TimestampedSchema):
    status: OfferStatus
    title: str | None = None
    base_salary: int | None = None
    bonus: int | None = None
    equity: str | None = None
    currency: str
    start_date: datetime | None = None
    expires_at: datetime | None = None
    offer_package: dict | None = None
    compensation_analysis: dict | None = None
    negotiation_notes: list = Field(default_factory=list)
    offer_score: float | None = None
    acceptance_probability: float | None = None
    candidate_id: str
    job_opening_id: str | None = None


class OfferGenerateRequest(BaseModel):
    candidate_id: str
    job_opening_id: str | None = None
    target_base_salary: int | None = None
