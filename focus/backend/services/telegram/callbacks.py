from __future__ import annotations
import logging

from focus.backend.database.enums import TaskStatus
from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.commands.done_pick import render_done_pick
from focus.backend.services.telegram.types import TelegramContext
from focus.backend.services.telegram.api import (
    answer_callback_query,
    send_reply,
    edit_message_text,
)
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.commands.tasks import command_tasks

log = logging.getLogger(__name__)


async def handle_callback(
    data: str,
    ctx: TelegramContext,
    callback_query_id: str | None,
    message_id: int | None,
) -> bool:
    """
    Returns True if handled.
    """
    await answer_callback_query(callback_query_id)

    if data in ("today_refresh", "today_replan"):
        text, kb = await render_today(ctx, args=[])
        log.info("tg.edit: chat_id=%s message_id=%s", ctx.chat_id, message_id)
        await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
        return True

    if data == "tasks_planned":
        await command_tasks(ctx, args=["planned"])
        return True

    if data == "task_add":
        await send_reply(
            ctx.chat_id,
            "Ок. Просто напиши текст задачи следующим сообщением — я добавлю в инбокс.\n\n"
            "Пример: `Купить воду`",
            parse_mode="Markdown",
        )
        return True

    if data == "today_done_pick":
        text, kb = await render_done_pick(ctx)
        await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
        return True

    if data.startswith("done:"):
        try:
            task_id = int(data.split(":", 1)[1])
        except ValueError:
            await answer_callback_query(
                callback_query_id, text="Некорректный id", show_alert=True
            )
            return True

        repo = TaskRepo(ctx.db)
        task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
        if not task:
            await answer_callback_query(
                callback_query_id, text=f"Не нашёл задачу id={task_id}", show_alert=True
            )
            return True

        if task.status == TaskStatus.DONE.value:
            await answer_callback_query(
                callback_query_id, text="Уже закрыта ✅", show_alert=False
            )
            return True

        await change_task_status(task, TaskStatus.DONE)
        await ctx.db.commit()

        text, kb = await render_today(ctx, args=[])
        await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)

        await answer_callback_query(
            callback_query_id, text="Готово ✅", show_alert=False
        )
        return True

    return False
