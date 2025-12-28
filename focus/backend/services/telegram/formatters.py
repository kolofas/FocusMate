from __future__ import annotations

from typing import Protocol, Sequence

from focus.backend.database.enums import TaskStatus
from focus.backend.services.telegram.consts import STATUS_EMOJI


class TaskLike(Protocol):
    id: int
    title: str
    status: str | TaskStatus
    tags: Sequence[str] | None


def _status_value(status: str | TaskStatus) -> str:
    return status.value if isinstance(status, TaskStatus) else status


def _format_tags(tags: Sequence[str] | None) -> str:
    if not tags:
        return ""
    cleaned: list[str] = []
    for t in tags:
        t = (t or "").strip()
        if not t:
            continue
        if t.startswith("#"):
            t = t[1:]
        if not t:
            continue
        cleaned.append(f"#{t}")
    return " ".join(cleaned)


def format_task_line(task: TaskLike) -> str:
    """
    Строка задачи для Telegram:
    '🧭 [id:4] купить молоко [planned] #home'
    """
    status = _status_value(task.status)
    emoji = STATUS_EMOJI.get(status, "•")
    base = f"{emoji} [id:{task.id}] {task.title} [{status}]"
    tags_part = _format_tags(task.tags)

    return f"{base} {tags_part}".rstrip()
