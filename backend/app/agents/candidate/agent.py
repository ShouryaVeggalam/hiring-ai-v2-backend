"""Agent 4 — Candidate Intelligence Agent.

Researches candidates: resume analysis, project analysis, career-growth
analysis, skill intelligence, and leadership detection. Produces a
candidate dossier, insights, and a candidate score.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName
from app.core.exceptions import NotFoundError
from app.repositories.candidate import CandidateRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T

_LEADERSHIP_SIGNALS = (
    "lead", "led", "managed", "mentored", "architected", "owned", "founded",
    "spearheaded", "directed", "head of", "principal", "staff",
)


class CandidateIntelligenceAgent(BaseAgent):
    name = AgentName.CANDIDATE
    description = "Builds a candidate dossier with insights and a candidate score."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        candidate_id = payload.get("candidate_id")
        repo = CandidateRepository(self.db)
        cand = repo.get(candidate_id) if candidate_id else None
        if not cand:
            raise NotFoundError("Candidate not found")

        skills = cand.skills or []
        experience = cand.experience or []
        projects = cand.projects or []
        education = cand.education or []

        blob = " ".join(str(e) for e in experience) + " " + (cand.headline or "")
        leadership = self._leadership(blob)
        growth = self._career_growth(cand.years_experience, len(experience))
        skill_intel = self._skill_intelligence(skills)

        candidate_score = T.clamp(
            min(100.0, len(skills) * 6.0) * 0.35
            + min(100.0, cand.years_experience * 10.0) * 0.25
            + growth * 0.2
            + leadership["score"] * 0.2
        )

        dossier = {
            "summary": f"{cand.full_name} — {cand.headline or 'candidate'} with "
            f"{cand.years_experience} yrs experience.",
            "skill_intelligence": skill_intel,
            "career_growth": {"score": growth, "roles": len(experience)},
            "leadership": leadership,
            "project_analysis": self._project_analysis(projects),
            "education": education,
        }
        insights = self._llm_insights(cand, dossier)

        cand.candidate_score = candidate_score
        cand.dossier = dossier
        cand.insights = insights
        repo.save(cand)

        recommendations = []
        if candidate_score >= 75:
            recommendations.append(
                {
                    "type": "shortlist",
                    "title": f"Strong profile: {cand.full_name}",
                    "rationale": f"Candidate score {round(candidate_score, 1)}.",
                    "confidence": 0.8,
                    "priority": 2,
                    "candidate_id": cand.id,
                }
            )
        return self._result(
            f"Dossier built for {cand.full_name} (score {round(candidate_score, 1)}).",
            output={"dossier": dossier, "insights": insights, "candidate_id": cand.id},
            recommendations=recommendations,
            score=candidate_score,
            confidence=0.72,
        )

    @staticmethod
    def _leadership(text: str) -> dict:
        low = text.lower()
        hits = [s for s in _LEADERSHIP_SIGNALS if s in low]
        score = T.clamp(len(hits) * 18.0)
        return {"detected": bool(hits), "signals": hits, "score": score}

    @staticmethod
    def _career_growth(years: float, role_count: int) -> float:
        if role_count == 0:
            return 40.0
        avg_tenure = years / role_count if role_count else years
        # Reward progression without excessive job-hopping.
        if avg_tenure < 1.0:
            return 50.0
        if avg_tenure > 5.0:
            return 70.0
        return T.clamp(60.0 + role_count * 5.0)

    @staticmethod
    def _skill_intelligence(skills: list[str]) -> dict:
        return {
            "total_skills": len(skills),
            "depth": "high" if len(skills) >= 10 else "medium" if len(skills) >= 5 else "low",
            "top_skills": skills[:8],
        }

    @staticmethod
    def _project_analysis(projects: list) -> dict:
        return {"count": len(projects), "highlights": [str(p) for p in projects[:5]]}

    def _llm_insights(self, cand: Any, dossier: dict) -> dict:
        out = self.llm.complete_json(
            system=(
                "You are a talent analyst. Given a candidate dossier, return JSON with keys: "
                "strengths (array), concerns (array), summary (string)."
            ),
            user=f"Candidate: {cand.full_name}\nDossier: {dossier}",
            default={},
        )
        if out.get("_offline"):
            return {
                "strengths": dossier["skill_intelligence"]["top_skills"][:3],
                "concerns": [] if dossier["leadership"]["detected"] else ["limited leadership signal"],
                "summary": dossier["summary"],
            }
        return out
