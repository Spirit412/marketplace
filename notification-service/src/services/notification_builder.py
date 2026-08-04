from datetime import UTC, datetime
from uuid import UUID

from jinja2 import BaseLoader, Environment

from src.core.datatype import uuid7
from src.models.notification import Notification, Template


class NotificationBuilder:
    """Fluent builder that assembles a Notification ORM object.

    Combines a template with variables.
    """

    def __init__(self) -> None:
        self._template: Template | None = None
        self._variables: dict[str, object] = {}
        self._recipient_id: UUID | None = None
        self._channel: str = ""
        self._event_type: str = ""
        self._notification_type: str = "info"

    def with_template(self, template: Template) -> "NotificationBuilder":
        self._template = template
        return self

    def with_variables(self, variables: dict[str, object]) -> "NotificationBuilder":
        self._variables = variables
        return self

    def with_recipient(self, user_id: UUID) -> "NotificationBuilder":
        self._recipient_id = user_id
        return self

    def with_channel(self, channel: str) -> "NotificationBuilder":
        self._channel = channel
        return self

    def with_event_type(self, event_type: str) -> "NotificationBuilder":
        self._event_type = event_type
        return self

    def with_notification_type(self, ntype: str) -> "NotificationBuilder":
        self._notification_type = ntype
        return self

    def build(self) -> Notification:
        if self._template is None:
            raise ValueError("Template is required")

        # Body renders as HTML (EmailChannel sends it as text/html) and can
        # embed variables a seller/buyer controls (product names, addresses,
        # ...) — autoescape so those can't inject markup into the email.
        # Subject is plain text, where HTML-escaping would just corrupt
        # ordinary characters like "&", so it gets its own non-escaping env.
        plain_env = Environment(loader=BaseLoader(), autoescape=False)  # noqa: S701 -- plain-text subject, not HTML
        html_env = Environment(loader=BaseLoader(), autoescape=True)
        subject_tpl = plain_env.from_string(self._template.subject)
        body_tpl = html_env.from_string(self._template.body_template)

        subject = subject_tpl.render(**self._variables)
        body = body_tpl.render(**self._variables)

        return Notification(
            id=uuid7(),
            user_id=self._recipient_id or uuid7(),
            event_type=self._event_type or self._template.code,
            channel=self._channel or "",
            notification_type=self._notification_type,
            subject=subject,
            body=body,
            status="unread",
            created_at=datetime.now(UTC),
        )
