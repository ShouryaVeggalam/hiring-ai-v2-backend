"""Reporting engine service — generates hiring/candidate/executive reports."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import ReportType
from app.models.report import HiringReport
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import CandidateRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.offer import OfferRepository
from app.repositories.report import ReportRepository
from app.schemas.report import ReportGenerateRequest
from app.services.chief_service import ChiefService
from app.services.dashboard_service import DashboardService


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReportRepository(db)

    def get(self, report_id: str) -> HiringReport | None:
        return self.repo.get(report_id)

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[HiringReport], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def generate(self, req: ReportGenerateRequest, actor_id: str | None = None) -> HiringReport:
        builder = {
            ReportType.HIRING: self._hiring,
            ReportType.CANDIDATE: self._candidate,
            ReportType.INTERVIEW: self._interview,
            ReportType.ASSESSMENT: self._assessment,
            ReportType.OFFER: self._offer,
            ReportType.EXECUTIVE: self._executive,
            ReportType.TALENT_INTELLIGENCE: self._talent_intelligence,
        }.get(req.report_type, self._hiring)

        title, summary, content = builder(req.company_id)
        report = self.repo.create(
            report_type=req.report_type,
            title=title,
            summary=summary,
            content=content,
            period_start=req.period_start,
            period_end=req.period_end,
            generated_by=actor_id or "system",
            company_id=req.company_id,
        )
        self.db.commit()
        return report

    # ---- builders ----
    def _hiring(self, company_id):
        dash = DashboardService(self.db).build(company_id)
        return (
            "Hiring Report",
            f"Hiring health {dash.hiring_health_score}/100 across {dash.open_roles} open roles.",
            dash.model_dump(),
        )

    def _candidate(self, company_id):
        repo = CandidateRepository(self.db)
        candidates = repo.list(limit=5000)
        stages: dict[str, int] = {}
        for c in candidates:
            stages[c.stage.value] = stages.get(c.stage.value, 0) + 1
        top = [
            {"name": c.full_name, "qualification_score": c.qualification_score}
            for c in repo.top_by_qualification(10)
        ]
        return (
            "Candidate Report",
            f"{len(candidates)} candidates across {len(stages)} stages.",
            {"total": len(candidates), "by_stage": stages, "top_candidates": top},
        )

    def _interview(self, company_id):
        repo = InterviewRepository(self.db)
        interviews = repo.list(limit=5000)
        completed = [i for i in interviews if i.interview_score is not None]
        avg = sum(i.interview_score for i in completed) / len(completed) if completed else 0
        return (
            "Interview Report",
            f"{len(interviews)} interviews; average score {round(avg, 1)}.",
            {"total": len(interviews), "completed": len(completed), "avg_score": round(avg, 2)},
        )

    def _assessment(self, company_id):
        repo = AssessmentRepository(self.db)
        items = repo.list(limit=5000)
        scored = [a for a in items if a.score is not None]
        avg = sum(a.score for a in scored) / len(scored) if scored else 0
        return (
            "Assessment Report",
            f"{len(items)} assessments; average score {round(avg, 1)}.",
            {"total": len(items), "evaluated": len(scored), "avg_score": round(avg, 2)},
        )

    def _offer(self, company_id):
        repo = OfferRepository(self.db)
        offers = repo.list(limit=5000)
        by_status: dict[str, int] = {}
        for o in offers:
            by_status[o.status.value] = by_status.get(o.status.value, 0) + 1
        return (
            "Offer Report",
            f"{len(offers)} offers tracked.",
            {"total": len(offers), "by_status": by_status},
        )

    def _executive(self, company_id):
        result = ChiefService(self.db).report(company_id)
        return ("Executive Report", result.summary, result.output)

    def _talent_intelligence(self, company_id):
        repo = CandidateRepository(self.db)
        candidates = repo.list(limit=5000)
        skill_freq: dict[str, int] = {}
        for c in candidates:
            for s in c.skills or []:
                skill_freq[s] = skill_freq.get(s, 0) + 1
        top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        return (
            "Talent Intelligence Report",
            f"Talent market across {len(candidates)} candidates.",
            {"talent_pool_size": len(candidates), "top_skills": top_skills},
        )
