from src.routers.health import router as health_router
from src.routers.reports import router as reports_router

routers = [health_router, reports_router]

__all__ = ["health", "reports"]
