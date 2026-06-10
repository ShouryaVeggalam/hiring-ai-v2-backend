"""Assessment Agent endpoints (/assessment)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.assessment import AssessmentCreate, AssessmentRead, AssessmentSubmit
from app.schemas.common import Page
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.get("", response_model=Page[AssessmentRead])
def list_assessments(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[AssessmentRead]:
    items, total = AssessmentService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[AssessmentRead](
        items=[AssessmentRead.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=AssessmentRead, status_code=201, dependencies=[Depends(require_recruiter)])
def create_assessment(payload: AssessmentCreate, db: DbSession, user: CurrentUser) -> AssessmentRead:
    return AssessmentRead.model_validate(AssessmentService(db).create(payload, actor_id=user.id))


@router.get("/{assessment_id}", response_model=AssessmentRead)
def get_assessment(assessment_id: str, db: DbSession) -> AssessmentRead:
    return AssessmentRead.model_validate(AssessmentService(db).get(assessment_id))


@router.post("/{assessment_id}/submit", response_model=AssessmentRead)
def submit_assessment(
    assessment_id: str, payload: AssessmentSubmit, db: DbSession
) -> AssessmentRead:
    return AssessmentRead.model_validate(AssessmentService(db).submit(assessment_id, payload.submission))


@router.post(
    "/{assessment_id}/evaluate", response_model=AgentRunResult,
    dependencies=[Depends(require_recruiter)],
)
def evaluate_assessment(
    assessment_id: str, db: DbSession, user: CurrentUser,
    payload: AssessmentSubmit | None = None,
) -> AgentRunResult:
    return AssessmentService(db).evaluate(
        assessment_id,
        submission=payload.submission if payload else None,
        actor_id=user.id,
    )
