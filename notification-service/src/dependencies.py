from rodi import Container

container = Container()

from src.engines.redis import get_redis_client
from src.engines.ws_manager import WebSocketManager
from src.patterns.channel_strategy import ChannelRegistry
from src.patterns.template_registry import TemplateRegistry
from src.repositories.notification_repo import NotificationRepository
from src.services.notification_service import NotificationService

_ws_manager: WebSocketManager | None = None
_channel_registry: ChannelRegistry | None = None
_template_registry: TemplateRegistry | None = None


def get_ws_manager() -> WebSocketManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager(redis_client=get_redis_client())
    return _ws_manager


def get_channel_registry() -> ChannelRegistry:
    global _channel_registry
    if _channel_registry is None:
        _channel_registry = ChannelRegistry(ws_manager=get_ws_manager())
    return _channel_registry


def get_template_registry() -> TemplateRegistry:
    global _template_registry
    if _template_registry is None:
        _template_registry = TemplateRegistry()
    return _template_registry


def build_notification_service() -> NotificationService:
    """Build the notification service.

    The repository is stateless — the session is passed per call — so the
    service carries no request state and is safe to reuse.
    """
    return NotificationService(
        notification_repo=NotificationRepository(),
        template_registry=get_template_registry(),
        channel_registry=get_channel_registry(),
    )


def get_notification_service() -> NotificationService:
    """FastAPI dependency yielding the notification service."""
    return build_notification_service()
