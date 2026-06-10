"""Notification repository."""
from __future__ import annotations

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def list_for_user(self, user_id: str, unread_only: bool = False, limit: int = 100) -> list[Notification]:
        filters: dict = {"user_id": user_id}
        if unread_only:
            filters["is_read"] = False
        return self.list(limit=limit, **filters)

    def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        return self.save(notification)
