from src.enums.import_type import ImportType
from src.patterns.import_strategy import (
    BaseImportStrategy,
    InventoryImport,
    PricesImport,
    ProductsImport,
)


class ImportStrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[ImportType, BaseImportStrategy] = {
            ImportType.PRODUCTS: ProductsImport(),
            ImportType.INVENTORY: InventoryImport(),
            ImportType.PRICES: PricesImport(),
        }

    def get(self, import_type: ImportType) -> BaseImportStrategy:
        return self._strategies[import_type]
