from __future__ import annotations

from typing import Protocol, Sequence

from focus.backend.database.enums import TaskStatus
from focus.backend.services.telegram.consts import STATUS_EMOJI


class TaskLike(Protocol):
    id: int
    title: str
    status: str | TaskStatus
    tags: Sequence[str] | None


def format_task_line(task: TaskLike) -> str:
    """
    Строка задачи для Telegram:
    '🧭 [id:4] купить молоко [planned] #home'
    """
    status = task.status.value if hasattr(task.status, "value") else task.status
    emoji = STATUS_EMOJI.get(status, "•")
    base = f"{emoji} [id:{task.id}] {task.title} [{status}]"
    if task.tags:
        tags_part = " ".join(f"#{t}" for t in task.tags)
        return f"{base} {tags_part}"
    return base
