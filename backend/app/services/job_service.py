"""Job opening service (CRUD + Job Intelligence Agent)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName, JobStatus
from app.core.exceptions import NotFoundError
from app.models.job import JobOpening
from app.repositories.job import JobRepository
from app.schemas.agent import AgentRunResult
from app.schemas.job import JobBlueprintRequest, JobCreate, JobUpdate
from app.services.common import log_activity, persist_recommendations, run_agent


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = JobRepository(db)

    def create(self, data: JobCreate, actor_id: str | None = None) -> JobOpening:
        job = self.repo.create(data.model_dump())
        log_activity(
            self.db, "job_created", description=f"Job '{job.title}' created",
            entity_type="job", entity_id=job.id, actor_id=actor_id, company_id=job.company_id,
        )
        self.db.commit()
        return job

    def get(self, job_id: str) -> JobOpening:
        job = self.repo.get(job_id)
        if not job:
            raise NotFoundError("Job opening not found")
        return job

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[JobOpening], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def update(self, job_id: str, data: JobUpdate) -> JobOpening:
        job = self.get(job_id)
        job = self.repo.update(job, data.model_dump(exclude_unset=True))
        self.db.commit()
        return job

    def delete(self, job_id: str) -> None:
        job = self.get(job_id)
        self.repo.delete(job)
        self.db.commit()

    def generate_blueprint(
        self, req: JobBlueprintRequest, *, company_id: str | None = None,
        department_id: str | None = None, actor_id: str | None = None, persist: bool = True,
    ) -> tuple[AgentRunResult, JobOpening | None]:
        result = run_agent(
            self.db,
            AgentName.JOB,
            {
                "title": req.title,
                "seniority": req.seniority.value,
                "context": req.context,
                "must_have_skills": req.must_have_skills,
            },
            company_id=company_id,
            actor_id=actor_id,
        )
        job: JobOpening | None = None
        if persist:
            out = result.output
            salary = out.get("salary_benchmark", {})
            job = self.repo.create(
                title=req.title,
                seniority=req.seniority,
                status=JobStatus.OPEN,
                company_id=company_id,
                department_id=department_id,
                hiring_manager_id=actor_id,
                location=req.location,
                required_skills=out.get("required_skills", []),
                preferred_skills=out.get("preferred_skills", []),
                responsibilities=out.get("responsibilities", []),
                job_blueprint=out.get("job_blueprint", {}),
                hiring_strategy=out.get("hiring_strategy", {}),
                interview_plan=out.get("interview_plan", {}),
                salary_benchmark=salary,
                salary_min=salary.get("min"),
                salary_max=salary.get("max"),
            )
            persist_recommendations(self.db, result, company_id=company_id)
            log_activity(
                self.db, "job_blueprint_generated", description=result.summary,
                entity_type="job", entity_id=job.id, actor_id=actor_id, company_id=company_id,
            )
        self.db.commit()
        return result, job
