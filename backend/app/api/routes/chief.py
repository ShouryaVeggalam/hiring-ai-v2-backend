"""Hiring Chief Agent endpoints (/chief)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_manager
from app.schemas.agent import AgentRunResult, OrchestrationRequest, OrchestrationResult
from app.services.chief_service import ChiefService
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/chief", tags=["hiring-chief"])


@router.get("/report", response_model=AgentRunResult, dependencies=[Depends(require_manager)])
def chief_report(
    db: DbSession,
    user: CurrentUser,
    company_id: str | None = Query(default=None),
) -> AgentRunResult:
    """AI Head of Talent executive briefing."""
    return ChiefService(db).report(company_id or user.company_id, actor_id=user.id)


@router.post("/orchestrate", response_model=OrchestrationResult, dependencies=[Depends(require_manager)])
def orchestrate_hiring(
    payload: OrchestrationRequest, db: DbSession, user: CurrentUser
) -> OrchestrationResult:
    """Run the full Hiring AI Network workflow for a role."""
    return OrchestrationService(db).run(payload, actor_id=user.id)
