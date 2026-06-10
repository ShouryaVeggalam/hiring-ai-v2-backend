"""Hiring Chief service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName, NotificationType
from app.schemas.agent import AgentRunResult
from app.services.common import log_activity, notify, persist_recommendations, run_agent


class ChiefService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def report(self, company_id: str | None = None, actor_id: str | None = None) -> AgentRunResult:
        result = run_agent(
            self.db, AgentName.CHIEF, {"company_id": company_id},
            company_id=company_id, actor_id=actor_id,
        )
        persist_recommendations(self.db, result, company_id=company_id)
        notify(
            self.db, notification_type=NotificationType.EXECUTIVE_ALERT,
            title="Executive hiring briefing", message=result.summary, company_id=company_id,
        )
        log_activity(
            self.db, "chief_report", description=result.summary,
            company_id=company_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
