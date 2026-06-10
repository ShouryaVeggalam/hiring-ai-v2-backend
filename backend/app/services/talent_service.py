"""Talent discovery service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName
from app.schemas.agent import AgentRunResult
from app.schemas.candidate import TalentDiscoveryRequest
from app.services.common import log_activity, persist_recommendations, run_agent


class TalentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def discover(
        self, req: TalentDiscoveryRequest, *, company_id: str | None = None,
        actor_id: str | None = None,
    ) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.TALENT,
            {
                "job_opening_id": req.job_opening_id,
                "query": req.query,
                "skills": req.skills,
                "location": req.location,
                "limit": req.limit,
            },
            company_id=company_id,
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result, company_id=company_id)
        log_activity(
            self.db, "talent_discovery", description=result.summary,
            company_id=company_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
