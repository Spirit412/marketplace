import aiohttp
from backoff import expo, on_exception


class CircuitBreakerClient:
    def __init__(self, base_url: str = "", timeout: int = 10) -> None:
        self._base_url = base_url
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @on_exception(expo, aiohttp.ClientError, max_tries=3)
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: object,
    ) -> dict:
        """Read the JSON body before the response/session context managers
        close the connection — returning the raw response object and reading
        .json() afterward (the previous approach) fails with "Connection
        closed", because __aexit__ on both `async with` blocks releases the
        connection back to an already-shut-down session as soon as this
        method returns.
        """
        url = f"{self._base_url}{path}"
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def get(self, path: str, **kwargs: object) -> dict:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: object) -> dict:
        return await self._request("POST", path, **kwargs)
