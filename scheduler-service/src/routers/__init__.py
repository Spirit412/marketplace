from src.routers.health import router as health_router
from src.routers.jobs import router as jobs_router

routers = [health_router, jobs_router]

__all__ = ["health", "jobs"]
