from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    TokenPayload,
    get_token_payload,
    require_permission,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.enums.dictionary_type import DictionaryType
from src.schemes.request.dictionary import CreateDictionaryEntry
from src.schemes.response.dictionary import (
    DictionaryEntryResponse,
    DictionaryListResponse,
)
from src.services.dictionary_service import DictionaryService


router = APIRouter(
    prefix="/dictionaries",
    tags=["dictionaries"],
)


@router.get("/{type}", response_model=DictionaryListResponse, summary="Get dictionary entries by type")
async def get_dictionary_entries(
    type: DictionaryType,
    service: Annotated[DictionaryService, Depends(Inject(DictionaryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> DictionaryListResponse:
    """Get dictionary entries filtered by type."""
    items = await service.get_all(session=session, type_=type)
    return DictionaryListResponse(
        type=type,
        items=[DictionaryEntryResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.post(
    "/{type}",
    response_model=DictionaryEntryResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Create dictionary entry",
)
async def create_dictionary_entry(
    type: DictionaryType,
    body: CreateDictionaryEntry,
    service: Annotated[DictionaryService, Depends(Inject(DictionaryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> DictionaryEntryResponse:
    """Create or update a dictionary entry for the given type."""
    entry = await service.create_or_update(
        session=session,
        type_=type,
        code=body.code,
        data=body.data,
    )
    return DictionaryEntryResponse.model_validate(entry)
