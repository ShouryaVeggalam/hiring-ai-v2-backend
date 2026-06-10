"""Reference Verification Agent endpoints (/verification)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_recruiter
from app.schemas.agent import AgentRunResult
from app.schemas.common import Page
from app.schemas.verification import ReferenceCreate, ReferenceRead, ReferenceSubmit
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/verification", tags=["reference-verification"])


@router.get("", response_model=Page[ReferenceRead])
def list_references(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[ReferenceRead]:
    items, total = VerificationService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[ReferenceRead](
        items=[ReferenceRead.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=ReferenceRead, status_code=201, dependencies=[Depends(require_recruiter)])
def create_reference(payload: ReferenceCreate, db: DbSession, user: CurrentUser) -> ReferenceRead:
    return ReferenceRead.model_validate(VerificationService(db).create(payload, actor_id=user.id))


@router.get("/{reference_id}", response_model=ReferenceRead)
def get_reference(reference_id: str, db: DbSession) -> ReferenceRead:
    return ReferenceRead.model_validate(VerificationService(db).get(reference_id))


@router.post(
    "/{reference_id}/verify", response_model=AgentRunResult,
    dependencies=[Depends(require_recruiter)],
)
def verify_reference(
    reference_id: str,
    db: DbSession,
    user: CurrentUser,
    payload: ReferenceSubmit | None = None,
) -> AgentRunResult:
    return VerificationService(db).verify(
        reference_id, response=payload.response if payload else None, actor_id=user.id
    )
