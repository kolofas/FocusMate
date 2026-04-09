from fastapi import FastAPI
import logging
import os
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .settings import settings
from .routers.health import router as health_router
from .routers.tasks import router as tasks_router
from .routers.inbox import router as inbox_router
from .routers.focus import router as focus_router
from .routers.telegram import router as telegram_router
from .services.reminders import send_due_reminders_once


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)


def _is_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


async def _run_reminder_tick() -> None:
    try:
        await send_due_reminders_once()
    except Exception:
        log.exception("reminders.tick failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler: AsyncIOScheduler | None = None

    if settings.reminders_worker_enabled and not _is_pytest():
        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(
            _run_reminder_tick,
            trigger="interval",
            seconds=settings.reminders_poll_seconds,
            id="reminders_tick",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        scheduler.start()
        log.info(
            "reminders.worker started interval=%ss batch=%s",
            settings.reminders_poll_seconds,
            settings.reminders_batch_size,
        )

    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title="FocusMate (MVP)", lifespan=lifespan)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(focus_router, prefix="/focus", tags=["focus"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

# Base.metadata.create_all(bind=engine)
