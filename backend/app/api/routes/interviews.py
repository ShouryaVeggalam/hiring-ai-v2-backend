"""Interview Intelligence Agent endpoints (/interview)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.common import Page
from app.schemas.interview import (
    InterviewCreate,
    InterviewPlanRequest,
    InterviewRead,
    InterviewUpdate,
    TranscriptAnalysisRequest,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview-intelligence"])


@router.get("", response_model=Page[InterviewRead])
def list_interviews(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[InterviewRead]:
    items, total = InterviewService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[InterviewRead](
        items=[InterviewRead.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=InterviewRead, status_code=201, dependencies=[Depends(require_recruiter)])
def create_interview(payload: InterviewCreate, db: DbSession, user: CurrentUser) -> InterviewRead:
    return InterviewRead.model_validate(InterviewService(db).create(payload, actor_id=user.id))


@router.get("/{interview_id}", response_model=InterviewRead)
def get_interview(interview_id: str, db: DbSession) -> InterviewRead:
    return InterviewRead.model_validate(InterviewService(db).get(interview_id))


@router.patch(
    "/{interview_id}", response_model=InterviewRead, dependencies=[Depends(require_recruiter)]
)
def update_interview(
    interview_id: str, payload: InterviewUpdate, db: DbSession
) -> InterviewRead:
    return InterviewRead.model_validate(InterviewService(db).update(interview_id, payload))


@router.post("/plan", response_model=AgentRunResult, dependencies=[Depends(require_recruiter)])
def generate_plan(
    payload: InterviewPlanRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    return InterviewService(db).generate_plan(payload, actor_id=user.id)


@router.post(
    "/{interview_id}/analyze", response_model=AgentRunResult,
    dependencies=[Depends(require_recruiter)],
)
def analyze_transcript(
    interview_id: str,
    payload: TranscriptAnalysisRequest,
    db: DbSession,
    user: CurrentUser,
) -> AgentRunResult:
    return InterviewService(db).analyze_transcript(
        interview_id, transcript=payload.transcript, actor_id=user.id
    )
