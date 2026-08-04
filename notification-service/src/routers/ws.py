import logging
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.config.settings import settings
from src.core.auth import decode_jwt
from src.dependencies import get_ws_manager
from src.engines.ws_manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    user_id: UUID,
    ws: WebSocket,
    token: str = "",
    manager: WebSocketManager = Depends(get_ws_manager),
) -> None:
    """Accept WebSocket connections and register with the manager."""
    if token:
        try:
            payload = decode_jwt(token, settings.jwt.SECRET_KEY, settings.jwt.ALGORITHM)
            user_id = UUID(payload.user_id)
        except Exception:
            await ws.close(code=4003, reason="Invalid token")
            return

    user_key = str(user_id)
    await manager.connect(user_key, ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket error for user=%s: %s", user_key, exc)
    finally:
        await manager.disconnect(user_key, ws)
