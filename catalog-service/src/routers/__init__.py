from src.routers.categories import router as categories_router
from src.routers.health import router as health_router
from src.routers.products import router as products_router
from src.routers.query_sets import router as query_sets_router

routers = [health_router, products_router, categories_router, query_sets_router]

__all__ = ["categories", "health", "products", "query_sets"]
