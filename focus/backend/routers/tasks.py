# focus/backend/routers/tasks.py
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from ..repositories.tasks_repo import TaskRepo
from ..schemas import TaskRead, TaskCreate, TaskUpdate, StatusChange
from focus.backend.database.enums import TaskStatus
from ..schemas.task_queries import TaskListQuery
from ..services import tasks
from ..services.tasks import change_task_status
from ..services.planner import plan_today
from ..auth import current_active_user_optional, resolve_scope_user_id
from focus.backend.database import models

router = APIRouter()

ALLOWED_STATUS = {s.value for s in TaskStatus}
ALLOWED_ORDER = {"created_at", "deadline"}
ALLOWED_DIR = {"asc", "desc"}


@router.get("/", response_model=List[TaskRead])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="inbox|planned|done|snoozed"),
    q: Optional[str] = Query(
        None, description="substring match in title (case-insensitive)"
    ),
    tag: Optional[str] = Query(None, description="filter by #tag without #"),
    order_by: str = Query("created_at"),
    direction: str = Query("desc", alias="dir"),
    user_id: int | None = Query(None, description="filter by user"),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    if status and status not in ALLOWED_STATUS:
        raise HTTPException(400, detail="Invalid status")
    if order_by not in ALLOWED_ORDER or direction not in ALLOWED_DIR:
        raise HTTPException(400, detail="Invalid order/dir")

    resolved_user_id = resolve_scope_user_id(current_user, user_id)

    query = TaskListQuery(
        user_id=resolved_user_id,
        limit=limit,
        offset=offset,
        status=status,
        q=q,
        tag=tag,
        order_by=order_by,
        direction=direction,
    )

    repo = TaskRepo(db)
    return await repo.list_tasks(query)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    repo = TaskRepo(db)
    obj = await repo.get_by_id(task_id)
    if not obj:
        raise HTTPException(404, detail="Task not found")
    return obj


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, None)
    try:
        obj = await tasks.create_task(db, payload, user_id=resolved_user_id)
    except Exception:
        await db.rollback()
        raise

    response.headers["Location"] = f"/tasks/{obj.id}"
    return obj


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, None)
    try:
        obj = await tasks.update_task(db, task_id, payload, user_id=resolved_user_id)
    except Exception:
        await db.rollback()
        raise

    if not obj:
        raise HTTPException(404, detail="Task not found")
    return obj


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, None)
    try:
        ok = await tasks.delete_task(db, task_id, user_id=resolved_user_id)
    except Exception:
        await db.rollback()
        raise

    if not ok:
        raise HTTPException(404, detail="Task not found")


@router.post("/{task_id}/status", response_model=TaskRead)
async def change_status(
    task_id: int,
    payload: StatusChange,
    db: AsyncSession = Depends(get_db),
    current_user: models.WebUser | None = Depends(current_active_user_optional),
):
    resolved_user_id = resolve_scope_user_id(current_user, None)
    repo = TaskRepo(db)
    obj = (
        await repo.get_user_task(task_id=task_id, user_id=resolved_user_id)
        if resolved_user_id is not None
        else await repo.get_by_id(task_id)
    )
    if not obj:
        raise HTTPException(404, detail="Task not found")

    await change_task_status(obj, payload.status)

    try:
        await db.flush()
        await plan_today(db, user_id=obj.user_id, for_date=date.today())
        await db.commit()
        await db.refresh(obj)
    except Exception:
        await db.rollback()
        raise
    return obj
