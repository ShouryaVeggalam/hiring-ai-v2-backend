"""Onboarding repository."""
from __future__ import annotations

from app.models.onboarding import Onboarding
from app.repositories.base import BaseRepository


class OnboardingRepository(BaseRepository[Onboarding]):
    model = Onboarding

    def get_for_candidate(self, candidate_id: str) -> Onboarding | None:
        return self.get_by(candidate_id=candidate_id)
