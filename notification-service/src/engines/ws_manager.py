import asyncio
import contextlib
import logging
from typing import Any

from fastapi import WebSocket

from src.schemes.ws_message import WSMessage

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections per user, with pub/sub for horizontal scaling."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._redis = redis_client

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(ws)
        logger.info(
            "WebSocket connected: user=%s total_connections=%d",
            user_id,
            len(self._connections[user_id]),
        )

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(ws)
                if not self._connections[user_id]:
                    del self._connections[user_id]
        with contextlib.suppress(Exception):
            await ws.close()
        logger.info("WebSocket disconnected: user=%s", user_id)

    async def send_to_user(self, user_id: str, message: WSMessage) -> None:
        """Send a message to all active WebSocket connections for a user."""
        payload = message.model_dump_json()
        async with self._lock:
            sockets = list(self._connections.get(str(user_id), set()))

        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning("Failed to send WS to user=%s: %s", user_id, exc)

    async def broadcast(
        self,
        message: WSMessage,
        role: str | None = None,  # noqa: ARG002
    ) -> None:
        """Broadcast to all connected users.

        `role` is accepted but not yet applied — this class doesn't track
        which role each connected socket belongs to, so filtering isn't
        possible without wiring that through connect() first. Nothing
        calls this method yet, so the gap is a placeholder, not a live bug.
        """
        payload = message.model_dump_json()
        async with self._lock:
            all_sockets: list[WebSocket] = []
            for sockets in self._connections.values():
                all_sockets.extend(sockets)

        for ws in all_sockets:
            with contextlib.suppress(Exception):
                await ws.send_text(payload)

    async def close_all(self) -> None:
        async with self._lock:
            for _uid, sockets in list(self._connections.items()):
                for ws in sockets:
                    with contextlib.suppress(Exception):
                        await ws.close()
            self._connections.clear()
        logger.info("All WebSocket connections closed")
