from fastapi import APIRouter, Depends, Query

from src.config.settings import settings
from src.core.auth import Permission, require_permission
from src.schemes.response.import_dto import ErrorTemplateResponse

router = APIRouter(prefix="/imports", tags=["error-templates"])

_ERROR_TEMPLATES = {
    "ru": [
        {"code": "MISSING_REQUIRED", "message": "Поле обязательно для заполнения"},
        {"code": "INVALID_TYPE", "message": "Неверный тип данных"},
        {"code": "DUPLICATE_SKU", "message": "SKU уже существует"},
        {"code": "CATEGORY_NOT_FOUND", "message": "Категория не найдена"},
        {"code": "BRAND_NOT_FOUND", "message": "Бренд не найден"},
        {"code": "INVALID_PRICE", "message": "Некорректная цена"},
        {"code": "INVALID_QUANTITY", "message": "Некорректное количество"},
    ],
    "en": [
        {"code": "MISSING_REQUIRED", "message": "Field is required"},
        {"code": "INVALID_TYPE", "message": "Invalid data type"},
        {"code": "DUPLICATE_SKU", "message": "SKU already exists"},
        {"code": "CATEGORY_NOT_FOUND", "message": "Category not found"},
        {"code": "BRAND_NOT_FOUND", "message": "Brand not found"},
        {"code": "INVALID_PRICE", "message": "Invalid price"},
        {"code": "INVALID_QUANTITY", "message": "Invalid quantity"},
    ],
}


@router.get(
    "/error-templates",
    response_model=list[ErrorTemplateResponse],
    summary="Get error templates",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_error_templates(
    locale: str = Query(default="ru"),
) -> list[ErrorTemplateResponse]:
    """Get error templates for the specified locale."""
    templates = _ERROR_TEMPLATES.get(locale, _ERROR_TEMPLATES["ru"])
    return [
        ErrorTemplateResponse(code=tmpl["code"], message=tmpl["message"], locale=locale)
        for tmpl in templates
    ]
