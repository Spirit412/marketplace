"""Tests for scheduler service — jobs and endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from src.schemes.response.job import JobList, JobStatus, TriggerResponse
from src.services.cache_warmup_job import cache_warmup_job
from src.services.cancel_unpaid_orders_job import cancel_unpaid_orders_job
from src.services.cart_cleanup_job import cart_cleanup_job
from src.services.daily_report_job import daily_report_job
from src.services.inventory_alert_job import inventory_alert_job


class TestHealthEndpoint:
    async def test_health_ok(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "scheduler-service"
        assert "checkers" in data


class TestJobsEndpoint:
    async def test_list_jobs_requires_auth(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/jobs")
        assert response.status_code == 403


class TestJobSchemas:
    def test_job_status_schema(self) -> None:
        job = JobStatus(
            id="cancel_unpaid_orders",
            name="Cancel Unpaid Orders",
            schedule="*/5 * * * *",
        )
        assert job.id == "cancel_unpaid_orders"
        assert job.is_running is False

    def test_job_list_schema(self) -> None:
        jobs = [
            JobStatus(id="j1", name="Job 1", schedule="*/5 * * * *"),
            JobStatus(id="j2", name="Job 2", schedule="0 * * * *"),
        ]
        job_list = JobList(jobs=jobs, total=2)
        assert job_list.total == 2
        assert len(job_list.jobs) == 2

    def test_trigger_response_schema(self) -> None:
        resp = TriggerResponse(job_id="cancel_unpaid_orders", run_id="run-123")
        assert resp.job_id == "cancel_unpaid_orders"
        assert resp.status == "accepted"


class TestJobFunctionsExist:
    """Smoke test — verify all job functions are callable."""

    def test_cancel_unpaid_orders_exists(self) -> None:
        assert callable(cancel_unpaid_orders_job)

    def test_daily_report_exists(self) -> None:
        assert callable(daily_report_job)

    def test_cache_warmup_exists(self) -> None:
        assert callable(cache_warmup_job)

    def test_cart_cleanup_exists(self) -> None:
        assert callable(cart_cleanup_job)

    def test_inventory_alert_exists(self) -> None:
        assert callable(inventory_alert_job)
