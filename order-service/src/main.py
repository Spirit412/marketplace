from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth_middleware import AuthMiddleware, init_auth
from src.config.settings import settings
from src.depends import init_container
from src.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    RateLimitExceededError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from src.routers import routers
from src.workers_main import broker as _events_broker


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_container()
    # Runs the payment.succeeded/payment.failed consumers (workers_main.py)
    # in this same process rather than a separate worker container — no
    # other service in this project runs a standalone worker process either
    # (their workers_main.py files exist but are never invoked), so this
    # keeps order-service self-contained instead of adding a new deployment
    # topology just for itself.
    await _events_broker.start()
    yield
    await _events_broker.stop()


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(
        _request: Request, exc: DomainError
    ) -> JSONResponse:
        status_map: dict[type[DomainError], int] = {
            NotFoundError: 404,
            ConflictError: 409,
            ValidationError: 400,
            UnauthorizedError: 401,
            ForbiddenError: 403,
            ServiceUnavailableError: 503,
            RateLimitExceededError: 429,
        }
        status_code = status_map.get(type(exc), 500)
        errors = getattr(exc, "errors", None)
        detail: str | list[str] = errors if errors and len(errors) > 1 else str(exc)
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
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
app.add_middleware(AuthMiddleware, exclude_paths=["/health", "/docs", "/openapi.json"])

for router in routers:
    app.include_router(router)

_register_exception_handlers(app)
