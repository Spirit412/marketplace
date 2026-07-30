import uuid

from typing import Any

from sqlalchemy import Select

from src.models.product import Product


class ProductQueryConstructor:
    """Build dynamic SQLAlchemy queries from filter parameters."""

    @staticmethod
    def apply_filters(
        stmt: Select[Any],
        filters: dict[str, str],
    ) -> Select[Any]:
        """Apply dynamic filters to a select statement."""
        for key, value in filters.items():
            if key == "filters_set":
                continue

            if "__" in key:
                field, operator = key.rsplit("__", 1)
            else:
                field = key
                operator = "eq"

            stmt = ProductQueryConstructor._apply_operator(stmt, field, operator, value)

        return stmt

    @staticmethod
    def apply_filters_set(
        stmt: Select[Any],
        filters_set_id: uuid.UUID | None,
    ) -> Select[Any]:
        """Apply a saved filters set to the query."""
        if filters_set_id is None:
            return stmt
        return stmt

    @staticmethod
    def _apply_operator(
        stmt: Select[Any],
        field: str,
        operator: str,
        value: str,
    ) -> Select[Any]:
        """Apply operator to JSONB custom_properties field."""
        jsonb_field = Product.custom_properties_config[field]

        operators = {
            "eq": lambda: jsonb_field.as_string() == value,
            "ne": lambda: jsonb_field.as_string() != value,
            "gt": lambda: jsonb_field.as_float() > float(value),
            "gte": lambda: jsonb_field.as_float() >= float(value),
            "lt": lambda: jsonb_field.as_float() < float(value),
            "lte": lambda: jsonb_field.as_float() <= float(value),
            "contains": lambda: jsonb_field.as_string().contains(value),
            "icontains": lambda: jsonb_field.as_string().ilike(f"%{value}%"),
            "in": lambda: jsonb_field.as_string().in_(value.split(",")),
        }

        op_fn = operators.get(operator)
        if op_fn is not None:
            return stmt.where(op_fn())

        return stmt

    @staticmethod
    def apply_search(
        stmt: Select[Any],
        query: str,
    ) -> Select[Any]:
        """Apply full-text search using tsvector."""
        if not query:
            return stmt
        return stmt.where(Product.search_vector.op("@@")(f"plainto_tsquery('{query}')"))

    @staticmethod
    def apply_sorting(
        stmt: Select[Any],
        sort_field: str = "newest",
    ) -> Select[Any]:
        """Apply sorting based on sort field."""
        sort_map: dict[str, Any] = {
            "price": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "rating": Product.rating.desc(),
            "newest": Product.created_at.desc(),
            "relevance": Product.search_vector,
        }
        order_col = sort_map.get(sort_field)
        if order_col is not None and sort_field != "relevance":
            stmt = stmt.order_by(order_col)
        return stmt
