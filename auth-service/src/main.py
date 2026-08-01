from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_container()
    yield


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
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
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

for router in routers:
    app.include_router(router)

_register_exception_handlers(app)
