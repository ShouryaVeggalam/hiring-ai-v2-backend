"""Agent 5 — Qualification Agent.

Ranks candidates against a job: job-match analysis, qualification scoring,
candidate ranking, and candidate comparison. Produces a shortlist.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, CandidateStage, RecommendationType
from app.core.exceptions import NotFoundError
from app.engines.matching import MatchingEngine
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository
from app.repositories.job import JobRepository
from app.schemas.agent import AgentRunResult


class QualificationAgent(BaseAgent):
    name = AgentName.QUALIFICATION
    description = "Scores and ranks candidates to produce a shortlist."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        job_repo = JobRepository(self.db)
        cand_repo = CandidateRepository(self.db)
        job = job_repo.get(payload["job_opening_id"]) if payload.get("job_opening_id") else None
        if not job:
            raise NotFoundError("Job opening not found")

        company_values: list[str] = []
        if job.company_id:
            company = CompanyRepository(self.db).get(job.company_id)
            if company and company.culture_values:
                company_values = list(company.culture_values.get("values", []))

        candidate_ids = payload.get("candidate_ids")
        if candidate_ids:
            candidates = [c for c in (cand_repo.get(cid) for cid in candidate_ids) if c]
        else:
            candidates = cand_repo.list_for_job(job.id) or cand_repo.list(limit=200)

        engine = MatchingEngine()
        ranked: list[dict] = []
        for cand in candidates:
            result = engine.match(
                candidate_skills=cand.skills or [],
                required_skills=job.required_skills or [],
                preferred_skills=job.preferred_skills or [],
                candidate_years=cand.years_experience,
                required_years=job.min_experience_years,
                candidate_education=cand.education or [],
                required_education=job.education_requirement,
                company_values=company_values,
            )
            qualification_score = result.match_score
            cand.match_score = result.match_score
            cand.qualification_score = qualification_score
            ranked.append(
                {
                    "candidate_id": cand.id,
                    "full_name": cand.full_name,
                    "qualification_score": round(qualification_score, 2),
                    "match": result.to_dict(),
                }
            )
        self.db.flush()
        ranked.sort(key=lambda r: r["qualification_score"], reverse=True)

        shortlist = [r for r in ranked if r["qualification_score"] >= 65][:10]
        # Promote shortlisted candidates' stage.
        for entry in shortlist:
            cand = cand_repo.get(entry["candidate_id"])
            if cand and cand.stage in {CandidateStage.DISCOVERED, CandidateStage.SCREENING}:
                cand.stage = CandidateStage.QUALIFIED
        self.db.flush()

        recommendations = [
            {
                "type": RecommendationType.SHORTLIST.value,
                "title": f"Shortlist {r['full_name']} for {job.title}",
                "rationale": f"Qualification score {r['qualification_score']}.",
                "confidence": min(0.95, r["qualification_score"] / 100),
                "priority": 2,
                "candidate_id": r["candidate_id"],
                "job_opening_id": job.id,
                "payload": r,
            }
            for r in shortlist[:5]
        ]
        avg = sum(r["qualification_score"] for r in ranked) / len(ranked) if ranked else 0.0
        return self._result(
            f"Ranked {len(ranked)} candidate(s) for {job.title}; "
            f"{len(shortlist)} shortlisted.",
            output={
                "ranking": ranked,
                "shortlist": shortlist,
                "job_opening_id": job.id,
            },
            recommendations=recommendations,
            score=round(avg, 2),
            confidence=0.8,
        )
