"""Reporting engine endpoints (/reports)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_manager
from app.core.exceptions import NotFoundError
from app.schemas.common import Page
from app.schemas.report import ReportGenerateRequest, ReportRead
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=Page[ReportRead])
def list_reports(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[ReportRead]:
    items, total = ReportService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[ReportRead](
        items=[ReportRead.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: str, db: DbSession) -> ReportRead:
    report = ReportService(db).get(report_id)
    if not report:
        raise NotFoundError("Report not found")
    return ReportRead.model_validate(report)


@router.post("/generate", response_model=ReportRead, dependencies=[Depends(require_manager)])
def generate_report(
    payload: ReportGenerateRequest, db: DbSession, user: CurrentUser
) -> ReportRead:
    report = ReportService(db).generate(payload, actor_id=user.id)
    return ReportRead.model_validate(report)
