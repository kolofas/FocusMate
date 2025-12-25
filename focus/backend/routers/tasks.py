# focus/backend/routers/tasks.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy import desc, func, asc
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database.core import get_db
from ..database import models
from ..repositories.tasks_repo import TaskRepo
from ..schemas import TaskRead, TaskCreate, TaskUpdate, StatusChange
from focus.backend.database.enums import TaskStatus
from ..schemas.task_queries import TaskListQuery
from ..utils.tags import canonicalize_tags
from ..settings import settings
from ..services.tasks import change_task_status

router = APIRouter()

ALLOWED_STATUS = {s.value for s in TaskStatus}
ALLOWED_ORDER = {"created_at", "deadline"}
ALLOWED_DIR = {"asc", "desc"}
MAX_DESC_LEN = settings.max_description_length


def apply_filters(stmt, status: Optional[str], q: Optional[str]):
    if status:
        if status not in ALLOWED_STATUS:
            raise HTTPException(400, detail="Invalid status")
        stmt = stmt.where(models.Task.status == status)
    if q:
        # кросс-диалектный case-insensitive через lower()+like
        stmt = stmt.where(func.lower(models.Task.title).like(f"%{q.lower()}%"))
    return stmt


def apply_ordering(stmt, order_by: str, direction: str):
    if order_by not in ALLOWED_ORDER or direction not in ALLOWED_DIR:
        raise HTTPException(400, detail="Invalid order/dir")
    column = getattr(models.Task, order_by)
    return stmt.order_by(asc(column) if direction == "asc" else desc(column))


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
):
    if status and status not in ALLOWED_STATUS:
        raise HTTPException(400, detail="Invalid status")
    if order_by not in ALLOWED_ORDER or direction not in ALLOWED_DIR:
        raise HTTPException(400, detail="Invalid order/dir")

    query = TaskListQuery(
        user_id=user_id,
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
    obj = await db.get(models.Task, task_id)
    if not obj:
        raise HTTPException(404, detail="Task not found")
    return obj


@router.post("/", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate, response: Response, db: AsyncSession = Depends(get_db)
):
    obj = models.Task(
        title=(payload.title or "").strip(),
        description=((payload.description or "")[:MAX_DESC_LEN]),
        source=(payload.source or "manual"),
        deadline=payload.deadline,
        tags=canonicalize_tags(payload.tags),
        status=TaskStatus.INBOX.value,
    )
    try:
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
    except Exception:
        await db.rollback()
        raise
    response.headers["Location"] = f"/tasks/{obj.id}"
    return obj


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await db.get(models.Task, task_id)
    if not obj:
        raise HTTPException(404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)

    # статус изменяем отдельным эндпоинтом — игнорируем здесь, если вдруг появится
    data.pop("status", None)

    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"][:MAX_DESC_LEN]
    if "tags" in data and data["tags"] is not None:
        data["tags"] = canonicalize_tags(data["tags"])

    for field, value in data.items():
        setattr(obj, field, value)

    try:
        await db.commit()
        await db.refresh(obj)
    except Exception:
        await db.rollback()
        raise
    return obj


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(models.Task, task_id)
    if not obj:
        raise HTTPException(404, detail="Task not found")
    try:
        await db.delete(obj)
        await db.commit()
    except Exception:
        await db.rollback()
        raise


@router.post("/{task_id}/status", response_model=TaskRead)
async def change_status(
    task_id: int, payload: StatusChange, db: AsyncSession = Depends(get_db)
):
    obj = await db.get(models.Task, task_id)
    if not obj:
        raise HTTPException(404, detail="Task not found")

    await change_task_status(obj, payload.status)

    try:
        await db.commit()
        await db.refresh(obj)
    except Exception:
        await db.rollback()
        raise
    return obj
