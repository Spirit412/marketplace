from enum import IntEnum, StrEnum


class PropertyType(IntEnum):
    INT = 0
    STRING = 1
    FLOAT = 2
    BOOL = 3
    SELECT = 4


class ProductSortField(StrEnum):
    PRICE = "price"
    RATING = "rating"
    NEWEST = "newest"
    RELEVANCE = "relevance"


class ProductStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
