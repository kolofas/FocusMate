from __future__ import annotations

from focus.backend.database.enums import TaskStatus

HELP_TEXT = (
    "🌟 FocusMate — быстрый инбокс задач\n\n"
    "Команды:\n"
    "/today            — фокус-лист на сегодня\n"
    "/tasks            — последние задачи (с фильтрами)\n"
    "/done <id>        — отметить задачу выполненной\n"
    "/status <id> <st> — изменить статус (inbox|planned|done|snoozed)\n"
    "/d <id> — alias для /done\n"
    "/s <id> <st> — alias для /status\n"
    "/help             — эта справка\n\n"
    "Фильтры для /tasks:\n"
    "  /tasks planned         — только planned\n"
    "  /tasks #work           — по тегу\n"
    "  /tasks 10 planned      — лимит + статус\n"
    "  /tasks planned #work   — комбинированно\n"
    "  /tasks planned all     — все задачи этого статуса\n\n"
    "Добавить задачу: просто напиши текст.\n"
    "Примеры:\n"
    "• купить молоко 2025-12-31\n"
    "• починить баг #urgent"
)


STATUS_EMOJI = {
    TaskStatus.INBOX.value: "📥",
    TaskStatus.PLANNED.value: "🧭",
    TaskStatus.DONE.value: "✅",
    TaskStatus.SNOOZED.value: "⏸️",
}


_ALLOWED_STATUS = {s.value for s in TaskStatus}
