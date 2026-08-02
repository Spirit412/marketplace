"""Application settings via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    USER: str = "marketplace"
    PASSWORD: str = "marketplace"  # noqa: S105 -- local-dev default, overridden by env in real deployments
    HOST: str = "mp-postgres"
    PORT: int = 5432
    DB: str = "marketplace"

    POOL_PRE_PING: bool = True
    ECHO: bool = False
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 5
    POOL_RECYCLE: int = 3600

    AUTO_COMMIT: bool = False
    AUTO_FLUSH: bool = False
    EXPIRE_ON_COMMIT: bool = False

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    HOST: str = "mp-redis"
    PORT: int = 6379
    DB: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


class RabbitMQSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    USER: str = "marketplace"
    PASSWORD: str = "marketplace"  # noqa: S105 -- local-dev default, overridden by env in real deployments
    HOST: str = "mp-rabbitmq"
    PORT: int = 5672

    @property
    def url(self) -> str:
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}//"


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    SECRET_KEY: str = "change-me"  # noqa: S105 -- local-dev default, overridden by env in real deployments
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class UpstreamSettings(BaseSettings):
    """API Gateway upstream service hostnames."""

    model_config = SettingsConfigDict(env_prefix="UPSTREAM_")

    CATALOG_HOST: str = "mp-catalog-service"
    ORDER_HOST: str = "mp-order-service"
    PAYMENT_HOST: str = "mp-payment-service"
    NOTIFICATION_HOST: str = "mp-notification-service"
    SCHEDULER_HOST: str = "mp-scheduler-service"
    REPORT_HOST: str = "mp-report-service"
    INVENTORY_HOST: str = "mp-inventory-service"
    DICTIONARY_HOST: str = "mp-dictionary-service"
    IMPORT_HOST: str = "mp-import-service"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "inventory-service"
    APP_ID: str = "INVENTORY"
    APP_PORT: int = 8180
    AUTH_SERVICE_URL: str = "http://mp-auth-service:8110"
    LOG_LEVEL: str = "debug"
    LOG_FORMAT: str = "text"  # "text" | "json" (for ELK/Loki/etc.)

    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    jwt: JWTSettings = JWTSettings()

    SYSTEM_TOKEN: str = ""

    CATALOG_SERVICE_URL: str = "http://mp-catalog-service:8120"

    STOCK_LOCK_TTL: int = 10
    STOCK_CACHE_TTL: int = 30

    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()

from src.core.config import configure as _configure_core  # noqa: E402

_configure_core(settings)
