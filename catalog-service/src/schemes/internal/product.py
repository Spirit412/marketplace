
from pydantic import BaseModel


class ProductCreatedPayload(BaseModel):
    product_id: str
    seller_id: str
    name: str
    price: float
    category_id: str | None = None


class ProductUpdatedPayload(BaseModel):
    product_id: str
    seller_id: str
    changed_fields: dict
