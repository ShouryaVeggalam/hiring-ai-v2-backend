"""Onboarding Agent endpoints (/onboarding)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.common import Page
from app.schemas.onboarding import OnboardingRead
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingRunRequest(BaseModel):
    candidate_id: str
    offer_id: str | None = None
    completed_items: list[str] = Field(default_factory=list)


@router.get("", response_model=Page[OnboardingRead])
def list_onboarding(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[OnboardingRead]:
    items, total = OnboardingService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[OnboardingRead](
        items=[OnboardingRead.model_validate(o) for o in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{onboarding_id}", response_model=OnboardingRead)
def get_onboarding(onboarding_id: str, db: DbSession) -> OnboardingRead:
    return OnboardingRead.model_validate(OnboardingService(db).get(onboarding_id))


@router.post("/run", response_model=AgentRunResult, dependencies=[Depends(require_recruiter)])
def run_onboarding(
    payload: OnboardingRunRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    return OnboardingService(db).run(
        payload.candidate_id,
        offer_id=payload.offer_id,
        completed_items=payload.completed_items,
        actor_id=user.id,
    )
