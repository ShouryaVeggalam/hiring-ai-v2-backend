"""Job Intelligence endpoints (/job)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.common import Page
from app.schemas.job import JobBlueprintRequest, JobCreate, JobRead, JobUpdate
from app.services.job_service import JobService

router = APIRouter(prefix="/job", tags=["job-intelligence"])


@router.get("/openings", response_model=Page[JobRead])
def list_jobs(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[JobRead]:
    items, total = JobService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[JobRead](
        items=[JobRead.model_validate(j) for j in items],
        total=total, page=page, page_size=page_size,
    )


@router.post(
    "/openings", response_model=JobRead, status_code=201,
    dependencies=[Depends(require_recruiter)],
)
def create_job(payload: JobCreate, db: DbSession, user: CurrentUser) -> JobRead:
    return JobRead.model_validate(JobService(db).create(payload, actor_id=user.id))


@router.get("/openings/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: DbSession) -> JobRead:
    return JobRead.model_validate(JobService(db).get(job_id))


@router.patch(
    "/openings/{job_id}", response_model=JobRead, dependencies=[Depends(require_recruiter)]
)
def update_job(job_id: str, payload: JobUpdate, db: DbSession) -> JobRead:
    return JobRead.model_validate(JobService(db).update(job_id, payload))


@router.delete(
    "/openings/{job_id}", status_code=204, dependencies=[Depends(require_recruiter)]
)
def delete_job(job_id: str, db: DbSession) -> None:
    JobService(db).delete(job_id)


@router.post("/blueprint", response_model=AgentRunResult, dependencies=[Depends(require_recruiter)])
def generate_blueprint(
    payload: JobBlueprintRequest,
    db: DbSession,
    user: CurrentUser,
    persist: bool = Query(True, description="Persist a JobOpening from the blueprint"),
) -> AgentRunResult:
    """Run the Job Intelligence Agent to produce a Job Blueprint."""
    result, _ = JobService(db).generate_blueprint(
        payload, company_id=user.company_id, actor_id=user.id, persist=persist
    )
    return result
