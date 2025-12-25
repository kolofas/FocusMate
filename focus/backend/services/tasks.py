# backend/tasks.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import models
from focus.backend.services import ParsedInbox
from focus.backend.database.enums import TaskSource, TaskStatus
from ..utils.datetime import to_utc
from ..settings import settings
from focus.backend.utils.tags import canonicalize_tags


MAX_DESC_LEN = settings.max_description_length  # единая константа


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
