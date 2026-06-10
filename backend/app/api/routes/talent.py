"""Talent Discovery Agent endpoints (/talent)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.candidate import TalentDiscoveryRequest
from app.services.talent_service import TalentService

router = APIRouter(prefix="/talent", tags=["talent-discovery"])


@router.post("/discover", response_model=AgentRunResult, dependencies=[Depends(require_recruiter)])
def discover_talent(
    payload: TalentDiscoveryRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    """Search talent pools and discover candidates for a role."""
    return TalentService(db).discover(payload, company_id=user.company_id, actor_id=user.id)
