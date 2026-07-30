from faststream.rabbit import RabbitBroker, RabbitQueue

from src.config.settings import settings
from src.schemes.internal.import_dto import ImportCompletedPayload

broker = RabbitBroker(settings.rabbitmq.url)

validate_queue = RabbitQueue("import.validate", durable=True)


@broker.subscriber(validate_queue)
async def handle_import_completed(payload: ImportCompletedPayload) -> None:
    """Handle ImportCompletedPayload — process validated import."""
