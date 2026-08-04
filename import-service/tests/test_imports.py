"""Integration tests for import-service."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.enums.import_status import ImportStatus
from src.enums.import_type import ImportType
from src.models.import_task import ImportTask
from src.repositories.import_repo import ImportRowRepository, ImportTaskRepository
from src.services.mapping_service import MappingService
from src.services.validation_service import RowValidator


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient) -> None:
    """GET /health should return healthy status."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "import-service"


@pytest.mark.asyncio
async def test_upload_csv_no_file(test_client: AsyncClient) -> None:
    """POST /imports/upload without file should return 422."""
    response = await test_client.post(
        "/imports/upload",
        data={"import_type": "PRODUCTS"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_task_not_found(test_client: AsyncClient) -> None:
    """GET /imports/{id} for unknown task should return 404."""
    response = await test_client.get(f"/imports/{uuid7()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_task_errors_empty(
    test_client: AsyncClient,
    seed_import_task: ImportTask,
) -> None:
    """GET /imports/{id}/errors for task without errors should return empty."""
    response = await test_client.get(
        f"/imports/{seed_import_task.id}/errors",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []


@pytest.mark.asyncio
async def test_repository_create_task(db_session: AsyncSession) -> None:
    """ImportTaskRepository.create_task should create and return a task."""
    repo = ImportTaskRepository(db_session)
    task = await repo.create_task(
        {
            "seller_id": uuid7(),
            "import_type": ImportType.PRODUCTS,
            "file_name": "products.csv",
            "file_path": "/tmp/products.csv",
        }
    )
    assert task.status == ImportStatus.PENDING.value
    assert task.file_name == "products.csv"


@pytest.mark.asyncio
async def test_repository_get_task(db_session: AsyncSession) -> None:
    """ImportTaskRepository.get_task should retrieve a task by ID."""
    repo = ImportTaskRepository(db_session)
    task = await repo.create_task(
        {
            "seller_id": uuid7(),
            "import_type": ImportType.PRICES,
            "file_name": "prices.csv",
            "file_path": "/tmp/prices.csv",
        }
    )
    retrieved = await repo.get_task(task.id)
    assert retrieved is not None
    assert retrieved.id == task.id


@pytest.mark.asyncio
async def test_repository_update_status(db_session: AsyncSession) -> None:
    """ImportTaskRepository.update_status should change status."""
    repo = ImportTaskRepository(db_session)
    task = await repo.create_task(
        {
            "seller_id": uuid7(),
            "import_type": ImportType.INVENTORY,
            "file_name": "stock.csv",
            "file_path": "/tmp/stock.csv",
        }
    )
    updated = await repo.update_status(task.id, ImportStatus.VALIDATING)
    assert updated is not None
    assert updated.status == ImportStatus.VALIDATING.value


@pytest.mark.asyncio
async def test_repository_update_progress(db_session: AsyncSession) -> None:
    """ImportTaskRepository.update_progress should update counters."""
    repo = ImportTaskRepository(db_session)
    task = await repo.create_task(
        {
            "seller_id": uuid7(),
            "import_type": ImportType.PRODUCTS,
            "file_name": "items.csv",
            "file_path": "/tmp/items.csv",
        }
    )
    await repo.update_progress(task.id, processed=42, total=100, errors=3)
    updated = await repo.get_task(task.id)
    assert updated is not None
    assert updated.processed_rows == 42
    assert updated.total_rows == 100
    assert updated.error_rows == 3


@pytest.mark.asyncio
async def test_row_repository_bulk_insert(db_session: AsyncSession) -> None:
    """ImportRowRepository.bulk_insert_rows should insert multiple rows."""
    task_repo = ImportTaskRepository(db_session)
    task = await task_repo.create_task(
        {
            "seller_id": uuid7(),
            "import_type": ImportType.PRODUCTS,
            "file_name": "bulk.csv",
            "file_path": "/tmp/bulk.csv",
        }
    )

    row_repo = ImportRowRepository(db_session)
    rows = [
        {
            "task_id": task.id,
            "row_number": 1,
            "row_data": {"name": "Product A", "price": "99.99"},
            "is_valid": True,
        },
        {
            "task_id": task.id,
            "row_number": 2,
            "row_data": {"name": "", "price": "invalid"},
            "error_description": {"field": "name", "code": "REQUIRED"},
            "is_valid": False,
        },
    ]
    await row_repo.bulk_insert_rows(rows)


@pytest.mark.asyncio
async def test_mapping_service_auto_map() -> None:
    """MappingService.auto_map should match columns by name."""
    service = MappingService()
    headers = ["Product Name", "Price", "Description", "SKU"]
    mapping = service.auto_map(headers, ImportType.PRODUCTS)
    assert isinstance(mapping, dict)
    assert len(mapping) > 0


@pytest.mark.asyncio
async def test_mapping_service_validate_missing_required() -> None:
    """MappingService.validate_mapping should detect missing required fields."""
    service = MappingService()
    mapping = {"col_a": "description"}
    missing = service.validate_mapping(mapping, ImportType.PRODUCTS)
    assert len(missing) > 0
    assert any("name" in m.lower() for m in missing)


@pytest.mark.asyncio
async def test_validation_service_rejects_invalid_rows() -> None:
    """RowValidator should accumulate all errors."""
    validator = RowValidator()
    rows = [
        {"name": "", "price": "-10", "category_id": str(uuid7())},
        {"name": "OK", "price": "not-a-number", "category_id": str(uuid7())},
    ]
    from src.services.import_strategy import ProductsImport

    strategy = ProductsImport()
    valid, errors = validator.validate_rows(rows, ImportType.PRODUCTS, strategy)
    assert len(errors) == 2
    assert len(valid) == 0
