"""Candidate ↔ Job Matching Engine.

Computes a weighted match score from skill, experience, education, and
culture sub-scores. Fully deterministic so it works without an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.utils import text as T


@dataclass
class MatchResult:
    match_score: float
    skill_match: float
    experience_match: float
    education_match: float
    culture_match: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "match_score": round(self.match_score, 2),
            "skill_match": round(self.skill_match, 2),
            "experience_match": round(self.experience_match, 2),
            "education_match": round(self.education_match, 2),
            "culture_match": round(self.culture_match, 2),
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "breakdown": self.breakdown,
        }


# Education ranking for comparison.
_EDU_RANK = {
    "high school": 1, "diploma": 2, "associate": 2,
    "bachelor": 3, "b.tech": 3, "b.sc": 3, "be": 3,
    "master": 4, "m.tech": 4, "m.sc": 4, "mba": 4,
    "phd": 5, "doctorate": 5,
}


class MatchingEngine:
    """Weighted matching between a candidate and a job."""

    WEIGHTS = {
        "skill": 0.45,
        "experience": 0.25,
        "education": 0.15,
        "culture": 0.15,
    }

    def match(
        self,
        *,
        candidate_skills: list[str],
        required_skills: list[str],
        preferred_skills: list[str] | None = None,
        candidate_years: float = 0.0,
        required_years: float = 0.0,
        candidate_education: list[dict] | None = None,
        required_education: str | None = None,
        candidate_culture: list[str] | None = None,
        company_values: list[str] | None = None,
    ) -> MatchResult:
        cand = {s.lower() for s in candidate_skills}
        req = {s.lower() for s in required_skills}
        pref = {s.lower() for s in (preferred_skills or [])}

        skill_match = self._skill_score(cand, req, pref)
        experience_match = self._experience_score(candidate_years, required_years)
        education_match = self._education_score(candidate_education or [], required_education)
        culture_match = self._culture_score(candidate_culture or [], company_values or [])

        total = (
            skill_match * self.WEIGHTS["skill"]
            + experience_match * self.WEIGHTS["experience"]
            + education_match * self.WEIGHTS["education"]
            + culture_match * self.WEIGHTS["culture"]
        )

        matched = sorted(cand & (req | pref))
        missing = sorted(req - cand)

        return MatchResult(
            match_score=T.clamp(total),
            skill_match=skill_match,
            experience_match=experience_match,
            education_match=education_match,
            culture_match=culture_match,
            matched_skills=matched,
            missing_skills=missing,
            breakdown={
                "weights": self.WEIGHTS,
                "required_skill_count": len(req),
                "candidate_skill_count": len(cand),
            },
        )

    @staticmethod
    def _skill_score(cand: set[str], req: set[str], pref: set[str]) -> float:
        if not req and not pref:
            return 70.0  # neutral when no requirements specified
        required_cov = T.coverage(req, cand)
        preferred_cov = T.coverage(pref, cand) if pref else 0.0
        score = required_cov * 85.0 + preferred_cov * 15.0
        return T.clamp(score)

    @staticmethod
    def _experience_score(candidate_years: float, required_years: float) -> float:
        if required_years <= 0:
            return 75.0
        ratio = candidate_years / required_years
        if ratio >= 1.0:
            # Slightly penalise heavy over-qualification.
            return T.clamp(100.0 - max(0.0, (ratio - 1.5)) * 10.0)
        return T.clamp(ratio * 100.0)

    @staticmethod
    def _education_score(candidate_education: list[dict], required_education: str | None) -> float:
        if not required_education:
            return 75.0
        req_rank = next(
            (r for key, r in _EDU_RANK.items() if key in required_education.lower()), 3
        )
        cand_rank = 0
        for edu in candidate_education:
            blob = " ".join(str(v) for v in edu.values()).lower()
            for key, r in _EDU_RANK.items():
                if key in blob:
                    cand_rank = max(cand_rank, r)
        if cand_rank == 0:
            return 40.0
        return T.clamp(min(1.0, cand_rank / req_rank) * 100.0)

    @staticmethod
    def _culture_score(candidate_culture: list[str], company_values: list[str]) -> float:
        if not company_values:
            return 70.0
        a = {c.lower() for c in candidate_culture}
        b = {c.lower() for c in company_values}
        return T.clamp(50.0 + T.jaccard(a, b) * 50.0)
