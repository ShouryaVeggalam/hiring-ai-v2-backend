"""Activity log repository."""
from __future__ import annotations

from app.models.activity import ActivityLog
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[ActivityLog]):
    model = ActivityLog

    def recent(self, company_id: str | None = None, limit: int = 20) -> list[ActivityLog]:
        filters = {"company_id": company_id} if company_id else {}
        return self.list(limit=limit, **filters)

    def log(
        self,
        action: str,
        *,
        description: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor_id: str | None = None,
        company_id: str | None = None,
        meta: dict | None = None,
    ) -> ActivityLog:
        return self.create(
            action=action,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            company_id=company_id,
            meta=meta or {},
        )
