"""Candidate / Resume / TalentPool repositories."""
from __future__ import annotations

from sqlalchemy import select

from app.core.constants import CandidateStage
from app.models.candidate import Candidate, Resume, TalentPool
from app.repositories.base import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    model = Candidate

    def list_by_stage(self, stage: CandidateStage, limit: int = 200) -> list[Candidate]:
        return self.list(stage=stage, limit=limit)

    def list_for_job(self, job_opening_id: str, limit: int = 500) -> list[Candidate]:
        return self.list(job_opening_id=job_opening_id, limit=limit)

    def count_by_stage(self, stage: CandidateStage) -> int:
        return self.count(stage=stage)

    def top_by_qualification(self, limit: int = 10) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .where(Candidate.qualification_score.is_not(None))
            .order_by(Candidate.qualification_score.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())


class ResumeRepository(BaseRepository[Resume]):
    model = Resume

    def list_for_candidate(self, candidate_id: str) -> list[Resume]:
        return self.list(candidate_id=candidate_id, limit=100)


class TalentPoolRepository(BaseRepository[TalentPool]):
    model = TalentPool
