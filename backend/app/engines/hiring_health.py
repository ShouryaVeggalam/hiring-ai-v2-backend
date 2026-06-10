"""Hiring Health Engine.

Aggregates pipeline signals into a single Hiring Health Score plus the
supporting KPIs (time-to-hire, interview success rate, offer acceptance
rate, candidate quality, hiring velocity).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.utils import text as T


@dataclass
class HealthMetrics:
    hiring_health_score: float
    time_to_hire_days: float
    interview_success_rate: float
    offer_acceptance_rate: float
    candidate_quality_score: float
    hiring_velocity: float
    breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "hiring_health_score": round(self.hiring_health_score, 2),
            "time_to_hire_days": round(self.time_to_hire_days, 2),
            "interview_success_rate": round(self.interview_success_rate, 2),
            "offer_acceptance_rate": round(self.offer_acceptance_rate, 2),
            "candidate_quality_score": round(self.candidate_quality_score, 2),
            "hiring_velocity": round(self.hiring_velocity, 2),
            "breakdown": self.breakdown,
        }


class HiringHealthEngine:
    """Computes hiring KPIs from already-aggregated counters."""

    def compute(
        self,
        *,
        hires: list[dict] | None = None,
        interviews: list[dict] | None = None,
        offers: list[dict] | None = None,
        candidate_scores: list[float] | None = None,
        hires_last_30d: int = 0,
        open_roles: int = 0,
    ) -> HealthMetrics:
        hires = hires or []
        interviews = interviews or []
        offers = offers or []
        candidate_scores = [s for s in (candidate_scores or []) if s is not None]

        time_to_hire = self._time_to_hire(hires)
        interview_success = self._interview_success(interviews)
        offer_acceptance = self._offer_acceptance(offers)
        quality = sum(candidate_scores) / len(candidate_scores) if candidate_scores else 0.0
        velocity = self._velocity(hires_last_30d, open_roles)

        # Composite health: normalise time-to-hire (lower is better).
        tth_score = T.clamp(100.0 - min(time_to_hire, 90.0) / 90.0 * 100.0)
        health = (
            tth_score * 0.2
            + interview_success * 0.2
            + offer_acceptance * 0.25
            + quality * 0.2
            + min(velocity * 20.0, 100.0) * 0.15
        )

        return HealthMetrics(
            hiring_health_score=T.clamp(health),
            time_to_hire_days=time_to_hire,
            interview_success_rate=interview_success,
            offer_acceptance_rate=offer_acceptance,
            candidate_quality_score=T.clamp(quality),
            hiring_velocity=velocity,
            breakdown={
                "time_to_hire_score": round(tth_score, 2),
                "sample_sizes": {
                    "hires": len(hires),
                    "interviews": len(interviews),
                    "offers": len(offers),
                    "scored_candidates": len(candidate_scores),
                },
            },
        )

    @staticmethod
    def _time_to_hire(hires: list[dict]) -> float:
        durations: list[float] = []
        for h in hires:
            start = h.get("created_at")
            end = h.get("hired_at") or h.get("updated_at")
            if isinstance(start, datetime) and isinstance(end, datetime):
                durations.append(max(0.0, (end - start).total_seconds() / 86400.0))
        return sum(durations) / len(durations) if durations else 0.0

    @staticmethod
    def _interview_success(interviews: list[dict]) -> float:
        if not interviews:
            return 0.0
        positive = sum(
            1 for i in interviews
            if (i.get("recommendation") in {"strong_hire", "hire"})
            or (i.get("interview_score") or 0) >= 70
        )
        return positive / len(interviews) * 100.0

    @staticmethod
    def _offer_acceptance(offers: list[dict]) -> float:
        decided = [o for o in offers if o.get("status") in {"accepted", "declined"}]
        if not decided:
            return 0.0
        accepted = sum(1 for o in decided if o.get("status") == "accepted")
        return accepted / len(decided) * 100.0

    @staticmethod
    def _velocity(hires_last_30d: int, open_roles: int) -> float:
        """Hires per week, lightly contextualised by open demand."""
        base = hires_last_30d / 4.0
        return round(base, 2)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
