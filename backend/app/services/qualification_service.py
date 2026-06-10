"""Qualification service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName
from app.schemas.agent import AgentRunResult
from app.services.common import log_activity, persist_recommendations, run_agent


class QualificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def qualify(
        self, job_opening_id: str, candidate_ids: list[str] | None = None,
        *, company_id: str | None = None, actor_id: str | None = None,
    ) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.QUALIFICATION,
            {"job_opening_id": job_opening_id, "candidate_ids": candidate_ids},
            company_id=company_id,
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result, company_id=company_id)
        log_activity(
            self.db, "qualification_run", description=result.summary,
            entity_type="job", entity_id=job_opening_id, company_id=company_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
