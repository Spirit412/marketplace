from src.routers.error_templates import router as error_templates_router
from src.routers.health import router as health_router
from src.routers.imports import router as imports_router

# error_templates shares the /imports prefix with a static path, so it must be
# registered before the router that declares /imports/{task_id}, otherwise the
# parameterised route shadows it.
routers = [health_router, error_templates_router, imports_router]

__all__ = ['imports', 'health', 'error_templates']
