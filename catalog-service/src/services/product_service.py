import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.engines.rabbitmq import RabbitMQEngine
from src.engines.redis import get_redis_client
from src.models.product import Product
from src.patterns.query_constructor import ProductQueryConstructor
from src.patterns.sort_strategy import get_sort_strategy
from src.repositories.product_repo import ProductRepo


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepo,
        settings: Settings,
        rmq_engine: RabbitMQEngine,
    ) -> None:
        self._repo = product_repo
        self._settings = settings
        self._rmq = rmq_engine
        self._redis = get_redis_client()
        self._query_constructor = ProductQueryConstructor()

    async def create(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        name: str,
        price: float,
        description: str | None = None,
        sku: str | None = None,
        stock: int = 0,
        category_id: uuid.UUID | None = None,
        custom_properties_config: dict[str, Any] | None = None,
        images: dict[str, Any] | None = None,
    ) -> Product:
        product = Product(
            seller_id=seller_id,
            name=name,
            price=price,
            description=description,
            sku=sku,
            stock=stock,
            category_id=category_id,
            custom_properties_config=custom_properties_config or {},
            images=images or {},
        )
        product = await self._repo.create(session, product)
        await self._cache_product(product)
        await self._publish_event("product.created", product)
        return product

    async def get_by_id(
        self, session: AsyncSession, product_id: uuid.UUID
    ) -> Product | None:
        cached = await self._redis.get(f"product:{product_id}")
        if cached:
            text = cached.decode() if isinstance(cached, bytes) else cached
            return self._deserialize_product(text)

        product = await self._repo.get_by_id(session, product_id)
        if product:
            await self._cache_product(product)
        return product

    async def update(
        self,
        session: AsyncSession,
        product_id: uuid.UUID,
        **kwargs: object,
    ) -> Product | None:
        product = await self._repo.get_by_id(session, product_id)
        if product is None:
            return None

        changed_fields = {}
        for field, value in kwargs.items():
            if value is not None and hasattr(product, field):
                old_value = getattr(product, field)
                if old_value != value:
                    changed_fields[field] = {"old": str(old_value), "new": str(value)}
                    setattr(product, field, value)

        product = await self._repo.update(session, product)
        await self._cache_product(product)
        if changed_fields:
            await self._publish_event(
                "product.updated",
                product,
                changed_fields=changed_fields,
            )
        return product

    async def delete(self, session: AsyncSession, product_id: uuid.UUID) -> bool:
        result = await self._repo.delete(session, product_id)
        if result:
            await self._redis.delete(f"product:{product_id}")
        return result

    async def search(
        self,
        session: AsyncSession,
        query: str | None = None,
        category_id: uuid.UUID | None = None,
        seller_id: uuid.UUID | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        filters: dict[str, str] | None = None,
    ) -> tuple[list[Product], int]:
        stmt = self._repo.base_query()

        if query:
            stmt = self._query_constructor.apply_search(stmt, query)
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if seller_id:
            stmt = stmt.where(Product.seller_id == seller_id)
        if price_min is not None:
            stmt = stmt.where(Product.price >= price_min)
        if price_max is not None:
            stmt = stmt.where(Product.price <= price_max)
        if status:
            stmt = stmt.where(Product.status == status)

        if filters:
            stmt = self._query_constructor.apply_filters(stmt, filters)

        strategy = get_sort_strategy(sort)
        stmt = strategy.apply(stmt)

        products, total = await self._repo.search(session, stmt, page, page_size)
        return products, total

    async def _cache_product(self, product: Product) -> None:
        key = f"product:{product.id}"
        data = json.dumps(self._serialize_product(product))
        await self._redis.setex(key, self._settings.CACHE_TTL, data)

    async def _publish_event(
        self,
        routing_key: str,
        product: Product,
        changed_fields: dict[str, Any] | None = None,
    ) -> None:
        if self._rmq is None:
            return
        payload: dict[str, Any] = {
            "product_id": str(product.id),
            "seller_id": str(product.seller_id),
            "name": product.name,
            "price": product.price,
            "category_id": str(product.category_id) if product.category_id else None,
        }
        if changed_fields:
            payload["changed_fields"] = changed_fields
        await self._rmq.publish(routing_key, payload)

    @staticmethod
    def _serialize_product(product: Product) -> dict[str, Any]:
        return {
            "id": str(product.id),
            "seller_id": str(product.seller_id),
            "category_id": str(product.category_id) if product.category_id else None,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "sku": product.sku,
            "stock": product.stock,
            "rating": product.rating,
            "custom_properties_config": product.custom_properties_config,
            "images": product.images,
            "is_active": product.is_active,
            "status": product.status,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat(),
        }

    @staticmethod
    def _deserialize_product(data: str) -> Product | None:
        """Rebuild a product from its cached payload.

        Mirrors _serialize_product field for field, so a cache hit produces an
        object that satisfies the response schema exactly like a database read.
        """
        try:
            parsed = json.loads(data)
            return Product(
                id=uuid.UUID(parsed["id"]),
                seller_id=uuid.UUID(parsed["seller_id"]),
                category_id=uuid.UUID(parsed["category_id"])
                if parsed.get("category_id")
                else None,
                name=parsed["name"],
                description=parsed.get("description"),
                price=parsed["price"],
                sku=parsed.get("sku"),
                stock=parsed.get("stock", 0),
                rating=parsed.get("rating", 0.0),
                custom_properties_config=parsed.get("custom_properties_config", {}),
                images=parsed.get("images", {}),
                is_active=parsed.get("is_active", True),
                status=parsed.get("status", "active"),
                created_at=datetime.fromisoformat(parsed["created_at"]),
                updated_at=datetime.fromisoformat(parsed["updated_at"]),
            )
        except (json.JSONDecodeError, KeyError):
            return None
