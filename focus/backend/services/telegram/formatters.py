from focus.backend.database import models
from focus.backend.services.telegram.consts import STATUS_EMOJI


def format_task_line(task: models.Task) -> str:
    """
    Строка задачи для Telegram:
    '🧭 [id:4] купить молоко [planned] #home'
    """
    emoji = STATUS_EMOJI.get(task.status, "•")
    base = f"{emoji} [id:{task.id}] {task.title} [{task.status}]"
    if task.tags:
        tags_part = " ".join(f"#{t}" for t in task.tags)
        return f"{base} {tags_part}"
    return base
