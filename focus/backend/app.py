from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .settings import settings, enforce_security_config
from .routers.health import router as health_router
from .routers.tasks import router as tasks_router
from .routers.inbox import router as inbox_router
from .routers.focus import router as focus_router
from .routers.life import router as life_router
from .routers.telegram import router as telegram_router
from .services.reminders import send_due_reminders_once
from .auth import (
    auth_backend,
    fastapi_users,
    UserRead,
    UserCreate,
    UserUpdate,
)


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
# apscheduler на INFO пишет две строки на каждый tick (каждые 30с) — это заваливает логи
logging.getLogger("apscheduler").setLevel(logging.WARNING)
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
    # В prod небезопасный конфиг (дефолтный JWT-секрет / пустой CORS) валит старт;
    # в dev — только warning. См. settings.enforce_security_config.
    enforce_security_config(settings)

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

allowed_origins = [
    origin.strip() for origin in settings.web_cors_origins.split(",") if origin.strip()
]
if not allowed_origins:
    log.warning(
        "WEB_CORS_ORIGINS пуст — CORS открыт для всех источников (allow_origins=*); "
        "допустимо только в dev"
    )
    allowed_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(focus_router, prefix="/focus", tags=["focus"])
app.include_router(life_router, prefix="/life", tags=["life"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

WEB_DIST_PATH = Path(__file__).resolve().parents[1] / "web" / "dist"
if WEB_DIST_PATH.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIST_PATH), html=True), name="web")

    @app.get("/", include_in_schema=False)
    async def root_redirect_to_web() -> RedirectResponse:
        return RedirectResponse(url="/web/")

# Base.metadata.create_all(bind=engine)
