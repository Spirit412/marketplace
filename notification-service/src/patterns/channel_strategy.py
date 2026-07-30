import abc
import logging

from src.config.settings import settings
from src.enums.channel import Channel
from src.engines.ws_manager import WebSocketManager
from src.models.notification import Notification
from src.schemes.ws_message import WSMessage

logger = logging.getLogger(__name__)


class BaseChannel(abc.ABC):
    """Abstract channel strategy."""

    @abc.abstractmethod
    async def send(self, notification: Notification) -> bool: ...


class EmailChannel(BaseChannel):
    """Deliver notification via SMTP."""

    async def send(self, notification: Notification) -> bool:
        try:
            from email.mime.text import MIMEText

            import aiosmtplib

            msg = MIMEText(notification.body, "html", "utf-8")
            msg["Subject"] = notification.subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = "placeholder@example.com"

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER or None,
                password=settings.SMTP_PASSWORD or None,
                start_tls=True,
            )
            return True
        except Exception as exc:
            logger.warning("EmailChannel failed for %s: %s", notification.id, exc)
            return False


class SmsChannel(BaseChannel):
    """Deliver notification via SMS API."""

    async def send(self, notification: Notification) -> bool:
        try:
            import httpx

            if not settings.SMS_API_KEY or not settings.SMS_API_URL:
                logger.warning("SMS not configured")
                return False

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    settings.SMS_API_URL,
                    json={
                        "api_key": settings.SMS_API_KEY,
                        "to": "placeholder",
                        "text": f"{notification.subject}\n{notification.body}",
                    },
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            logger.warning("SmsChannel failed for %s: %s", notification.id, exc)
            return False


class PushChannel(BaseChannel):
    """Deliver notification via FCM/APNs."""

    async def send(self, notification: Notification) -> bool:
        logger.info("PushChannel: %s (FCM/APNs stub)", notification.id)
        return True


class WebSocketChannel(BaseChannel):
    """Deliver notification via WebSocket manager."""

    def __init__(self, ws_manager: WebSocketManager) -> None:
        self._ws_manager = ws_manager

    async def send(self, notification: Notification) -> bool:
        try:
            msg = WSMessage(
                type=notification.event_type,
                title=notification.subject,
                body=notification.body,
                notification_type=notification.notification_type,
                timestamp=notification.created_at,
            )
            await self._ws_manager.send_to_user(str(notification.user_uuid), msg)
            return True
        except Exception as exc:
            logger.warning("WebSocketChannel failed for %s: %s", notification.id, exc)
            return False


class ChannelRegistry:
    """Registry mapping Channel → strategy class."""

    def __init__(self, ws_manager: WebSocketManager | None = None) -> None:
        self._strategies: dict[str, BaseChannel] = {
            Channel.email: EmailChannel(),
            Channel.sms: SmsChannel(),
            Channel.push: PushChannel(),
        }
        if ws_manager is not None:
            self._strategies[Channel.websocket] = WebSocketChannel(ws_manager)

    def get(self, channel: str) -> BaseChannel | None:
        return self._strategies.get(channel)

    def register(self, channel: str, strategy: BaseChannel) -> None:
        self._strategies[channel] = strategy
