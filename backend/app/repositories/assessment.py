"""Assessment repository."""
from __future__ import annotations

from app.models.assessment import Assessment
from app.repositories.base import BaseRepository


class AssessmentRepository(BaseRepository[Assessment]):
    model = Assessment

    def list_for_candidate(self, candidate_id: str) -> list[Assessment]:
        return self.list(candidate_id=candidate_id, limit=200)
