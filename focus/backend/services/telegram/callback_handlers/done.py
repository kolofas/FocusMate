from __future__ import annotations

from focus.backend.database.enums import TaskStatus
from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.tasks import change_task_status
from focus.backend.services.telegram.api import answer_callback_query, edit_message_text
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.commands.done_pick import render_done_pick
from focus.backend.services.telegram.types import TelegramContext


async def handle_today_done_pick(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    text, kb = await render_done_pick(ctx)
    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id)


async def handle_done_task(
    ctx: TelegramContext,
    *,
    task_id: int,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)

    if not task:
        await answer_callback_query(
            callback_query_id, text=f"Не нашёл задачу id={task_id}", show_alert=True
        )
        return

    if task.status == TaskStatus.DONE.value:
        await answer_callback_query(
            callback_query_id, text="Уже закрыта ✅", show_alert=False
        )
        return

    await change_task_status(task, TaskStatus.DONE)
    await ctx.db.commit()

    text, kb = await render_today(ctx, args=[])
    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)

    await answer_callback_query(callback_query_id, text="Готово ✅", show_alert=False)
