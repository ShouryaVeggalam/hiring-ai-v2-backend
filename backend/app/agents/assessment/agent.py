"""Agent 7 — Assessment Agent.

Evaluates skills: coding assessment evaluation, assignment evaluation,
case-study evaluation, and assessment analytics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, AssessmentStatus, AssessmentType
from app.core.exceptions import NotFoundError
from app.repositories.assessment import AssessmentRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T

_QUALITY_SIGNALS = ("test", "tests", "edge case", "complexity", "readme", "documentation",
                    "modular", "clean", "efficient", "scalable", "error handling")


class AssessmentAgent(BaseAgent):
    name = AgentName.ASSESSMENT
    description = "Evaluates coding, assignment, and case-study submissions."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        repo = AssessmentRepository(self.db)
        assessment = repo.get(payload["assessment_id"]) if payload.get("assessment_id") else None
        if not assessment:
            raise NotFoundError("Assessment not found")

        submission = payload.get("submission") or assessment.submission or ""
        evaluation = self._evaluate(assessment.assessment_type, submission)

        assessment.submission = submission
        assessment.score = evaluation["score"]
        assessment.skill_breakdown = evaluation["skill_breakdown"]
        assessment.risk_areas = evaluation["risk_areas"]
        assessment.analytics = evaluation["analytics"]
        assessment.status = AssessmentStatus.EVALUATED
        assessment.submitted_at = assessment.submitted_at or datetime.now(timezone.utc)
        repo.save(assessment)

        recommendations = []
        if evaluation["score"] >= 75:
            recommendations.append(
                {
                    "type": "shortlist",
                    "title": f"Strong assessment ({round(evaluation['score'], 1)})",
                    "rationale": "Candidate demonstrated strong skills.",
                    "confidence": 0.8,
                    "priority": 2,
                    "candidate_id": assessment.candidate_id,
                }
            )
        return self._result(
            f"Assessment evaluated — score {round(evaluation['score'], 1)}/100.",
            output=evaluation,
            recommendations=recommendations,
            score=evaluation["score"],
            confidence=0.7,
        )

    def _evaluate(self, atype: AssessmentType, submission: str) -> dict:
        low = submission.lower()
        signals = [s for s in _QUALITY_SIGNALS if s in low]
        length_score = T.clamp(min(100.0, len(submission) / 20.0))
        quality_score = T.clamp(len(signals) * 12.0)
        base = length_score * 0.4 + quality_score * 0.6

        llm = self.llm.complete_json(
            system=(
                "You are a senior engineer grading a candidate submission. Return JSON with keys: "
                "score (0-100 number), skill_breakdown (object), risk_areas (string array), "
                "rationale (string)."
            ),
            user=f"Assessment type: {atype.value}\nSubmission:\n{submission[:6000]}",
            default={},
        )
        if not llm.get("_offline") and isinstance(llm.get("score"), (int, float)):
            score = T.clamp(float(llm["score"]))
            return {
                "score": round(score, 2),
                "skill_breakdown": llm.get("skill_breakdown", {}),
                "risk_areas": llm.get("risk_areas", []),
                "analytics": {"rationale": llm.get("rationale", ""), "signals": signals},
            }
        return {
            "score": round(base, 2),
            "skill_breakdown": {
                "correctness": round(quality_score, 1),
                "completeness": round(length_score, 1),
                "best_practices": round(min(100.0, len(signals) * 15.0), 1),
            },
            "risk_areas": [] if "test" in low else ["no tests detected"],
            "analytics": {"quality_signals": signals, "submission_length": len(submission)},
        }
