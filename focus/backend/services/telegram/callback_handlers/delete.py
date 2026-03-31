from __future__ import annotations

from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.api import answer_callback_query, send_or_edit
from focus.backend.services.telegram.commands.delete_pick import render_delete_pick
from focus.backend.services.telegram.screens.today_screen import (
    refresh_today_screen,
    resolve_screen_message_id,
)
from focus.backend.services.telegram.types import TelegramContext


async def handle_today_delete_pick(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    text, kb = await render_delete_pick(ctx)
    target_message_id = resolve_screen_message_id(ctx, message_id)
    new_message_id = await send_or_edit(
        ctx.chat_id, target_message_id, text, reply_markup=kb
    )
    if new_message_id and new_message_id != ctx.telegram_user.screen_message_id:
        ctx.telegram_user.screen_message_id = new_message_id
        await ctx.db.commit()
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
            [{"text": "⬅️ Назад", "callback_data": "today_refresh"}],
        ]
    }

    target_message_id = resolve_screen_message_id(ctx, message_id)
    new_message_id = await send_or_edit(
        ctx.chat_id, target_message_id, text, reply_markup=kb
    )
    if new_message_id and new_message_id != ctx.telegram_user.screen_message_id:
        ctx.telegram_user.screen_message_id = new_message_id
        await ctx.db.commit()
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

    await refresh_today_screen(ctx, preferred_message_id=message_id)
    await answer_callback_query(callback_query_id, text="Удалено 🗑️")


async def handle_delete_no(
    ctx: TelegramContext,
    *,
    callback_query_id: str | None,
    message_id: int | None,
) -> None:
    await refresh_today_screen(ctx, preferred_message_id=message_id)
    await answer_callback_query(callback_query_id)
