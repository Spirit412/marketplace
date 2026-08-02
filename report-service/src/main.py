import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth_middleware import AuthMiddleware, init_auth
from src.config.settings import settings
from src.core.logging import configure_logging
from src.depends import init_container
from src.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from src.routers import routers

configure_logging(settings.APP_NAME, settings.LOG_FORMAT, settings.LOG_LEVEL)

logger = logging.getLogger(__name__)


def _log_error(request: Request, status_code: int, detail: object) -> None:
    is_server_error = status_code >= HTTPStatus.INTERNAL_SERVER_ERROR
    level = logging.ERROR if is_server_error else logging.WARNING
    logger.log(
        level,
        "%s %s -> %s: %s",
        request.method,
        request.url.path,
        status_code,
        detail,
        exc_info=is_server_error,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_container()
    yield


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_map: dict[type[DomainError], int] = {
            NotFoundError: 404,
            ConflictError: 409,
            ValidationError: 400,
            UnauthorizedError: 401,
            ForbiddenError: 403,
            ServiceUnavailableError: 503,
        }
        status_code = status_map.get(type(exc), 500)
        detail = str(exc)
        _log_error(request, status_code, detail)
        return JSONResponse(status_code=status_code, content={"detail": detail})

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # A genuine bug, not a DomainError covered above -- log the full
        # traceback but never leak it to the caller.
        _log_error(request, 500, str(exc))
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    # Interactive docs are api-service's job (the intended discovery
    # path for consumers) -- disabling them here shrinks the attack
    # surface for anyone who reaches this service's port directly
    # without losing any actual functionality (HTTP/RMQ unaffected).
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_auth(
    auth_service_url=settings.AUTH_SERVICE_URL,
    app_id=settings.APP_ID,
    redis_url=settings.redis.url,
)
app.add_middleware(AuthMiddleware)

for router in routers:
    app.include_router(router)

_register_exception_handlers(app)
