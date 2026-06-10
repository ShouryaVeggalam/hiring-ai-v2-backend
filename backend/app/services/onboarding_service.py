"""Onboarding service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName, NotificationType
from app.core.exceptions import NotFoundError
from app.models.onboarding import Onboarding
from app.repositories.onboarding import OnboardingRepository
from app.schemas.agent import AgentRunResult
from app.services.common import log_activity, notify, run_agent


class OnboardingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OnboardingRepository(db)

    def get(self, onboarding_id: str) -> Onboarding:
        ob = self.repo.get(onboarding_id)
        if not ob:
            raise NotFoundError("Onboarding not found")
        return ob

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[Onboarding], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def run(
        self, candidate_id: str, *, offer_id: str | None = None,
        completed_items: list[str] | None = None, actor_id: str | None = None,
    ) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.ONBOARDING,
            {
                "candidate_id": candidate_id,
                "offer_id": offer_id,
                "completed_items": completed_items or [],
            },
            actor_id=actor_id,
        )
        notify(
            self.db, notification_type=NotificationType.ONBOARDING_ALERT,
            title="Onboarding update", message=result.summary,
            payload={"candidate_id": candidate_id},
        )
        log_activity(
            self.db, "onboarding_update", description=result.summary,
            entity_type="candidate", entity_id=candidate_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
