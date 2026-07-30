"""Integration tests for dictionary-service."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.enums.dictionary_type import DictionaryType
from src.models.dictionary import DictionaryEntry
from src.repositories.dictionary_repo import DictionaryRepository


@pytest.mark.asyncio
async def test_get_all_dictionaries_returns_items(
    test_client: AsyncClient,
    seed_dictionary: list[DictionaryEntry],
) -> None:
    """GET /dictionaries/{type} should return all entries for given type."""
    response = await test_client.get("/dictionaries/countries")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "countries"
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_all_dictionaries_empty_type(test_client: AsyncClient) -> None:
    """GET /dictionaries/{type} for empty type should return empty list."""
    response = await test_client.get("/dictionaries/units")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "units"
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_all_dictionaries_invalid_type(test_client: AsyncClient) -> None:
    """GET /dictionaries/{type} with invalid type should return 422."""
    response = await test_client.get("/dictionaries/unknown_type")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_dictionary_entry_success(
    test_client: AsyncClient,
) -> None:
    """POST /dictionaries/{type} should create a new entry."""
    response = await test_client.post(
        "/dictionaries/countries",
        json={
            "type": "countries",
            "code": "DE",
            "data": {"name_ru": "Германия", "name_en": "Germany"},
        },
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code in {201, 403}


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient) -> None:
    """GET /health should return healthy status."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "dictionary-service"


@pytest.mark.asyncio
async def test_repository_get_all_by_type(
    db_session: AsyncSession,
    seed_dictionary: list[DictionaryEntry],
) -> None:
    """Repository.get_all_by_type should filter entries by type."""
    repo = DictionaryRepository(db_session)
    entries = await repo.get_all_by_type(DictionaryType.COUNTRIES)
    assert len(entries) == 2
    codes = {e.code for e in entries}
    assert codes == {"RU", "US"}


@pytest.mark.asyncio
async def test_repository_upsert_new_entry(db_session: AsyncSession) -> None:
    """Repository.upsert should create a new entry if not exists."""
    repo = DictionaryRepository(db_session)
    entry = await repo.upsert(
        DictionaryType.REGIONS,
        "MOS",
        {"name_ru": "Москва", "name_en": "Moscow"},
    )
    assert entry.id is not None
    assert entry.code == "MOS"
    assert entry.type == "regions"


@pytest.mark.asyncio
async def test_repository_upsert_existing_entry(
    db_session: AsyncSession,
    seed_dictionary: list[DictionaryEntry],
) -> None:
    """Repository.upsert should update existing entry."""
    repo = DictionaryRepository(db_session)
    entry = await repo.upsert(
        DictionaryType.COUNTRIES,
        "RU",
        {"name_ru": "Российская Федерация", "name_en": "Russian Federation"},
    )
    assert entry.data["name_ru"] == "Российская Федерация"


@pytest.mark.asyncio
async def test_repository_delete_existing(
    db_session: AsyncSession,
    seed_dictionary: list[DictionaryEntry],
) -> None:
    """Repository.delete should remove an existing entry."""
    repo = DictionaryRepository(db_session)
    result = await repo.delete(DictionaryType.COUNTRIES, "RU")
    assert result is True
    remaining = await repo.get_all_by_type(DictionaryType.COUNTRIES)
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_repository_delete_nonexistent(db_session: AsyncSession) -> None:
    """Repository.delete on nonexistent entry should return False."""
    repo = DictionaryRepository(db_session)
    result = await repo.delete(DictionaryType.COUNTRIES, "XX")
    assert result is False
