class ProductFromRowBuilder:
    @staticmethod
    def build(row_data: dict) -> dict:
        """Build a ProductCreateRequest-compatible dict from row data."""
        product: dict = {
            "name": str(row_data["name"]).strip(),
            "price": float(row_data["price"]),
            "category_id": str(row_data["category_id"]).strip(),
        }

        if row_data.get("description"):
            product["description"] = str(row_data["description"]).strip()
        if row_data.get("sku"):
            product["sku"] = str(row_data["sku"]).strip()
        if row_data.get("brand"):
            product["brand"] = str(row_data["brand"]).strip()
        if row_data.get("images"):
            raw = row_data["images"]
            if isinstance(raw, str):
                product["images"] = [
                    img.strip() for img in raw.split(",") if img.strip()
                ]
            elif isinstance(raw, list):
                product["images"] = [str(img).strip() for img in raw if img]

        return product
