from typing import Any
from uuid import UUID

from pydantic import BaseModel


class NotificationPayload(BaseModel):
    """Pydantic schema for events arriving from RabbitMQ."""

    event_type: str
    user_id: UUID
    locale: str = "ru"
    variables: dict[str, Any] = {}
    metadata: dict[str, Any] | None = None
