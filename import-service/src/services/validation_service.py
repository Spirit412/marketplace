class RowValidator:
    def validate_rows(
        self,
        rows: list[dict],
        import_type: str,
        strategy: object,
    ) -> tuple[list[dict], list[dict]]:
        required = strategy.get_required_columns()
        valid: list[dict] = []
        errors: list[dict] = []

        for row_item in rows:
            row_data = row_item["data"]
            row_errors: dict[str, str] = {}

            for field in required:
                error = self.validate_field(field, row_data.get(field), {"required": True})
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
    def validate_field(field: str, value: object, rules: dict) -> str | None:
        required = rules.get("required", False)
        if required and (value is None or (isinstance(value, str) and not value.strip())):
            return f"Field '{field}' is required"

        if value is not None and isinstance(value, str):
            value = value.strip()

        if field == "price" or field == "sale_price":
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
