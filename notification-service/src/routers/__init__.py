from src.routers.health import router as health_router
from src.routers.notifications import router as notifications_router
from src.routers.ws import router as ws_router

routers = [health_router, notifications_router, ws_router]

__all__ = ['ws', 'notifications', 'health']
