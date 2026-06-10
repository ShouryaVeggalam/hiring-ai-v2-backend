"""Interview repository."""
from __future__ import annotations

from sqlalchemy import select

from app.core.constants import InterviewStatus
from app.models.interview import Interview
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    model = Interview

    def list_for_candidate(self, candidate_id: str) -> list[Interview]:
        return self.list(candidate_id=candidate_id, limit=200)

    def count_active(self) -> int:
        stmt = select(Interview).where(
            Interview.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.IN_PROGRESS])
        )
        return len(list(self.db.execute(stmt).scalars().all()))

    def list_completed(self, limit: int = 500) -> list[Interview]:
        return self.list(status=InterviewStatus.COMPLETED, limit=limit)
