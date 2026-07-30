import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for notification API endpoints."""

    uuid: uuid.UUID
    event_type: str
    channel: str
    notification_type: str
    subject: str
    body: str
    status: Literal["unread", "read"]
    created_at: datetime
    read_at: datetime | None = None
