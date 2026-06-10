"""Offer repository."""
from __future__ import annotations

from app.core.constants import OfferStatus
from app.models.offer import Offer
from app.repositories.base import BaseRepository


class OfferRepository(BaseRepository[Offer]):
    model = Offer

    def list_for_candidate(self, candidate_id: str) -> list[Offer]:
        return self.list(candidate_id=candidate_id, limit=200)

    def count_sent(self) -> int:
        return self.count(status=OfferStatus.SENT)

    def list_by_status(self, status: OfferStatus, limit: int = 500) -> list[Offer]:
        return self.list(status=status, limit=limit)
