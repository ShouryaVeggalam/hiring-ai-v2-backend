"""Aggregate all API routers under the versioned prefix."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    assessments,
    auth,
    candidates,
    chief,
    companies,
    dashboard,
    health,
    interviews,
    jobs,
    notifications,
    offers,
    onboarding,
    qualification,
    reports,
    talent,
    users,
    verification,
    websocket,
    workforce,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(workforce.router)
api_router.include_router(jobs.router)
api_router.include_router(talent.router)
api_router.include_router(candidates.router)
api_router.include_router(qualification.router)
api_router.include_router(interviews.router)
api_router.include_router(assessments.router)
api_router.include_router(verification.router)
api_router.include_router(offers.router)
api_router.include_router(onboarding.router)
api_router.include_router(chief.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(websocket.router)
