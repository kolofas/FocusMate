from __future__ import annotations

from typing import Sequence


from focus.backend.repositories.tasks_repo import TaskRepo
from focus.backend.services.telegram.api import send_reply
from focus.backend.services.telegram.commands.today import render_today
from focus.backend.services.telegram.types import TelegramContext


async def command_delete(ctx: TelegramContext, args: Sequence[str]) -> None:
    """
    /del <id> - удалить задачу
    /rm <id> - алиас
    """
    if not args:
        await send_reply(ctx.chat_id, "Укажите id. Пример /del 12")
        return
    
    try:
        task_id = int(args[0])
    except ValueError:
        await send_reply(ctx.chat_id, "Некорректный id. Пример: /del 12")
        return
    
    repo = TaskRepo(ctx.db)
    task = await repo.get_user_task(task_id=task_id, user_id=ctx.telegram_user.id)
    if not task:
        await send_reply(ctx.chat_id, f"Не нашел зачу id={task_id}")
        return
    
    await repo.delete(task)
    await ctx.db.commit()

    text, kb = await render_today(ctx, args=[])
    await send_reply(ctx.chat_id, f"Удалено 🗑️\n\n{text}", reply_markup=kb)
