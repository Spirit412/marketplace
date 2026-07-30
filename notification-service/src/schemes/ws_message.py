from datetime import datetime

from pydantic import BaseModel


class WSMessage(BaseModel):
    """Structure of a WebSocket-delivered notification message."""

    type: str
    title: str
    body: str
    notification_type: str = "info"
    timestamp: datetime
