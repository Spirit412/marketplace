from functools import lru_cache

from faststream.rabbit import RabbitBroker

from src.config.settings import settings


@lru_cache
def get_broker() -> RabbitBroker:
    return RabbitBroker(url=settings.rabbitmq.url)


async def check_rabbitmq() -> None:
    # connect() is idempotent — it only opens a connection if one doesn't
    # already exist — so there's no need to peek at the broker's private
    # _connection state first.
    await get_broker().connect()
