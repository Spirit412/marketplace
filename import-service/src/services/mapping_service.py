from src.patterns.import_registry import ImportStrategyRegistry


class MappingService:
    @staticmethod
    def auto_map(headers: list[str], import_type: str) -> dict[str, str]:
        """Auto-map CSV headers to expected column names (case-insensitive)."""
        normalized = {
            header.strip().lower().replace(" ", "_"): header.strip()
            for header in headers
        }
        mapping: dict[str, str] = {}

        if import_type == "products":
            target_fields = [
                "name",
                "price",
                "category_id",
                "description",
                "sku",
                "brand",
                "images",
            ]
        elif import_type == "inventory":
            target_fields = ["sku", "quantity", "warehouse_id"]
        else:
            target_fields = ["sku", "price", "sale_price", "currency"]

        for field in target_fields:
            if field in normalized:
                mapping[field] = normalized[field]
            elif field.upper() in (k.upper() for k in headers):
                for header in headers:
                    if header.strip().upper() == field.upper():
                        mapping[field] = header.strip()
                        break

        return mapping

    @staticmethod
    def apply_mapping(row: dict, mapping: dict) -> dict:
        """Apply column mapping to a raw CSV row."""
        result: dict = {}
        for target_field, source_header in mapping.items():
            if source_header in row:
                result[target_field] = row[source_header]
        return result

    @staticmethod
    def validate_mapping(mapping: dict, import_type: str) -> list[str]:
        """Return list of missing required fields."""
        registry = ImportStrategyRegistry()
        strategy = registry.get(import_type)
        required = strategy.get_required_columns()
        return [field_name for field_name in required if field_name not in mapping]
