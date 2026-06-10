"""Workforce Planning Agent endpoints (/workforce)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, require_manager
from app.schemas.agent import AgentRunResult, WorkforceAnalysisRequest
from app.services.workforce_service import WorkforceService

router = APIRouter(prefix="/workforce", tags=["workforce-planning"])


@router.post("/analyze", response_model=AgentRunResult, dependencies=[Depends(require_manager)])
def analyze_workforce(
    payload: WorkforceAnalysisRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    """Run capacity analysis, workload analysis, and hiring demand forecasting."""
    return WorkforceService(db).analyze(payload, actor_id=user.id)
