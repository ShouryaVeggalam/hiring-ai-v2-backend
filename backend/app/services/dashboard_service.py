"""Dashboard aggregation service — powers the single /dashboard endpoint."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import CandidateStage, InterviewStatus, OfferStatus
from app.engines.hiring_health import HiringHealthEngine
from app.repositories.activity import ActivityRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.offer import OfferRepository
from app.repositories.recommendation import RecommendationRepository
from app.schemas.dashboard import (
    ActivityItem,
    DashboardResponse,
    HiringHealth,
)
from app.schemas.recommendation import RecommendationRead


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, company_id: str | None = None) -> DashboardResponse:
        jobs = JobRepository(self.db)
        cands = CandidateRepository(self.db)
        interviews = InterviewRepository(self.db)
        offers = OfferRepository(self.db)
        recs = RecommendationRepository(self.db)
        acts = ActivityRepository(self.db)

        all_candidates = cands.list(limit=5000)
        all_offers = offers.list(limit=5000)
        all_interviews = interviews.list(limit=5000)

        open_roles = jobs.count_open(company_id)
        candidates_discovered = len(all_candidates)
        candidates_qualified = sum(
            1 for c in all_candidates
            if c.stage in {CandidateStage.QUALIFIED, CandidateStage.INTERVIEWING,
                           CandidateStage.ASSESSMENT, CandidateStage.OFFER}
        )
        interviews_active = interviews.count_active()
        offers_sent = sum(1 for o in all_offers if o.status == OfferStatus.SENT)

        health = self._health(all_candidates, all_interviews, all_offers, open_roles)

        top_recs = [RecommendationRead.model_validate(r) for r in recs.top(company_id, limit=10)]
        recent = [
            ActivityItem(
                id=a.id,
                action=a.action,
                description=a.description,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                created_at=a.created_at.isoformat(),
            )
            for a in acts.recent(company_id, limit=20)
        ]

        return DashboardResponse(
            open_roles=open_roles,
            candidates_discovered=candidates_discovered,
            candidates_qualified=candidates_qualified,
            interviews_active=interviews_active,
            offers_sent=offers_sent,
            hiring_velocity=health.hiring_velocity,
            hiring_health_score=health.hiring_health_score,
            candidate_quality_score=health.candidate_quality_score,
            top_recommendations=top_recs,
            recent_activity=recent,
            health=HiringHealth(**health.to_dict()),
        )

    def _health(self, candidates, interviews, offers, open_roles):
        engine = HiringHealthEngine()
        hires = [
            {"created_at": c.created_at, "hired_at": c.updated_at}
            for c in candidates
            if c.stage in {CandidateStage.HIRED, CandidateStage.ONBOARDING}
        ]
        interview_dicts = [
            {
                "recommendation": i.recommendation.value if i.recommendation else None,
                "interview_score": i.interview_score,
            }
            for i in interviews if i.status == InterviewStatus.COMPLETED
        ]
        offer_dicts = [{"status": o.status.value} for o in offers]
        scores = [c.qualification_score for c in candidates if c.qualification_score is not None]
        return engine.compute(
            hires=hires,
            interviews=interview_dicts,
            offers=offer_dicts,
            candidate_scores=scores,
            hires_last_30d=len(hires),
            open_roles=open_roles,
        )
