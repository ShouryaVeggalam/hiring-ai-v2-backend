"""Reference verification repository."""
from __future__ import annotations

from app.models.verification import ReferenceCheck
from app.repositories.base import BaseRepository


class ReferenceRepository(BaseRepository[ReferenceCheck]):
    model = ReferenceCheck

    def list_for_candidate(self, candidate_id: str) -> list[ReferenceCheck]:
        return self.list(candidate_id=candidate_id, limit=200)
