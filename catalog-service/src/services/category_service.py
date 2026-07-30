import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.engines.redis import get_redis_client
from src.models.category import Category
from src.repositories.category_repo import CategoryRepo
from src.repositories.property_repo import PropertyRepo


class CategoryService:
    def __init__(
        self,
        category_repo: CategoryRepo,
        property_repo: PropertyRepo,
        settings: Settings,
    ) -> None:
        self._repo = category_repo
        self._property_repo = property_repo
        self._settings = settings
        self._redis = get_redis_client()

    async def create(
        self,
        session: AsyncSession,
        name: str,
        slug: str,
        description: str | None = None,
        parent_id: uuid.UUID | None = None,
    ) -> Category:
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
        )
        if parent_id is not None:
            parent = await self._repo.get_by_id(session, parent_id)
            if parent is not None:
                category.tree_id = parent.tree_id
                category.level = parent.level + 1
                category.lft = parent.rgt
                category.rgt = parent.rgt + 1

        category = await self._repo.create(session, category)
        await self._invalidate_cache()
        return category

    async def create_with_properties(
        self,
        session: AsyncSession,
        name: str,
        slug: str,
        description: str | None = None,
        parent_id: uuid.UUID | None = None,
        properties: list[dict] | None = None,
    ) -> Category:
        category = await self.create(
            session,
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
        )
        if properties:
            await self.link_properties(session, category.id, properties)
        return category

    async def get_by_id(
        self, session: AsyncSession, category_id: uuid.UUID
    ) -> Category | None:
        return await self._repo.get_by_id(session, category_id)

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Category | None:
        return await self._repo.get_by_slug(session, slug)

    async def update(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        **kwargs: object,
    ) -> Category | None:
        category = await self._repo.get_by_id(session, category_id)
        if category is None:
            return None

        for field, value in kwargs.items():
            if value is not None and hasattr(category, field):
                setattr(category, field, value)

        category = await self._repo.update(session, category)
        await self._invalidate_cache()
        return category

    async def delete(self, session: AsyncSession, category_id: uuid.UUID) -> bool:
        result = await self._repo.delete(session, category_id)
        if result:
            await self._invalidate_cache()
        return result

    async def get_tree(self, session: AsyncSession) -> list[Category]:
        cached = await self._redis.get("category_tree")
        if cached:
            try:
                data = json.loads(cached)
                return self._deserialize_tree(data)
            except json.JSONDecodeError:
                pass

        tree = await self._repo.get_tree(session)
        await self._cache_tree(tree)
        return tree

    async def get_ancestors(
        self, session: AsyncSession, category_id: uuid.UUID
    ) -> list[Category]:
        category = await self._repo.get_by_id(session, category_id)
        if category is None:
            return []
        return await self._repo.get_ancestors(session, category)

    async def get_descendants(
        self, session: AsyncSession, category_id: uuid.UUID
    ) -> list[Category]:
        category = await self._repo.get_by_id(session, category_id)
        if category is None:
            return []
        return await self._repo.get_descendants(session, category)

    async def move_node(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        new_parent_id: uuid.UUID | None,
    ) -> Category | None:
        category = await self._repo.get_by_id(session, category_id)
        if category is None:
            return None
        result = await self._repo.move_node(session, category, new_parent_id)
        await self._invalidate_cache()
        return result

    async def link_properties(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        property_ids: list[dict],
    ) -> None:
        if self._property_repo is None:
            return
        for prop_data in property_ids:
            await self._property_repo.link_category_property(
                session,
                category_id=category_id,
                property_id=uuid.UUID(prop_data["property_id"]),
                is_required=prop_data.get("is_required", False),
                sort_order=prop_data.get("sort_order", 0),
            )
        await self._invalidate_cache()

    async def _cache_tree(self, tree: list[Category]) -> None:
        """Cache the tree.

        Every field the response schema requires is stored, so a tree rebuilt
        from cache validates the same as one loaded from the database.
        """
        data = json.dumps(
            [
                {
                    "id": str(categ.id),
                    "name": categ.name,
                    "slug": categ.slug,
                    "description": categ.description,
                    "parent_id": str(categ.parent_id) if categ.parent_id else None,
                    "lft": categ.lft,
                    "rgt": categ.rgt,
                    "tree_id": categ.tree_id,
                    "level": categ.level,
                    "created_at": categ.created_at.isoformat(),
                    "updated_at": categ.updated_at.isoformat(),
                }
                for categ in tree
            ]
        )
        await self._redis.setex("category_tree", self._settings.CACHE_TTL, data)

    async def _invalidate_cache(self) -> None:
        await self._redis.delete("category_tree")

    @staticmethod
    def _deserialize_tree(data: list[dict]) -> list[Category]:
        return [
            Category(
                id=uuid.UUID(item["id"]),
                name=item["name"],
                slug=item["slug"],
                description=item.get("description"),
                parent_id=uuid.UUID(item["parent_id"])
                if item.get("parent_id")
                else None,
                lft=item.get("lft", 0),
                rgt=item.get("rgt", 0),
                tree_id=item.get("tree_id", 0),
                level=item.get("level", 0),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
            )
            for item in data
        ]
