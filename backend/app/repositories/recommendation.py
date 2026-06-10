"""Hiring recommendation repository."""
from __future__ import annotations

from sqlalchemy import select

from app.models.recommendation import HiringRecommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[HiringRecommendation]):
    model = HiringRecommendation

    def top(self, company_id: str | None = None, limit: int = 10) -> list[HiringRecommendation]:
        stmt = select(HiringRecommendation).where(
            HiringRecommendation.is_acted_on.is_(False)
        )
        if company_id:
            stmt = stmt.where(HiringRecommendation.company_id == company_id)
        stmt = stmt.order_by(
            HiringRecommendation.priority.desc(),
            HiringRecommendation.created_at.desc(),
        ).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
