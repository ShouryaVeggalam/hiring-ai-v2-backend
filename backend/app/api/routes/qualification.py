"""Qualification Agent endpoints (/qualification)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.services.qualification_service import QualificationService

router = APIRouter(prefix="/qualification", tags=["qualification"])


class QualificationRequest(BaseModel):
    job_opening_id: str
    candidate_ids: list[str] | None = Field(default=None)


@router.post("/rank", response_model=AgentRunResult, dependencies=[Depends(require_recruiter)])
def rank_candidates(
    payload: QualificationRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    """Rank candidates against a job and produce a shortlist."""
    return QualificationService(db).qualify(
        payload.job_opening_id,
        payload.candidate_ids,
        company_id=user.company_id,
        actor_id=user.id,
    )
