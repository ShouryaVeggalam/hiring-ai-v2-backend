"""Agent 3 — Talent Discovery Agent.

Finds candidates: talent-pool search, candidate discovery, candidate
matching, and recommendations. Produces a ranked talent pipeline.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName
from app.engines.matching import MatchingEngine
from app.repositories.candidate import CandidateRepository
from app.repositories.job import JobRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T


class TalentDiscoveryAgent(BaseAgent):
    name = AgentName.TALENT
    description = "Discovers and ranks candidates into a talent pipeline."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        cand_repo = CandidateRepository(self.db)
        job_repo = JobRepository(self.db)
        limit = int(payload.get("limit", 20))
        query_skills = {s.lower() for s in payload.get("skills", [])}

        required_skills: list[str] = []
        job = None
        if payload.get("job_opening_id"):
            job = job_repo.get(payload["job_opening_id"])
            if job:
                required_skills = list(job.required_skills or [])
                query_skills |= {s.lower() for s in required_skills}

        if payload.get("query"):
            query_skills |= set(T.extract_skills(payload["query"]))

        candidates = cand_repo.list(limit=500)
        engine = MatchingEngine()
        ranked: list[dict] = []
        for cand in candidates:
            cand_skills = {s.lower() for s in (cand.skills or [])}
            overlap = T.coverage(query_skills, cand_skills) * 100 if query_skills else 50.0
            recency = 60.0  # placeholder freshness signal
            discovery_score = T.clamp(overlap * 0.7 + recency * 0.3)
            cand.discovery_score = discovery_score
            ranked.append(
                {
                    "candidate_id": cand.id,
                    "full_name": cand.full_name,
                    "discovery_score": round(discovery_score, 2),
                    "matched_skills": sorted(query_skills & cand_skills),
                    "stage": cand.stage.value,
                }
            )
        self.db.flush()
        ranked.sort(key=lambda r: r["discovery_score"], reverse=True)
        pipeline = ranked[:limit]

        recommendations = [
            {
                "type": "shortlist",
                "title": f"Add {c['full_name']} to pipeline",
                "rationale": f"Discovery score {c['discovery_score']}.",
                "confidence": min(0.95, c["discovery_score"] / 100),
                "priority": 1,
                "candidate_id": c["candidate_id"],
                "payload": c,
            }
            for c in pipeline[:5]
        ]
        avg = sum(c["discovery_score"] for c in pipeline) / len(pipeline) if pipeline else 0.0
        return self._result(
            f"Discovered {len(pipeline)} candidate(s) for the talent pipeline.",
            output={
                "talent_pipeline": pipeline,
                "candidate_count": len(pipeline),
                "query_skills": sorted(query_skills),
                "job_opening_id": payload.get("job_opening_id"),
            },
            recommendations=recommendations,
            score=round(avg, 2),
            confidence=0.7,
        )
