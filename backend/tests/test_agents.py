"""Unit tests for the agent network."""
from __future__ import annotations

from app.agents.base import AgentContext
from app.agents.candidate import CandidateIntelligenceAgent
from app.agents.job import JobIntelligenceAgent
from app.agents.qualification import QualificationAgent
from app.agents.workforce import WorkforcePlanningAgent
from app.core.constants import JobStatus, SeniorityLevel
from app.models.candidate import Candidate
from app.models.company import Company, Department
from app.models.job import JobOpening
from app.repositories.candidate import CandidateRepository
from app.repositories.company import CompanyRepository, DepartmentRepository
from app.repositories.job import JobRepository


class TestWorkforceAgent:
    def test_capacity_analysis(self, db_session):
        company = CompanyRepository(db_session).create(name="Acme Corp")
        DepartmentRepository(db_session).create(
            name="Engineering", company_id=company.id, headcount=8, target_headcount=12
        )
        DepartmentRepository(db_session).create(
            name="Sales", company_id=company.id, headcount=5, target_headcount=5
        )
        db_session.commit()

        ctx = AgentContext(db=db_session, company_id=company.id)
        result = WorkforcePlanningAgent(ctx).execute(
            {"company_id": company.id, "horizon_months": 6}
        )
        assert result.success
        assert result.output["total_headcount_gap"] == 4
        assert len(result.output["priority_roles"]) >= 1


class TestJobAgent:
    def test_blueprint_generation(self, db_session):
        ctx = AgentContext(db=db_session)
        result = JobIntelligenceAgent(ctx).execute(
            {
                "title": "Backend Engineer",
                "seniority": SeniorityLevel.SENIOR.value,
                "must_have_skills": ["python", "fastapi"],
            }
        )
        assert result.success
        assert "python" in result.output["required_skills"]
        assert result.output["salary_benchmark"]["min"] > 0
        assert result.output["interview_plan"]["stages"]


class TestQualificationAgent:
    def test_candidate_ranking(self, db_session):
        job = JobRepository(db_session).create(
            title="Python Developer",
            status=JobStatus.OPEN,
            required_skills=["python", "fastapi"],
            min_experience_years=3.0,
        )
        CandidateRepository(db_session).create(
            full_name="Alice Strong",
            skills=["python", "fastapi", "postgresql"],
            years_experience=5.0,
            job_opening_id=job.id,
        )
        CandidateRepository(db_session).create(
            full_name="Bob Weak",
            skills=["java"],
            years_experience=1.0,
            job_opening_id=job.id,
        )
        db_session.commit()

        ctx = AgentContext(db=db_session)
        result = QualificationAgent(ctx).execute({"job_opening_id": job.id})
        assert result.success
        ranking = result.output["ranking"]
        assert ranking[0]["full_name"] == "Alice Strong"
        assert ranking[0]["qualification_score"] > ranking[1]["qualification_score"]
        assert len(result.output["shortlist"]) >= 1


class TestCandidateAgent:
    def test_dossier_build(self, db_session):
        cand = CandidateRepository(db_session).create(
            full_name="Carol Expert",
            skills=["python", "leadership", "architecture"],
            years_experience=10.0,
            experience=[{"title": "Principal Engineer at BigCo"}],
            headline="Principal Engineer",
        )
        db_session.commit()

        ctx = AgentContext(db=db_session)
        result = CandidateIntelligenceAgent(ctx).execute({"candidate_id": cand.id})
        assert result.success
        assert result.score is not None
        assert result.output["dossier"]["leadership"]["detected"] is True
