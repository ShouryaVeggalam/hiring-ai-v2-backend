"""Job opening repository."""
from __future__ import annotations

from sqlalchemy import select

from app.core.constants import JobStatus
from app.models.job import JobOpening
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[JobOpening]):
    model = JobOpening

    def list_open(self, company_id: str | None = None, limit: int = 200) -> list[JobOpening]:
        stmt = select(JobOpening).where(JobOpening.status == JobStatus.OPEN)
        if company_id:
            stmt = stmt.where(JobOpening.company_id == company_id)
        stmt = stmt.order_by(JobOpening.priority.desc(), JobOpening.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_open(self, company_id: str | None = None) -> int:
        filters: dict = {"status": JobStatus.OPEN}
        if company_id:
            filters["company_id"] = company_id
        return self.count(**filters)
