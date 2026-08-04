from typing import Any

from src.services.import_strategy import BaseImportStrategy


class RowValidator:
    def validate_rows(
        self,
        rows: list[dict[str, Any]],
        import_type: str,
        strategy: BaseImportStrategy,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        required = strategy.get_required_columns()
        valid: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for row_item in rows:
            row_data = row_item["data"]
            row_errors: dict[str, str] = {}

            for field in required:
                error = self.validate_field(
                    field, row_data.get(field), {"required": True}
                )
                if error:
                    row_errors[field] = error

            if row_errors:
                errors.append(
                    {
                        "row_number": row_item["row_number"],
                        "data": row_data,
                        "errors": row_errors,
                    }
                )
            else:
                valid.append(row_item)

        return valid, errors

    @staticmethod
    def validate_field(field: str, value: object, rules: dict[str, Any]) -> str | None:
        required = rules.get("required", False)
        if required and (
            value is None or (isinstance(value, str) and not value.strip())
        ):
            return f"Field '{field}' is required"

        if value is not None and isinstance(value, str):
            value = value.strip()

        if field in {"price", "sale_price"}:
            if value is not None and isinstance(value, str) and value:
                try:
                    float(value)
                except ValueError:
                    return f"Field '{field}' must be a valid number"

        if field == "quantity":
            if value is not None and isinstance(value, str) and value:
                try:
                    int(value)
                except ValueError:
                    return f"Field '{field}' must be a valid integer"

        return None
