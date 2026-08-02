"""Application settings via pydantic-settings.

No PostgresSettings/JWTSettings/RabbitMQSettings here — api-service has no
database, never issues or decodes a JWT itself (it forwards the caller's
token as-is to downstream services), and doesn't publish/consume RMQ
events. Its only state is the AuthMiddleware check-access cache in Redis.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    HOST: str = "mp-redis"
    PORT: int = 6379
    DB: int = 0

    @property
    def url(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "api-service"
    APP_ID: str = "API"
    APP_PORT: int = 8100
    LOG_LEVEL: str = "debug"
    LOG_FORMAT: str = "text"  # "text" | "json" (for ELK/Loki/etc.)

    AUTH_SERVICE_URL: str = "http://mp-auth-service:8110"

    CATALOG_SERVICE_URL: str = "http://mp-catalog-service:8120"
    ORDER_SERVICE_URL: str = "http://mp-order-service:8130"
    PAYMENT_SERVICE_URL: str = "http://mp-payment-service:8140"
    INVENTORY_SERVICE_URL: str = "http://mp-inventory-service:8180"

    redis: RedisSettings = RedisSettings()


settings = Settings()
