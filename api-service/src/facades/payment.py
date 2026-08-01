"""Facade for payment-service.

Forwards the caller's own Authorization header (see facades/catalog.py for
why) — payment-service's own ownership check runs unmodified.
"""

from http import HTTPStatus
from typing import Any

import aiohttp

from src.core.http_client import CircuitBreakerClient


class PaymentFacade:
    def __init__(self, base_url: str) -> None:
        self._client = CircuitBreakerClient(base_url=base_url)

    async def get_payment_by_order(
        self, order_id: str, authorization: str
    ) -> dict[str, Any] | None:
        """Fetch the payment for an order. None if none exists yet.

        Not finding a payment is an expected state (order just created,
        `pending`) — not an error the caller needs to handle specially.
        """
        try:
            return await self._client.get(
                f"/payments/by-order/{order_id}",
                headers={"Authorization": authorization},
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                return None
            raise
