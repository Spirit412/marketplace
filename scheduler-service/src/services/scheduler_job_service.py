"""Query and trigger APScheduler's registered jobs."""

from typing import Any

from src.core.datatype import uuid7
from src.exceptions import NotFoundError
from src.schemes.response.job import JobList, JobStatus, TriggerResponse


class SchedulerJobService:
    def __init__(self, scheduler: Any) -> None:
        self._scheduler = scheduler

    def list_jobs(self) -> JobList:
        jobs = [
            JobStatus(
                id=job.id,
                name=job.name,
                schedule=str(job.trigger) if job.trigger else "manual",
                next_run=job.next_run_time,
                last_run=None,
                is_running=job.next_run_time is not None,
            )
            for job in self._scheduler.get_jobs()
        ]
        return JobList(jobs=jobs, total=len(jobs))

    async def trigger(self, job_id: str) -> TriggerResponse:
        """Run a job's function immediately, outside its normal schedule.

        A failure inside the job function itself propagates as-is -- the
        app-wide unhandled-exception handler logs it and returns a generic
        500, same as it would for a bug in any request handler. It isn't
        wrapped into a domain error here, since there's no more specific
        recovery this layer could do with it.
        """
        job = self._scheduler.get_job(job_id)
        if job is None:
            raise NotFoundError(f"Job {job_id} not found")

        run_id = str(uuid7())
        await job.func()
        return TriggerResponse(job_id=job_id, run_id=run_id)
