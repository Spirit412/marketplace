
import uuid

from pydantic import BaseModel, ConfigDict

from src.enums.channel import Channel
from src.enums.notification_type import NotificationType


class SendNotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Request schema for manual notification sending (admin mass mailing)."""

    user_uuids: list[uuid.UUID] | None = None
    role: str | None = None
    subject: str
    body: str
    channel: Channel = Channel.email
    notification_type: NotificationType = NotificationType.info
