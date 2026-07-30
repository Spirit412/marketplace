from typing import Protocol, runtime_checkable


@runtime_checkable
class JWTSettings(Protocol):
    """Signing parameters required to issue and verify tokens."""

    SECRET_KEY: str
    ALGORITHM: str


@runtime_checkable
class PostgresSettings(Protocol):
    """Connection and pooling parameters required to build the engine."""

    ECHO: bool
    POOL_SIZE: int
    MAX_OVERFLOW: int
    POOL_RECYCLE: int
    POOL_PRE_PING: bool
    EXPIRE_ON_COMMIT: bool
    AUTO_FLUSH: bool

    @property
    def dsn(self) -> str:
        """Async SQLAlchemy connection string."""
        ...


@runtime_checkable
class CoreSettings(Protocol):
    """The settings surface this package depends on.

    Declared structurally so a consuming service can satisfy it with its own
    configuration object without inheriting from anything here. `jwt` and
    `postgres` are typed as properties rather than plain attributes: mypy
    checks a Protocol's plain attributes invariantly, which a concrete
    service's own `JWTSettings`/`PostgresSettings` classes — structurally
    identical but nominally distinct from this module's — would fail even
    though they satisfy every field. Properties are checked covariantly by
    return type, which a plain attribute on the concrete class also satisfies.
    """

    @property
    def jwt(self) -> JWTSettings:
        """JWT signing settings."""
        ...

    @property
    def postgres(self) -> PostgresSettings:
        """Postgres connection settings."""
        ...


_settings: CoreSettings | None = None


def configure(settings: CoreSettings) -> None:
    """Bind the settings object this package will read.

    Call once during import of the consuming service's configuration module,
    before any request is served. Binding at configuration-import time rather
    than in each entry point means workers, migrations, seeds, and the API all
    get a configured package without repeating the call.

    Args:
        settings: An object providing `jwt` and `postgres` sections.
    """
    global _settings
    _settings = settings


def get_settings() -> CoreSettings:
    """Return the bound settings.

    Returns:
        The object passed to `configure`.

    Raises:
        RuntimeError: If `configure` has not been called yet.
    """
    if _settings is None:
        raise RuntimeError(
            "src.core is not configured — call core.configure(settings) from "
            "the service's configuration module before using it"
        )
    return _settings
