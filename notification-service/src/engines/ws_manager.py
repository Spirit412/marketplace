import asyncio
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

    async def connect(self, user_uuid: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            if user_uuid not in self._connections:
                self._connections[user_uuid] = set()
            self._connections[user_uuid].add(ws)
        logger.info("WebSocket connected: user=%s total_connections=%d", user_uuid, len(self._connections[user_uuid]))

    async def disconnect(self, user_uuid: str, ws: WebSocket) -> None:
        async with self._lock:
            if user_uuid in self._connections:
                self._connections[user_uuid].discard(ws)
                if not self._connections[user_uuid]:
                    del self._connections[user_uuid]
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("WebSocket disconnected: user=%s", user_uuid)

    async def send_to_user(self, user_uuid: str, message: WSMessage) -> None:
        """Send a message to all active WebSocket connections for a user."""
        payload = message.model_dump_json()
        async with self._lock:
            sockets = list(self._connections.get(str(user_uuid), set()))

        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning("Failed to send WS to user=%s: %s", user_uuid, exc)

    async def broadcast(self, message: WSMessage, role: str | None = None) -> None:
        """Broadcast to all connected users, optionally filtered by role."""
        payload = message.model_dump_json()
        async with self._lock:
            all_sockets: list[WebSocket] = []
            for uid, sockets in self._connections.items():
                all_sockets.extend(sockets)

        for ws in all_sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                pass

    async def close_all(self) -> None:
        async with self._lock:
            for uid, sockets in list(self._connections.items()):
                for ws in sockets:
                    try:
                        await ws.close()
                    except Exception:
                        pass
            self._connections.clear()
        logger.info("All WebSocket connections closed")
