"""Agent 11 — Hiring Chief Agent (AI Head of Talent).

Consumes signals from every other agent and answers leadership questions:
who to hire, what risks exist, which roles are critical, where the
bottlenecks are, and what leadership should focus on.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import (
    AgentName,
    CandidateStage,
    InterviewStatus,
    OfferStatus,
)
from app.engines.hiring_health import HiringHealthEngine
from app.repositories.candidate import CandidateRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.offer import OfferRepository
from app.repositories.recommendation import RecommendationRepository
from app.schemas.agent import AgentRunResult


class HiringChiefAgent(BaseAgent):
    name = AgentName.CHIEF
    description = "AI Head of Talent: executive summary, health score, and forecast."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        company_id = payload.get("company_id") or self.ctx.company_id
        job_repo = JobRepository(self.db)
        cand_repo = CandidateRepository(self.db)
        interview_repo = InterviewRepository(self.db)
        offer_repo = OfferRepository(self.db)
        rec_repo = RecommendationRepository(self.db)

        open_roles = job_repo.count_open(company_id)
        candidates = cand_repo.list(limit=2000)
        interviews = interview_repo.list(limit=2000)
        offers = offer_repo.list(limit=2000)

        health = self._health(candidates, interviews, offers, open_roles)
        bottlenecks = self._bottlenecks(candidates, interviews)
        critical_roles = [
            {"job_id": j.id, "title": j.title, "priority": j.priority.value}
            for j in job_repo.list_open(company_id)
            if j.priority.value in {"high", "critical"}
        ]
        top_candidates = [
            {
                "candidate_id": c.id,
                "full_name": c.full_name,
                "qualification_score": c.qualification_score,
                "stage": c.stage.value,
            }
            for c in cand_repo.top_by_qualification(limit=5)
        ]
        risks = self._risks(health, bottlenecks, offers)
        existing_recs = rec_repo.top(company_id, limit=10)

        executive_summary = self._executive_summary(
            health, open_roles, critical_roles, bottlenecks, top_candidates
        )
        forecast = {
            "projected_hires_next_30d": round(health.hiring_velocity * 4, 1),
            "open_roles": open_roles,
            "pipeline_strength": "strong" if len(candidates) > open_roles * 5 else "thin",
        }

        recommendations = [
            {
                "type": "hire",
                "title": f"Advance {c['full_name']}",
                "rationale": f"Top qualified candidate (score {c['qualification_score']}).",
                "confidence": 0.85,
                "priority": 3,
                "candidate_id": c["candidate_id"],
            }
            for c in top_candidates[:3]
        ]
        recommendations += [
            {
                "type": "hiring_risk",
                "title": r["title"],
                "rationale": r["detail"],
                "confidence": 0.7,
                "priority": 3,
            }
            for r in risks
        ]

        return self._result(
            executive_summary,
            output={
                "executive_summary": executive_summary,
                "hiring_health_score": health.hiring_health_score,
                "health": health.to_dict(),
                "critical_roles": critical_roles,
                "bottlenecks": bottlenecks,
                "top_candidates": top_candidates,
                "hiring_risks": risks,
                "hiring_forecast": forecast,
                "open_recommendations": [
                    {"title": r.title, "type": r.recommendation_type.value} for r in existing_recs
                ],
                "answers": self._answers(
                    top_candidates, risks, critical_roles, bottlenecks
                ),
            },
            recommendations=recommendations,
            score=health.hiring_health_score,
            confidence=0.8,
        )

    def _health(self, candidates, interviews, offers, open_roles) -> Any:
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
            for i in interviews
            if i.status == InterviewStatus.COMPLETED
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

    @staticmethod
    def _bottlenecks(candidates, interviews) -> list[dict]:
        stage_counts: dict[str, int] = {}
        for c in candidates:
            stage_counts[c.stage.value] = stage_counts.get(c.stage.value, 0) + 1
        bottlenecks = []
        # A bottleneck = a stage holding a disproportionate share of candidates.
        total = sum(stage_counts.values()) or 1
        for stage, count in stage_counts.items():
            if stage in {CandidateStage.HIRED.value, CandidateStage.REJECTED.value}:
                continue
            share = count / total
            if share >= 0.4 and count >= 3:
                bottlenecks.append(
                    {"stage": stage, "candidates": count, "share": round(share, 2)}
                )
        return bottlenecks

    @staticmethod
    def _risks(health, bottlenecks, offers) -> list[dict]:
        risks: list[dict] = []
        if health.offer_acceptance_rate < 50 and offers:
            risks.append(
                {
                    "title": "Low offer acceptance",
                    "detail": f"Acceptance rate at {health.offer_acceptance_rate}%.",
                }
            )
        if health.time_to_hire_days > 45:
            risks.append(
                {
                    "title": "Slow time-to-hire",
                    "detail": f"Average time-to-hire is {health.time_to_hire_days} days.",
                }
            )
        for b in bottlenecks:
            risks.append(
                {
                    "title": f"Pipeline bottleneck at {b['stage']}",
                    "detail": f"{b['candidates']} candidates stuck ({int(b['share'] * 100)}%).",
                }
            )
        return risks

    def _executive_summary(self, health, open_roles, critical_roles, bottlenecks, top_candidates) -> str:
        default = (
            f"Hiring health is {health.hiring_health_score}/100 across {open_roles} open role(s). "
            f"{len(critical_roles)} role(s) are critical, {len(bottlenecks)} bottleneck(s) detected, "
            f"and {len(top_candidates)} top candidate(s) are ready to advance."
        )
        out = self.llm.complete(
            system="You are the AI Head of Talent. Write a concise 2-3 sentence executive summary.",
            user=(
                f"Health: {health.to_dict()}\nOpen roles: {open_roles}\n"
                f"Critical roles: {critical_roles}\nBottlenecks: {bottlenecks}\n"
                f"Top candidates: {top_candidates}"
            ),
        )
        return default if out.startswith("[offline-llm]") else out

    @staticmethod
    def _answers(top_candidates, risks, critical_roles, bottlenecks) -> dict:
        return {
            "who_should_we_hire": [c["full_name"] for c in top_candidates[:3]],
            "what_hiring_risks_exist": [r["title"] for r in risks],
            "what_roles_are_critical": [r["title"] for r in critical_roles],
            "where_are_bottlenecks": [b["stage"] for b in bottlenecks],
            "leadership_focus": (
                [r["title"] for r in risks][:2]
                or ["Advance top candidates and keep pipeline flowing"]
            ),
        }
