from src.routers.cart import router as cart_router
from src.routers.health import router as health_router
from src.routers.orders import router as orders_router

routers = [health_router, orders_router, cart_router]

__all__ = ["cart", "health", "orders"]
