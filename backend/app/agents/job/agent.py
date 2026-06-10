"""Agent 2 — Job Intelligence Agent.

Creates hiring requirements: JD generation, skill extraction, salary
benchmarking, role analysis, and interview plan creation.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, SeniorityLevel
from app.utils import text as T
from app.schemas.agent import AgentRunResult

# Rough multipliers applied to a base salary band per seniority.
_SENIORITY_MULTIPLIER = {
    SeniorityLevel.INTERN: 0.4,
    SeniorityLevel.JUNIOR: 0.7,
    SeniorityLevel.MID: 1.0,
    SeniorityLevel.SENIOR: 1.4,
    SeniorityLevel.LEAD: 1.7,
    SeniorityLevel.PRINCIPAL: 2.1,
    SeniorityLevel.EXECUTIVE: 3.0,
}

_BASE_BAND = (90000, 130000)  # USD mid-level reference band


class JobIntelligenceAgent(BaseAgent):
    name = AgentName.JOB
    description = "Generates the Job Blueprint, skill requirements, and hiring strategy."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        title = payload.get("title", "Software Engineer")
        seniority = self._coerce_seniority(payload.get("seniority"))
        must_have = [s.lower() for s in payload.get("must_have_skills", [])]
        context = payload.get("context") or ""

        extracted = T.extract_skills(f"{title} {context} {' '.join(must_have)}")
        required_skills = sorted(set(must_have) | set(extracted[:8]))
        preferred_skills = [s for s in extracted if s not in required_skills][:6]

        salary = self._salary_benchmark(seniority)
        interview_plan = self._interview_plan(seniority)
        blueprint = self._blueprint(title, seniority, required_skills, context)

        output = {
            "job_blueprint": blueprint,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "responsibilities": blueprint.get("responsibilities", []),
            "salary_benchmark": salary,
            "interview_plan": interview_plan,
            "hiring_strategy": self._strategy(seniority, required_skills),
            "seniority": seniority.value,
        }
        recommendations = [
            {
                "type": "shortlist",
                "title": f"Source candidates with: {', '.join(required_skills[:4])}",
                "rationale": "Core skills derived for the role blueprint.",
                "confidence": 0.7,
                "priority": 1,
                "payload": {"skills": required_skills},
            }
        ]
        return self._result(
            f"Job blueprint generated for {title} ({seniority.value}).",
            output=output,
            recommendations=recommendations,
            score=80.0,
            confidence=0.78,
        )

    @staticmethod
    def _coerce_seniority(value: Any) -> SeniorityLevel:
        if isinstance(value, SeniorityLevel):
            return value
        try:
            return SeniorityLevel(str(value))
        except ValueError:
            return SeniorityLevel.MID

    def _salary_benchmark(self, seniority: SeniorityLevel) -> dict:
        mult = _SENIORITY_MULTIPLIER[seniority]
        low = int(_BASE_BAND[0] * mult)
        high = int(_BASE_BAND[1] * mult)
        return {
            "currency": "USD",
            "min": low,
            "max": high,
            "median": (low + high) // 2,
            "methodology": "seniority-adjusted reference band",
        }

    @staticmethod
    def _interview_plan(seniority: SeniorityLevel) -> dict:
        stages = ["screening", "technical", "behavioral"]
        if seniority in {SeniorityLevel.SENIOR, SeniorityLevel.LEAD,
                         SeniorityLevel.PRINCIPAL, SeniorityLevel.EXECUTIVE}:
            stages += ["system_design", "final"]
        return {
            "stages": stages,
            "total_rounds": len(stages),
            "estimated_days": len(stages) * 3,
        }

    def _blueprint(self, title: str, seniority: SeniorityLevel, skills: list[str], context: str) -> dict:
        default = {
            "title": title,
            "summary": f"{seniority.value.title()} {title} responsible for delivering high-impact work.",
            "responsibilities": [
                f"Own and deliver {title} initiatives end to end.",
                "Collaborate cross-functionally with product and design.",
                "Uphold engineering quality, testing, and documentation standards.",
            ],
            "required_skills": skills,
        }
        llm_out = self.llm.complete_json(
            system=(
                "You are an expert technical recruiter. Produce a JSON job blueprint with keys: "
                "summary (string), responsibilities (string array of 4-6 items)."
            ),
            user=f"Role: {title}\nSeniority: {seniority.value}\nContext: {context}\nSkills: {skills}",
            default={},
        )
        if llm_out and not llm_out.get("_offline"):
            default.update({k: v for k, v in llm_out.items() if k in {"summary", "responsibilities"}})
        return default

    @staticmethod
    def _strategy(seniority: SeniorityLevel, skills: list[str]) -> dict:
        channels = ["referrals", "inbound applications", "talent pool"]
        if seniority in {SeniorityLevel.SENIOR, SeniorityLevel.LEAD,
                         SeniorityLevel.PRINCIPAL, SeniorityLevel.EXECUTIVE}:
            channels = ["executive search", "targeted outreach", *channels]
        return {
            "sourcing_channels": channels,
            "priority_skills": skills[:5],
            "expected_difficulty": "high" if seniority in {
                SeniorityLevel.PRINCIPAL, SeniorityLevel.EXECUTIVE
            } else "medium",
        }
