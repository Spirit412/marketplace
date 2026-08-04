"""Shared infrastructure kernel, identical in every microservice.

This package is kept byte-for-byte identical across all services so it can be
extracted into its own distribution and consumed as a dependency. Nothing here
imports service-specific modules — no models, repositories, routers, or
services, and no configuration.

Configuration is injected rather than imported: a consuming service calls
`core.configure(settings)` with an object satisfying `core.config.CoreSettings`
(a `jwt` section with SECRET_KEY/ALGORITHM and a `postgres` section). Doing
that at the bottom of the service's own configuration module means every entry
point — API, workers, Alembic, seeds — is configured by the act of importing
its settings, with no per-entry-point wiring to forget.
"""

from . import (
    access,
    auth,
    config,
    database,
    datatype,
    event,
    health,
    http_client,
    import_uow,
    orm,
    repository,
    state_machine,
    uow,
)
from .config import configure

__all__ = [
    "access",
    "auth",
    "config",
    "configure",
    "database",
    "datatype",
    "event",
    "health",
    "http_client",
    "import_uow",
    "orm",
    "repository",
    "state_machine",
    "uow",
]
