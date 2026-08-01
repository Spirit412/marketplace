"""FastStream composition root for order-service.

Builds the broker and includes each domain's router via
`broker.include_router()` — the org's usual FastStream convention (see
web_milk_back/api/app/workers_main.py) — rather than declaring subscribers
directly on the broker. `app` is exposed for standalone execution
(`faststream run src.workers_main:app`); no service in this project
currently runs a standalone worker container though — main.py's lifespan
starts/stops `broker` in-process instead, so `app` exists for parity with
the convention and isn't itself imported anywhere yet.
"""

from faststream import FastStream

from src.consumers.payment_events import router as payment_events_router
from src.engines.rabbitmq import get_broker

broker = get_broker()
broker.include_router(payment_events_router)

app = FastStream(broker)
