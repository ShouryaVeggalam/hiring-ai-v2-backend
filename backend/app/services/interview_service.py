"""Interview service: CRUD + Interview Intelligence Agent."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName, NotificationType
from app.core.exceptions import NotFoundError
from app.models.interview import Interview
from app.repositories.interview import InterviewRepository
from app.schemas.agent import AgentRunResult
from app.schemas.interview import InterviewCreate, InterviewPlanRequest, InterviewUpdate
from app.services.common import log_activity, notify, persist_recommendations, run_agent


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InterviewRepository(db)

    def create(self, data: InterviewCreate, actor_id: str | None = None) -> Interview:
        interview = self.repo.create(data.model_dump())
        notify(
            self.db, notification_type=NotificationType.INTERVIEW_ALERT,
            title="Interview scheduled",
            message=f"{interview.interview_type.value} interview created.",
            payload={"interview_id": interview.id},
        )
        log_activity(
            self.db, "interview_created", entity_type="interview", entity_id=interview.id,
            actor_id=actor_id,
        )
        self.db.commit()
        return interview

    def get(self, interview_id: str) -> Interview:
        interview = self.repo.get(interview_id)
        if not interview:
            raise NotFoundError("Interview not found")
        return interview

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[Interview], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def update(self, interview_id: str, data: InterviewUpdate) -> Interview:
        interview = self.get(interview_id)
        interview = self.repo.update(interview, data.model_dump(exclude_unset=True))
        self.db.commit()
        return interview

    def generate_plan(self, req: InterviewPlanRequest, actor_id: str | None = None) -> AgentRunResult:
        result = run_agent(
            self.db,
            AgentName.INTERVIEW,
            {
                "action": "plan",
                "candidate_id": req.candidate_id,
                "job_opening_id": req.job_opening_id,
                "interview_type": req.interview_type.value,
                "focus_areas": req.focus_areas,
            },
            actor_id=actor_id,
        )
        self.db.commit()
        return result

    def analyze_transcript(
        self, interview_id: str, transcript: str | None = None, actor_id: str | None = None,
    ) -> AgentRunResult:
        self.get(interview_id)
        result = run_agent(
            self.db,
            AgentName.INTERVIEW,
            {"action": "analyze", "interview_id": interview_id, "transcript": transcript},
            actor_id=actor_id,
        )
        persist_recommendations(self.db, result)
        log_activity(
            self.db, "interview_analyzed", description=result.summary,
            entity_type="interview", entity_id=interview_id, actor_id=actor_id,
        )
        self.db.commit()
        return result
