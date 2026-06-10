"""Reference verification service: CRUD + Verification Agent."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName
from app.core.exceptions import NotFoundError
from app.models.verification import ReferenceCheck
from app.repositories.verification import ReferenceRepository
from app.schemas.agent import AgentRunResult
from app.schemas.verification import ReferenceCreate
from app.services.common import log_activity, persist_recommendations, run_agent


class VerificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReferenceRepository(db)

    def create(self, data: ReferenceCreate, actor_id: str | None = None) -> ReferenceCheck:
        ref = self.repo.create(data.model_dump())
        log_activity(
            self.db, "reference_created", entity_type="reference", entity_id=ref.id,
            actor_id=actor_id,
        )
        self.db.commit()
        return ref

    def get(self, reference_id: str) -> ReferenceCheck:
        ref = self.repo.get(reference_id)
        if not ref:
            raise NotFoundError("Reference check not found")
        return ref

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[ReferenceCheck], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def verify(
        self, reference_id: str, response: str | None = None, actor_id: str | None = None,
    ) -> AgentRunResult:
        self.get(reference_id)
        result = run_agent(
            self.db,
            AgentName.VERIFICATION,
            {"reference_id": reference_id, "response": response},
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result)
        log_activity(
            self.db, "reference_verified", description=result.summary,
            entity_type="reference", entity_id=reference_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
