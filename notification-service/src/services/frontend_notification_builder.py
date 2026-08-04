from datetime import UTC, datetime

from src.schemes.ws_message import WSMessage


class FrontendNotificationBuilder:
    """Fluent builder for WebSocket notification messages."""

    def __init__(self) -> None:
        self._event_type: str = ""
        self._notification_type: str = "info"
        self._title: str = ""
        self._body: str = ""

    def with_event_type(self, event_type: str) -> "FrontendNotificationBuilder":
        self._event_type = event_type
        return self

    def with_notification_type(self, ntype: str) -> "FrontendNotificationBuilder":
        self._notification_type = ntype
        return self

    def with_title(self, title: str) -> "FrontendNotificationBuilder":
        self._title = title
        return self

    def with_body(self, body: str) -> "FrontendNotificationBuilder":
        self._body = body
        return self

    def build(self) -> WSMessage:
        return WSMessage(
            type=self._event_type,
            title=self._title,
            body=self._body,
            notification_type=self._notification_type,
            timestamp=datetime.now(UTC),
        )
