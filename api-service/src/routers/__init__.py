from src.routers.health import router as health_router
from src.routers.orders import router as orders_router
from src.routers.storefront import router as storefront_router

routers = [health_router, storefront_router, orders_router]

__all__ = ["routers"]
