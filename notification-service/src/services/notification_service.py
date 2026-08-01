import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.enums.channel import Channel
from src.models.notification import Notification
from src.models.notification import Template as Tpl
from src.patterns.channel_strategy import ChannelRegistry
from src.patterns.notification_builder import NotificationBuilder
from src.patterns.template_registry import TemplateRegistry
from src.repositories.notification_repo import NotificationRepository
from src.schemes.internal.notification import NotificationPayload

logger = logging.getLogger(__name__)


class NotificationService:
    """Orchestrates notification dispatch from RabbitMQ events."""

    def __init__(
        self,
        notification_repo: NotificationRepository,
        template_registry: TemplateRegistry,
        channel_registry: ChannelRegistry,
    ) -> None:
        self._repo = notification_repo
        self._templates = template_registry
        self._channels = channel_registry

    async def dispatch(
        self, session: AsyncSession, event: NotificationPayload
    ) -> list[Notification]:
        """Receive an event from RMQ.

        Renders and sends via all applicable channels (email/websocket).
        """
        results: list[Notification] = []

        template = self._templates.get(event.event_type, event.locale)
        if template is None:
            logger.debug(
                "No template for event_type=%s locale=%s",
                event.event_type,
                event.locale,
            )
            notification = self._build_plain(event)
            await self._repo.create(session, notification)
            results.append(notification)
            return results

        channels_to_use = self._resolve_channels(template)

        for ch_name in channels_to_use:
            strategy = self._channels.get(ch_name)
            if strategy is None:
                continue

            notification = self._build_from_template(template, event, ch_name)
            notification = await self._repo.create(session, notification)

            success = await strategy.send(notification)
            if success:
                await self._repo.update_status(session, notification.id, "read")
            else:
                await self._repo.update_status(session, notification.id, "unread")
                logger.warning(
                    "Failed to send notification %s via %s", notification.id, ch_name
                )

            results.append(notification)

        return results

    async def send_manual(
        self,
        session: AsyncSession,
        user_uuids: list[uuid.UUID],
        subject: str,
        body: str,
        channel: str,
        notification_type: str,
    ) -> list[Notification]:
        """Admin-initiated manual notification (mass mailing)."""
        results: list[Notification] = []
        strategy = self._channels.get(channel)

        for user_id in user_uuids:
            notification = Notification(
                id=uuid7(),
                user_id=user_id,
                event_type="manual",
                channel=channel,
                notification_type=notification_type,
                subject=subject,
                body=body,
                status="unread",
            )
            notification = await self._repo.create(session, notification)

            if strategy is not None:
                success = await strategy.send(notification)
                if success:
                    await self._repo.update_status(session, notification.id, "read")

            results.append(notification)

        return results

    def _build_plain(self, event: NotificationPayload) -> Notification:
        builder = (
            NotificationBuilder()
            .with_event_type(event.event_type)
            .with_channel("email")
            .with_notification_type("info")
            .with_recipient(event.user_id)
            .with_variables(event.variables)
        )
        dummy = Tpl(
            code=event.event_type,
            locale=event.locale,
            subject=f"Event: {event.event_type}",
            body_template=str(event.variables),
        )
        builder.with_template(dummy)
        return builder.build()

    def _build_from_template(
        self, template: object, event: NotificationPayload, channel: str
    ) -> Notification:
        assert isinstance(template, Tpl)  # noqa: S101 -- type narrowing, not input validation
        builder = (
            NotificationBuilder()
            .with_template(template)
            .with_variables(event.variables)
            .with_recipient(event.user_id)
            .with_channel(channel)
            .with_event_type(event.event_type)
        )
        return builder.build()

    @staticmethod
    def _resolve_channels(template: object) -> list[str]:
        assert isinstance(template, Tpl)  # noqa: S101 -- type narrowing, not input validation
        if template.channels:
            if isinstance(template.channels, list):
                return template.channels
            if isinstance(template.channels, dict):
                return list(template.channels.keys())
        return [Channel.email, Channel.websocket]
