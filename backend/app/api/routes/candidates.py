"""Candidate Intelligence + Resume Processing endpoints (/candidate)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.repositories.candidate import ResumeRepository
from app.schemas.agent import AgentRunResult
from app.schemas.candidate import (
    CandidateCreate,
    CandidateRead,
    CandidateUpdate,
    ResumeRead,
)
from app.schemas.common import Page
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidate", tags=["candidate-intelligence"])


@router.get("", response_model=Page[CandidateRead])
def list_candidates(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[CandidateRead]:
    items, total = CandidateService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[CandidateRead](
        items=[CandidateRead.model_validate(c) for c in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=CandidateRead, status_code=201, dependencies=[Depends(require_recruiter)])
def create_candidate(payload: CandidateCreate, db: DbSession, user: CurrentUser) -> CandidateRead:
    return CandidateRead.model_validate(CandidateService(db).create(payload, actor_id=user.id))


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: str, db: DbSession) -> CandidateRead:
    return CandidateRead.model_validate(CandidateService(db).get(candidate_id))


@router.patch(
    "/{candidate_id}", response_model=CandidateRead, dependencies=[Depends(require_recruiter)]
)
def update_candidate(
    candidate_id: str, payload: CandidateUpdate, db: DbSession
) -> CandidateRead:
    return CandidateRead.model_validate(CandidateService(db).update(candidate_id, payload))


@router.post(
    "/resume", response_model=CandidateRead, status_code=201,
    dependencies=[Depends(require_recruiter)],
)
async def upload_resume(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    candidate_id: str | None = Form(default=None),
    job_opening_id: str | None = Form(default=None),
) -> CandidateRead:
    """Upload and parse a resume (PDF / DOCX / TXT) into a candidate profile."""
    content = await file.read()
    cand, _resume = CandidateService(db).upload_resume(
        content=content,
        filename=file.filename or "resume.txt",
        candidate_id=candidate_id,
        job_opening_id=job_opening_id,
        actor_id=user.id,
    )
    return CandidateRead.model_validate(cand)


@router.get("/{candidate_id}/resumes", response_model=list[ResumeRead])
def list_resumes(candidate_id: str, db: DbSession) -> list[ResumeRead]:
    items = ResumeRepository(db).list_for_candidate(candidate_id)
    return [ResumeRead.model_validate(r) for r in items]


@router.post(
    "/{candidate_id}/analyze", response_model=AgentRunResult,
    dependencies=[Depends(require_recruiter)],
)
def analyze_candidate(candidate_id: str, db: DbSession, user: CurrentUser) -> AgentRunResult:
    """Run the Candidate Intelligence Agent to build a dossier."""
    return CandidateService(db).analyze(candidate_id, actor_id=user.id)
