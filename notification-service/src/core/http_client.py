from http import HTTPStatus
from typing import Any

import aiohttp
from backoff import expo, on_exception


def _is_client_error(exc: BaseException) -> bool:
    """4xx is the server's answer, not a transient failure.

    Retrying it would send the identical request and get the identical
    answer back, at the cost of exponential-backoff latency (seconds) on
    every expected 4xx -- e.g. "no payment for this order yet" or "product
    out of stock", both routinely handled as normal control flow by callers
    of this client, not as failures.
    """
    if not isinstance(exc, aiohttp.ClientResponseError):
        return False
    return exc.status < HTTPStatus.INTERNAL_SERVER_ERROR


class CircuitBreakerClient:
    def __init__(self, base_url: str = "", timeout: int = 10) -> None:
        self._base_url = base_url
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @on_exception(expo, aiohttp.ClientError, max_tries=3, giveup=_is_client_error)
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Read the JSON body before the session/response context managers close.

        Returning the raw response object and reading .json() afterward
        (the previous approach) fails with "Connection closed", because
        __aexit__ on both `async with` blocks releases the connection back
        to an already-shut-down session as soon as this method returns.
        """
        url = f"{self._base_url}{path}"
        async with (
            aiohttp.ClientSession(timeout=self._timeout) as session,
            session.request(method, url, **kwargs) as response,
        ):
            response.raise_for_status()
            data: dict[str, Any] = await response.json()
            return data

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", path, **kwargs)
