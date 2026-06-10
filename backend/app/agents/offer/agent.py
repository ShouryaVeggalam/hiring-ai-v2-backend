"""Agent 9 — Offer Agent.

Generates offers: offer generation, compensation analysis, offer tracking,
negotiation support, and acceptance-probability prediction.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, OfferStatus
from app.core.exceptions import NotFoundError
from app.repositories.candidate import CandidateRepository
from app.repositories.job import JobRepository
from app.repositories.offer import OfferRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T


class OfferAgent(BaseAgent):
    name = AgentName.OFFER
    description = "Generates competitive offers with acceptance-probability prediction."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        cand_repo = CandidateRepository(self.db)
        job_repo = JobRepository(self.db)
        offer_repo = OfferRepository(self.db)

        cand = cand_repo.get(payload["candidate_id"]) if payload.get("candidate_id") else None
        if not cand:
            raise NotFoundError("Candidate not found")
        job = job_repo.get(payload["job_opening_id"]) if payload.get("job_opening_id") else None

        comp = self._compensation(job, cand, payload.get("target_base_salary"))
        acceptance = self._acceptance_probability(cand, comp)
        offer_score = self._offer_score(comp, acceptance)

        package = {
            "base_salary": comp["base_salary"],
            "bonus": comp["bonus"],
            "equity": comp["equity"],
            "currency": comp["currency"],
            "total_comp": comp["base_salary"] + comp["bonus"],
        }

        offer = offer_repo.create(
            candidate_id=cand.id,
            job_opening_id=job.id if job else None,
            title=job.title if job else (cand.headline or "Offer"),
            base_salary=comp["base_salary"],
            bonus=comp["bonus"],
            equity=comp["equity"],
            currency=comp["currency"],
            status=OfferStatus.DRAFT,
            offer_package=package,
            compensation_analysis=comp,
            offer_score=offer_score,
            acceptance_probability=acceptance,
        )

        recommendations = [
            {
                "type": "hire",
                "title": f"Offer drafted for {cand.full_name}",
                "rationale": f"Acceptance probability {round(acceptance * 100, 1)}%.",
                "confidence": acceptance,
                "priority": 2,
                "candidate_id": cand.id,
                "job_opening_id": job.id if job else None,
                "payload": {"offer_id": offer.id},
            }
        ]
        return self._result(
            f"Offer drafted for {cand.full_name} — "
            f"{round(acceptance * 100, 1)}% acceptance probability.",
            output={
                "offer_id": offer.id,
                "offer_package": package,
                "compensation_analysis": comp,
                "offer_score": offer_score,
                "acceptance_probability": acceptance,
            },
            recommendations=recommendations,
            score=offer_score,
            confidence=0.72,
        )

    def _compensation(self, job: Any, cand: Any, target: int | None) -> dict:
        if job and job.salary_benchmark:
            median = job.salary_benchmark.get("median")
        else:
            median = None
        if target:
            base = target
        elif median:
            base = median
        elif job and job.salary_max:
            base = (job.salary_min or job.salary_max) // 1
        else:
            base = 120000
        # Experience premium.
        base = int(base * (1 + min(0.2, cand.years_experience * 0.02)))
        bonus = int(base * 0.12)
        equity = "0.05%-0.15%" if (job and job.seniority and job.seniority.value in {
            "senior", "lead", "principal", "executive"
        }) else "0.01%-0.05%"
        return {
            "base_salary": base,
            "bonus": bonus,
            "equity": equity,
            "currency": "USD",
            "benchmark_median": median,
            "methodology": "benchmark + experience premium",
        }

    @staticmethod
    def _acceptance_probability(cand: Any, comp: dict) -> float:
        median = comp.get("benchmark_median")
        prob = 0.6
        if median:
            ratio = comp["base_salary"] / median
            prob = T.clamp(50.0 + (ratio - 1.0) * 120.0, 5.0, 95.0) / 100.0
        # Higher-quality candidates have more competing offers (slightly lower prob).
        if (cand.qualification_score or 0) >= 85:
            prob *= 0.9
        return round(prob, 3)

    @staticmethod
    def _offer_score(comp: dict, acceptance: float) -> float:
        return round(T.clamp(acceptance * 100.0 * 0.7 + 30.0), 2)
