from abc import ABC, abstractmethod
from typing import Any


class BaseImportStrategy(ABC):
    @abstractmethod
    async def process_row(self, row_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_required_columns(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_optional_columns(self) -> list[str]:
        raise NotImplementedError


class ProductsImport(BaseImportStrategy):
    def get_required_columns(self) -> list[str]:
        return ["name", "price", "category_id"]

    def get_optional_columns(self) -> list[str]:
        return ["description", "sku", "brand", "images"]

    async def process_row(self, row_data: dict[str, Any]) -> dict[str, Any]:
        return row_data


class InventoryImport(BaseImportStrategy):
    def get_required_columns(self) -> list[str]:
        return ["sku", "quantity"]

    def get_optional_columns(self) -> list[str]:
        return ["warehouse_id"]

    async def process_row(self, row_data: dict[str, Any]) -> dict[str, Any]:
        return row_data


class PricesImport(BaseImportStrategy):
    def get_required_columns(self) -> list[str]:
        return ["sku", "price"]

    def get_optional_columns(self) -> list[str]:
        return ["sale_price", "currency"]

    async def process_row(self, row_data: dict[str, Any]) -> dict[str, Any]:
        return row_data
