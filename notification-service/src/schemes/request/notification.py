from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.enums.channel import Channel
from src.enums.notification_type import NotificationType


class SendNotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Request schema for manual notification sending (admin mass mailing)."""

    user_ids: list[UUID] | None = Field(
        default=None,
        description="Recipient user ids.",
        examples=[["019f0000-0000-7000-8000-000000000010"]],
    )
    role: str | None = Field(
        default=None, description="Recipient role, as an alternative to user_ids."
    )
    subject: str = Field(
        description="Notification subject.", examples=["Order shipped"]
    )
    body: str = Field(
        description="Notification body.", examples=["Your order has been shipped."]
    )
    channel: Channel = Field(
        default=Channel.email, description="Delivery channel.", examples=["email"]
    )
    notification_type: NotificationType = Field(
        default=NotificationType.info,
        description="Notification category.",
        examples=["info"],
    )
