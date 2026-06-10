"""Notification schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.constants import NotificationChannel, NotificationType
from app.schemas.common import TimestampedSchema


class NotificationRead(TimestampedSchema):
    notification_type: NotificationType
    channel: NotificationChannel
    title: str
    message: str | None = None
    is_read: bool
    payload: dict | None = None
    user_id: str | None = None
    company_id: str | None = None


class NotificationCreate(BaseModel):
    notification_type: NotificationType
    title: str
    message: str | None = None
    channel: NotificationChannel = NotificationChannel.IN_APP
    payload: dict = Field(default_factory=dict)
    user_id: str | None = None
    company_id: str | None = None
