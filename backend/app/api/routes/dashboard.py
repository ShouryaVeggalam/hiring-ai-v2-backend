"""Dashboard aggregation endpoint (/dashboard)."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: DbSession,
    user: CurrentUser,
    company_id: str | None = Query(default=None),
) -> DashboardResponse:
    """Single endpoint returning all hiring KPIs and activity."""
    return DashboardService(db).build(company_id or user.company_id)
