from src.routers.dictionaries import router as dictionaries_router
from src.routers.health import router as health_router

routers = [health_router, dictionaries_router]

__all__ = ['dictionaries', 'health']
