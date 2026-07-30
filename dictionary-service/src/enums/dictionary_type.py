from enum import StrEnum


class DictionaryType(StrEnum):
    currencies = "currencies"
    units = "units"
    countries = "countries"
    regions = "regions"
    timezones = "timezones"
    property_types = "property_types"
    order_statuses = "order_statuses"
    property_categories = "property_categories"
    error_templates = "error_templates"
