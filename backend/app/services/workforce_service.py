"""Workforce planning service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName
from app.schemas.agent import AgentRunResult, WorkforceAnalysisRequest
from app.services.common import log_activity, persist_recommendations, run_agent


class WorkforceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyze(self, req: WorkforceAnalysisRequest, actor_id: str | None = None) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.WORKFORCE,
            {
                "company_id": req.company_id,
                "horizon_months": req.horizon_months,
                "context": req.context,
            },
            company_id=req.company_id,
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result, company_id=req.company_id)
        log_activity(
            self.db,
            "workforce_analysis",
            description=result.summary,
            company_id=req.company_id,
            actor_id=actor_id,
        )
        self.db.commit()
        return result
