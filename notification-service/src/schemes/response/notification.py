from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Response schema for notification API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    channel: str
    notification_type: str
    subject: str
    body: str
    status: Literal["unread", "read"]
    created_at: datetime
    read_at: datetime | None = None
