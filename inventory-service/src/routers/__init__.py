from src.routers.health import router as health_router
from src.routers.stock import router as stock_router
from src.routers.warehouses import router as warehouses_router

routers = [health_router, stock_router, warehouses_router]

__all__ = ["health", "stock", "warehouses"]
