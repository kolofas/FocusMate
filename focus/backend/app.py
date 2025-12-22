from fastapi import FastAPI
import logging
from .settings import settings
from .routers.health import router as health_router
from .routers.tasks import router as tasks_router
from .routers.inbox import router as inbox_router
from .routers.focus import router as focus_router
from .routers.telegram import router as telegram_router


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


app = FastAPI(title="FocusMate (MVP)")
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(focus_router, prefix="/focus", tags=["focus"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])

# Base.metadata.create_all(bind=engine)
