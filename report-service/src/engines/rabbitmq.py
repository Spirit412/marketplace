try:
    from faststream.rabbit import RabbitBroker
except ImportError:
    RabbitBroker = None
from src.config.settings import settings

_broker: "RabbitBroker | None" = None


def get_broker() -> "RabbitBroker":
    global _broker
    if _broker is None:
        _broker = RabbitBroker(url=settings.rabbitmq.url)
    return _broker


async def check_rabbitmq() -> None:
    broker = get_broker()
    if not broker._connection:
        await broker.connect()
