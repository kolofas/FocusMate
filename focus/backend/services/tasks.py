# backend/tasks.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import models
from focus.backend.services import ParsedInbox
from focus.backend.database.enums import TaskSource, TaskStatus
from ..utils.datetime import to_utc
from ..settings import settings
from focus.backend.utils.tags import canonicalize_tags
from ..repositories.tasks_repo import TaskRepo
from ..schemas import TaskCreate, TaskUpdate

MAX_DESC_LEN = settings.max_description_length


async def create_task_from_parsed(
    db: AsyncSession,
    parsed: ParsedInbox,
    *,
    source: TaskSource,
    status: TaskStatus = TaskStatus.INBOX,
    raw_text: Optional[str] = None,
) -> models.Task:
    """
    Создаёт Task из ParsedInbox. Источник и статус приходят снаружи.
    Нормализует title/tags и переводит дедлайн в UTC.
    """
    title = (parsed.title or "").strip()
    if not title:
        raise ValueError("empty title")

    description = (raw_text or parsed.raw or "")[:MAX_DESC_LEN]

    deadline_utc = (
        to_utc(parsed.deadline_local)
        if getattr(parsed, "deadline_local", None)
        else None
    )

    tags = canonicalize_tags(parsed.tags or [])

    task = models.Task(
        title=title,
        description=description,
        source=source.value,
        status=status.value,
        deadline=deadline_utc,
        tags=tags,
    )

    db.add(task)
    await db.flush()
    return task


async def change_task_status(task: models.Task, new_status: TaskStatus) -> None:
    """
    Единое место смены статуса задачи.
    Сейчас просто присваивает строковое значение, но сюда можно будет
    добавить правила переходов (например, что из done нельзя в inbox).
    """
    value = new_status.value
    if task.status == value:
        return

    task.status = value


async def create_task(
    db: AsyncSession,
    payload: TaskCreate,
) -> models.Task:
    repo = TaskRepo(db)

    task = models.Task(
        title=(payload.title or "").strip(),
        description=((payload.description or "")[:MAX_DESC_LEN]),
        source=(payload.source or "manual"),
        deadline=payload.deadline,
        tags=canonicalize_tags(payload.tags),
        status=TaskStatus.INBOX.value,
    )

    repo.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    task_id: int,
    payload: TaskUpdate,
) -> models.Task | None:
    repo = TaskRepo(db)

    task = await repo.get_by_id(task_id)
    if not task:
        return None

    data = payload.model_dump(exclude_unset=True)
    data.pop("status", None)

    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"][:MAX_DESC_LEN]
    if "tags" in data and data["tags"] is not None:
        data["tags"] = canonicalize_tags(data["tags"])

    for field, value in data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task


async def delete_task(
    db: AsyncSession,
    task_id: int,
) -> bool:
    repo = TaskRepo(db)

    task = await repo.get_by_id(task_id)
    if not task:
        return False

    await repo.delete(task)
    await db.commit()
    return True
