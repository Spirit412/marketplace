from typing import Any

from sqlalchemy import Select

from src.models.product import Product


class SortStrategy:
    """Base sort strategy."""

    def apply(self, stmt: Select[Any]) -> Select[Any]:
        raise NotImplementedError


class PriceSort(SortStrategy):
    def apply(self, stmt: Select[Any]) -> Select[Any]:
        return stmt.order_by(Product.price.asc())


class PriceDescSort(SortStrategy):
    def apply(self, stmt: Select[Any]) -> Select[Any]:
        return stmt.order_by(Product.price.desc())


class RatingSort(SortStrategy):
    def apply(self, stmt: Select[Any]) -> Select[Any]:
        return stmt.order_by(Product.rating.desc())


class NewestSort(SortStrategy):
    def apply(self, stmt: Select[Any]) -> Select[Any]:
        return stmt.order_by(Product.created_at.desc())


class RelevanceSort(SortStrategy):
    def apply(self, stmt: Select[Any]) -> Select[Any]:
        return stmt.order_by(Product.search_vector)


def get_sort_strategy(sort_field: str) -> SortStrategy:
    strategies: dict[str, SortStrategy] = {
        "price": PriceSort(),
        "price_desc": PriceDescSort(),
        "rating": RatingSort(),
        "newest": NewestSort(),
        "relevance": RelevanceSort(),
    }
    return strategies.get(sort_field, NewestSort())
