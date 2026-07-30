import asyncio
import logging

from faststream.rabbit import RabbitBroker

from src.config.settings import settings
from src.core.database import get_async_session
from src.dependencies import (
    build_notification_service,
    get_channel_registry,
    get_template_registry,
)
from src.engines.rabbitmq import create_subscriber_router
from src.engines.ws_manager import WebSocketManager
from src.schemes.internal.notification import NotificationPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification-worker")


async def main() -> None:

    ws_manager = WebSocketManager()
    channel_registry = get_channel_registry()
    template_registry = get_template_registry()

    broker = RabbitBroker(settings.rabbitmq.url)
    router = create_subscriber_router()

    @router.subscriber("notification.all_events")
    async def handle_event(body: dict) -> None:
        try:
            payload = NotificationPayload(**body)
            async for session in get_async_session():
                service = build_notification_service()
                await service.dispatch(session, payload)
                break
        except Exception as exc:
            logger.error("Failed to process event: %s", exc, exc_info=True)

    broker.include_router(router)

    try:
        await broker.start()
        logger.info("Notification worker started, listening for events...")
        await asyncio.Event().wait()
    finally:
        await broker.close()
        await ws_manager.close_all()


if __name__ == "__main__":
    asyncio.run(main())
