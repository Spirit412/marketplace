import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from rodi import Container

from src.config.settings import settings
from src.services.cache_warmup_job import cache_warmup_job
from src.services.cancel_unpaid_orders_job import cancel_unpaid_orders_job
from src.services.cart_cleanup_job import cart_cleanup_job
from src.services.daily_report_job import daily_report_job
from src.services.inventory_alert_job import inventory_alert_job

logger = logging.getLogger(__name__)

container = Container()

_scheduler: AsyncIOScheduler | None = None

JOB_REGISTRY = {
    "cancel_unpaid_orders": (cancel_unpaid_orders_job, settings.CANCEL_UNPAID_ORDERS_CRON, "Cancel unpaid orders"),
    "daily_report": (daily_report_job, settings.DAILY_REPORT_CRON, "Daily seller report"),
    "cache_warmup": (cache_warmup_job, settings.CACHE_WARMUP_CRON, "Cache warmup"),
    "cart_cleanup": (cart_cleanup_job, settings.CART_CLEANUP_CRON, "Cart cleanup"),
    "inventory_alert": (inventory_alert_job, settings.INVENTORY_ALERT_CRON, "Inventory low-stock alert"),
}


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    return _scheduler


def set_scheduler(scheduler: AsyncIOScheduler) -> None:
    global _scheduler
    _scheduler = scheduler


def start_scheduler() -> AsyncIOScheduler:
    """Register all recurring jobs and start the scheduler. Called once from lifespan."""
    scheduler = get_scheduler()
    for job_id, (func, cron_expr, name) in JOB_REGISTRY.items():
        scheduler.add_job(
            func,
            trigger=CronTrigger.from_crontab(cron_expr, timezone=settings.TIMEZONE),
            id=job_id,
            name=name,
            replace_existing=True,
        )
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(JOB_REGISTRY))
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
