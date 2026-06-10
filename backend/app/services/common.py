"""Shared service helpers: agent execution, recommendation + activity persistence."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import AgentContext
from app.agents.registry import get_agent
from app.core.constants import AgentName, NotificationType, RecommendationType
from app.repositories.activity import ActivityRepository
from app.repositories.notification import NotificationRepository
from app.repositories.recommendation import RecommendationRepository
from app.schemas.agent import AgentRunResult


def run_agent(
    db: Session,
    name: AgentName,
    payload: dict[str, Any],
    *,
    company_id: str | None = None,
    actor_id: str | None = None,
) -> AgentRunResult:
    """Instantiate and execute an agent within a fresh context."""
    ctx = AgentContext(db=db, company_id=company_id, actor_id=actor_id)
    agent = get_agent(name, ctx)
    return agent.execute(payload)


def persist_recommendations(
    db: Session,
    result: AgentRunResult,
    *,
    company_id: str | None = None,
) -> int:
    """Persist an agent's recommendations into the recommendations table."""
    repo = RecommendationRepository(db)
    created = 0
    for rec in result.recommendations:
        try:
            rec_type = RecommendationType(rec.get("type", "shortlist"))
        except ValueError:
            rec_type = RecommendationType.SHORTLIST
        repo.create(
            recommendation_type=rec_type,
            source_agent=result.agent,
            title=rec.get("title", "Recommendation"),
            rationale=rec.get("rationale"),
            confidence=rec.get("confidence"),
            priority=int(rec.get("priority", 0)),
            payload=rec.get("payload", {}),
            company_id=rec.get("company_id") or company_id,
            candidate_id=rec.get("candidate_id"),
            job_opening_id=rec.get("job_opening_id"),
        )
        created += 1
    return created


def log_activity(
    db: Session,
    action: str,
    *,
    description: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    company_id: str | None = None,
    meta: dict | None = None,
) -> None:
    ActivityRepository(db).log(
        action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        company_id=company_id,
        meta=meta,
    )


def notify(
    db: Session,
    *,
    notification_type: NotificationType,
    title: str,
    message: str | None = None,
    user_id: str | None = None,
    company_id: str | None = None,
    payload: dict | None = None,
) -> None:
    NotificationRepository(db).create(
        notification_type=notification_type,
        title=title,
        message=message,
        user_id=user_id,
        company_id=company_id,
        payload=payload or {},
    )
