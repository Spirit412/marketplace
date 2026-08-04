from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.dependencies import Inject
from src.schemes.response.import_dto import ErrorTemplateResponse
from src.services.error_template_service import ErrorTemplateService

router = APIRouter(prefix="/imports", tags=["error-templates"])


@router.get(
    "/error-templates",
    summary="Get error templates",
)
async def get_error_templates(
    service: Annotated[ErrorTemplateService, Depends(Inject(ErrorTemplateService))],
    locale: Annotated[
        str, Query(description="Locale to fetch templates for.", examples=["ru"])
    ] = "ru",
) -> list[ErrorTemplateResponse]:
    """Get error templates for the specified locale."""
    return service.get_templates(locale)
