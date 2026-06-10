"""Notification endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.repositories.notification import NotificationRepository
from app.schemas.common import Message
from app.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    db: DbSession,
    user: CurrentUser,
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
) -> list[NotificationRead]:
    items = NotificationRepository(db).list_for_user(user.id, unread_only=unread_only, limit=limit)
    return [NotificationRead.model_validate(n) for n in items]


@router.post("/{notification_id}/read", response_model=Message)
def mark_read(notification_id: str, db: DbSession, user: CurrentUser) -> Message:
    repo = NotificationRepository(db)
    notif = repo.get(notification_id)
    if not notif or notif.user_id != user.id:
        raise NotFoundError("Notification not found")
    repo.mark_read(notif)
    db.commit()
    return Message(message="Marked as read")
