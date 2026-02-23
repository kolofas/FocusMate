from __future__ import annotations

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.api import answer_callback_query, edit_message_text
from focus.backend.services.telegram.commands.delete_pick import render_delete_pick
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.types import TelegramContext


async def handle_today_delete_pick(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    text, kb = await render_delete_pick(ctx)
    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id)


async def handle_delete_confirm(
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
            callback_query_id, text="Не нашёл задачу", show_alert=True
        )
        return

    text = f"Точно удалить?\n🗑️ [id:{task.id}] {task.title}"
    kb = {
        "inline_keyboard": [
            [
                {"text": "✅ Удалить", "callback_data": f"del_yes:{task_id}"},
                {"text": "❌ Отмена", "callback_data": "del_no"},
            ],
            [{"text": "⬅️ Назад", "callback_data": "today_delete_pick"}],
        ]
    }

    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id)


async def handle_delete_yes(
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
            callback_query_id, text="Уже удалена/не найдена", show_alert=True
        )
        return

    await repo.delete(task)
    await ctx.db.commit()

    text, kb = await render_today(ctx, args=[])
    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id, text="Удалено 🗑️")


async def handle_delete_no(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    text, kb = await render_today(ctx, args=[])
    await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    await answer_callback_query(callback_query_id)
