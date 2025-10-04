from fastapi import FastAPI
from .routers.health import router as health_router
from .routers.tasks import router as tasks_router
from .routers.inbox import router as inbox_router
from .routers.focus import router as focus_router
from focus.backend.database.models import Base
from focus.backend.database.core import engine

app = FastAPI(title="FocusMate (MVP)")
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(focus_router, prefix="/focus", tags=["focus"])

# Base.metadata.create_all(bind=engine)