"""Assessment service: CRUD + Assessment Agent."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.constants import AgentName, AssessmentStatus
from app.core.exceptions import NotFoundError
from app.models.assessment import Assessment
from app.repositories.assessment import AssessmentRepository
from app.schemas.agent import AgentRunResult
from app.schemas.assessment import AssessmentCreate
from app.services.common import log_activity, persist_recommendations, run_agent


class AssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AssessmentRepository(db)

    def create(self, data: AssessmentCreate, actor_id: str | None = None) -> Assessment:
        assessment = self.repo.create(data.model_dump())
        log_activity(
            self.db, "assessment_created", entity_type="assessment", entity_id=assessment.id,
            actor_id=actor_id,
        )
        self.db.commit()
        return assessment

    def get(self, assessment_id: str) -> Assessment:
        assessment = self.repo.get(assessment_id)
        if not assessment:
            raise NotFoundError("Assessment not found")
        return assessment

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[Assessment], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def submit(self, assessment_id: str, submission: str) -> Assessment:
        assessment = self.get(assessment_id)
        assessment.submission = submission
        assessment.status = AssessmentStatus.SUBMITTED
        assessment.submitted_at = datetime.now(timezone.utc)
        self.repo.save(assessment)
        self.db.commit()
        return assessment

    def evaluate(
        self, assessment_id: str, submission: str | None = None, actor_id: str | None = None,
    ) -> AgentRunResult:
        self.get(assessment_id)
        result = run_agent(
            self.db,
            AgentName.ASSESSMENT,
            {"assessment_id": assessment_id, "submission": submission},
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result)
        log_activity(
            self.db, "assessment_evaluated", description=result.summary,
            entity_type="assessment", entity_id=assessment_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
