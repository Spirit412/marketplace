from .auth import router as auth_router
from .groups import router as groups_router
from .health import router as health_router
from .permissions import router as permissions_router
from .roles import router as roles_router
from .user_access import router as user_access_router

routers = [
    health_router,
    auth_router,
    roles_router,
    permissions_router,
    groups_router,
    user_access_router,
]

__all__ = ["routers"]
