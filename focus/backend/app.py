from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


_STATUS_TO_CODE = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
}


def _error_payload(
    *,
    code: str,
    message: str,
    details: object | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    code = _STATUS_TO_CODE.get(exc.status_code, "http_error")

    if isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = "Request failed"
        details = exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code=code, message=message, details=details),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        {"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="validation_error",
            message="Validation failed",
            details=details,
        ),
    )


app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(focus_router, prefix="/focus", tags=["focus"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

# Base.metadata.create_all(bind=engine)
