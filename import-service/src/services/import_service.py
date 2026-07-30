import csv
import io
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.http_client import CatalogClient, DictionaryClient
from src.engines.rabbitmq import ImportPublisher
from src.enums.import_status import IMPORT_STATE_MACHINE, ImportStatus
from src.enums.import_type import ImportType
from src.exceptions import NotFoundError
from src.models.import_row import ImportRow
from src.models.import_task import ImportTask
from src.patterns.file_storage_registry import FileStorageRegistry
from src.patterns.import_registry import ImportStrategyRegistry
from src.patterns.product_from_row_builder import ProductFromRowBuilder
from src.repositories.import_repo import ImportRowRepository, ImportTaskRepository
from src.services.mapping_service import MappingService
from src.services.validation_service import RowValidator

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(
        self,
        file_storage: FileStorageRegistry,
        strategy_registry: ImportStrategyRegistry,
        publisher: ImportPublisher,
        catalog_client: CatalogClient,
        dict_client: DictionaryClient,
        task_repo: ImportTaskRepository,
        row_repo: ImportRowRepository,
    ) -> None:
        self._file_storage = file_storage
        self._strategy_registry = strategy_registry
        self._publisher = publisher
        self._catalog_client = catalog_client
        self._dict_client = dict_client
        self._task_repo = task_repo
        self._row_repo = row_repo

    async def create_task(
        self,
        *,
        session: AsyncSession,
        seller_id: uuid.UUID,
        import_type: str,
        file_name: str,
        content: bytes,
    ) -> ImportTask:
        file_path = await self._file_storage.backend.save(
            content, f"{seller_id}/{file_name}"
        )
        task = await self._task_repo.create_task(
            session,
            {
                "seller_id": seller_id,
                "import_type": import_type,
                "file_name": file_name,
                "file_path": file_path,
                "status": ImportStatus.PENDING,
            },
        )
        return task

    async def _transition_status(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
        new_status: ImportStatus,
        **extra: object,
    ) -> ImportTask | None:
        """Validate and apply an import task status transition.

        Import tasks are advanced by background workers with no HTTP
        caller to surface a conflict to, so an invalid transition is
        logged and skipped rather than raised.
        """
        task = await self._task_repo.get_task(session, task_id)
        if task is None:
            return None

        current_status = ImportStatus(task.status)
        if not IMPORT_STATE_MACHINE.can_transition(current_status, new_status):
            logger.warning(
                "Skipping invalid import task status transition %s -> %s for task %s",
                current_status,
                new_status,
                task_id,
            )
            return task

        return await self._task_repo.update_status(
            session, task_id, new_status, **extra
        )

    async def validate_csv(self, *, session: AsyncSession, task_id: uuid.UUID) -> None:

        task = await self._task_repo.get_task(session, task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")

        await self._transition_status(session, task_id, ImportStatus.VALIDATING)

        strategy = self._strategy_registry.get(ImportType(task.import_type))

        content = await self._file_storage.backend.read(task.file_path)
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        headers = list(reader.fieldnames or [])
        mapping = MappingService.auto_map(headers, task.import_type)

        rows: list[dict[str, Any]] = []
        row_number = 0
        for row in reader:
            row_number += 1
            mapped = MappingService.apply_mapping(row, mapping)
            rows.append({"row_number": row_number, "data": mapped})

        validator = RowValidator()
        valid_rows, error_rows = validator.validate_rows(
            rows, task.import_type, strategy
        )

        row_records: list[dict[str, Any]] = []
        for item in valid_rows:
            row_records.append(
                {
                    "task_id": task_id,
                    "row_number": item["row_number"],
                    "row_data": item["data"],
                    "is_valid": True,
                }
            )
        for item in error_rows:
            row_records.append(
                {
                    "task_id": task_id,
                    "row_number": item["row_number"],
                    "row_data": item["data"],
                    "error_description": item["errors"],
                    "is_valid": False,
                }
            )

        await self._row_repo.bulk_insert_rows(session, row_records)

        total_rows = len(rows)
        error_count = len(error_rows)
        await self._task_repo.update_progress(
            session,
            task_id,
            processed=len(valid_rows),
            total=total_rows,
            errors=error_count,
        )

        if error_rows:
            await self._transition_status(
                session,
                task_id,
                ImportStatus.FAILED,
                error_details={"message": f"{error_count} rows failed validation"},
            )
        else:
            await self._transition_status(session, task_id, ImportStatus.PROCESSING)

    async def process_rows(self, *, session: AsyncSession, task_id: uuid.UUID) -> None:

        task = await self._task_repo.get_task(session, task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")

        rows = await self._row_repo.get_rows_by_task(session, task_id)
        valid_rows = [r for r in rows if r.is_valid]

        products: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for row in valid_rows:
            try:
                product = ProductFromRowBuilder.build(row.row_data)
                products.append(product)
            except Exception as exc:
                errors.append({"row": row.row_number, "error": str(exc)})

        products_created = 0
        if products:
            try:
                result = await self._catalog_client.create_products(products)
                products_created = result.get("created", len(products))
            except Exception as exc:
                await self._publisher.publish_import_failed(
                    {"task_id": str(task_id), "error": str(exc)}
                )
                await self._transition_status(
                    session,
                    task_id,
                    ImportStatus.FAILED,
                    error_details={"message": str(exc)},
                )
                return

        await self._task_repo.update_progress(
            session,
            task_id,
            processed=task.processed_rows + products_created,
            total=task.total_rows,
            errors=task.error_rows + len(errors),
        )

        await self._publisher.publish_import_completed(
            {
                "task_id": str(task_id),
                "import_type": task.import_type,
                "products_created": products_created,
                "errors": errors,
            }
        )

        await self._transition_status(session, task_id, ImportStatus.COMPLETED)

    async def get_task_status(
        self, *, session: AsyncSession, task_id: uuid.UUID
    ) -> ImportTask | None:
        return await self._task_repo.get_task(session, task_id)

    async def get_task_errors(
        self, *, session: AsyncSession, task_id: uuid.UUID, offset: int, limit: int
    ) -> list[ImportRow]:
        return await self._row_repo.get_task_errors(session, task_id, offset, limit)
