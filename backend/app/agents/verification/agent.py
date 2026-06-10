"""Agent 8 — Reference Verification Agent.

Verifies trustworthiness: employment verification, education verification,
reference analysis, claim validation, and risk detection.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, ReferenceStatus
from app.core.exceptions import NotFoundError
from app.repositories.verification import ReferenceRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T

_RISK_PHRASES = ("would not recommend", "not rehireable", "left abruptly", "performance issues",
                 "could not confirm", "discrepancy", "no record", "terminated")
_POSITIVE_PHRASES = ("highly recommend", "excellent", "would rehire", "top performer",
                     "reliable", "trustworthy", "strong performer", "confirmed")


class ReferenceVerificationAgent(BaseAgent):
    name = AgentName.VERIFICATION
    description = "Verifies references and produces trust and verification scores."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        repo = ReferenceRepository(self.db)
        ref = repo.get(payload["reference_id"]) if payload.get("reference_id") else None
        if not ref:
            raise NotFoundError("Reference check not found")

        response = payload.get("response") or ref.response or ""
        analysis = self._analyze(response, ref.claims_to_validate or [])

        ref.response = response
        ref.employment_verified = analysis["employment_verified"]
        ref.education_verified = analysis["education_verified"]
        ref.verification_score = analysis["verification_score"]
        ref.trust_score = analysis["trust_score"]
        ref.risk_alerts = analysis["risk_alerts"]
        ref.analysis = analysis
        ref.status = ReferenceStatus.FLAGGED if analysis["risk_alerts"] else ReferenceStatus.VERIFIED
        repo.save(ref)

        recommendations = []
        if analysis["risk_alerts"]:
            recommendations.append(
                {
                    "type": "hiring_risk",
                    "title": "Reference risk detected",
                    "rationale": "; ".join(analysis["risk_alerts"]),
                    "confidence": 0.75,
                    "priority": 3,
                    "candidate_id": ref.candidate_id,
                }
            )
        return self._result(
            f"Reference verified — trust score {round(analysis['trust_score'], 1)}.",
            output=analysis,
            recommendations=recommendations,
            score=analysis["trust_score"],
            confidence=0.7,
        )

    def _analyze(self, response: str, claims: list) -> dict:
        low = response.lower()
        risks = [p for p in _RISK_PHRASES if p in low]
        positives = [p for p in _POSITIVE_PHRASES if p in low]

        employment_verified = "confirm" in low or "verified" in low or bool(positives)
        education_verified = "degree" in low or "graduated" in low or "education" in low

        base_trust = 60.0 + len(positives) * 10.0 - len(risks) * 25.0
        trust_score = T.clamp(base_trust)
        verification_score = T.clamp(
            (50.0 if employment_verified else 20.0)
            + (30.0 if education_verified else 10.0)
            + len(positives) * 5.0
        )
        risk_alerts = [f"flagged phrase: '{p}'" for p in risks]
        if not response:
            risk_alerts.append("no reference response on record")

        claim_results = [
            {"claim": c, "validated": str(c).lower() in low} for c in claims
        ]
        return {
            "employment_verified": employment_verified,
            "education_verified": education_verified,
            "verification_score": round(verification_score, 2),
            "trust_score": round(trust_score, 2),
            "risk_alerts": risk_alerts,
            "claim_validation": claim_results,
            "positive_signals": positives,
        }
