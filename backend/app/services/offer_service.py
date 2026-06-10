"""Offer service: generation, status tracking, CRUD."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName, CandidateStage, NotificationType, OfferStatus
from app.core.exceptions import NotFoundError
from app.models.offer import Offer
from app.repositories.candidate import CandidateRepository
from app.repositories.offer import OfferRepository
from app.schemas.agent import AgentRunResult
from app.schemas.offer import OfferGenerateRequest, OfferUpdate
from app.services.common import log_activity, notify, persist_recommendations, run_agent


class OfferService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OfferRepository(db)

    def get(self, offer_id: str) -> Offer:
        offer = self.repo.get(offer_id)
        if not offer:
            raise NotFoundError("Offer not found")
        return offer

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[Offer], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def generate(
        self, req: OfferGenerateRequest, *, company_id: str | None = None,
        actor_id: str | None = None,
    ) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.OFFER,
            {
                "candidate_id": req.candidate_id,
                "job_opening_id": req.job_opening_id,
                "target_base_salary": req.target_base_salary,
            },
            company_id=company_id,
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result, company_id=company_id)
        notify(
            self.db, notification_type=NotificationType.OFFER_ALERT,
            title="Offer drafted", message=result.summary, company_id=company_id,
            payload=result.output,
        )
        log_activity(
            self.db, "offer_generated", description=result.summary,
            entity_type="candidate", entity_id=req.candidate_id,
            company_id=company_id, actor_id=actor_id,
        )
        self.db.commit()
        return result

    def update_status(self, offer_id: str, data: OfferUpdate) -> Offer:
        offer = self.get(offer_id)
        offer = self.repo.update(offer, data.model_dump(exclude_unset=True))
        # Move candidate forward on acceptance.
        if data.status == OfferStatus.ACCEPTED:
            cand = CandidateRepository(self.db).get(offer.candidate_id)
            if cand:
                cand.stage = CandidateStage.OFFER
        self.db.commit()
        return offer
