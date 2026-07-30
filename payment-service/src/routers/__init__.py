from src.routers.health import router as health_router
from src.routers.payments import router as payments_router
from src.routers.webhooks import router as webhooks_router

routers = [health_router, payments_router, webhooks_router]

__all__ = ["health", "payments", "webhooks"]
