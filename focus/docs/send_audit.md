1. sendMessage
    /home/kolofas/projects/FocusMate/focus/backend/services/telegram/api.py
    строка 29: url = f"https://api.telegram.org/bot{token}/sendMessage"

2. bot.send
    
    focus/backend/routers/telegram.py:
    12  from ..services.telegram.inbox_flow import try_handle_command, process_inbox_text
    13: from ..services.telegram.api import send_reply
    14  from ..services.telegram.types import TelegramContext, TelegramMeta

    114      if result.get("duplicate"):
    115:         await send_reply(chat_id, "Это уже есть в инбоксе 👌")
    116      else:
    117:         await send_reply(chat_id, f"Добавил: {result.get('title')}")
    118  

    focus/backend/services/telegram/api.py:
    9  
    10: async def send_reply(
    11      chat_id: Optional[int],

    28  
    29:     url = f"https://api.telegram.org/bot{token}/sendMessage"
    30      payload: dict[str, Any] = {

    43      except Exception:
    44:         log.exception("Failed to send telegram message to chat_id=%s", chat_id)
    45  

    focus/backend/services/telegram/inbox_flow.py:
    14  
    15: from focus.backend.services.telegram.api import send_reply
    16  from focus.backend.services.telegram.commands import COMMAND_HANDLERS

    38      if cmd.startswith("/"):
    39:         await send_reply(ctx.chat_id, "Не знаю такую команду. Напиши /help")
    40          return True

    focus/backend/services/telegram/callback_handlers/add.py:
    2  
    3: from focus.backend.services.telegram.api import send_reply
    4  from focus.backend.services.telegram.types import TelegramContext

    7  async def handle_task_add(ctx: TelegramContext) -> None:
    8:     await send_reply(
    9          ctx.chat_id,

    focus/backend/services/telegram/commands/delete.py:
    6  from focus.backend.repositories.tasks_repo import TaskRepo
    7: from focus.backend.services.telegram.api import send_reply
    8  from focus.backend.services.telegram.commands.today import render_today

    17      if not args:
    18:         await send_reply(ctx.chat_id, "Укажите id. Пример /del 12")
    19          return

    23      except ValueError:
    24:         await send_reply(ctx.chat_id, "Некорректный id. Пример: /del 12")
    25          return

    29      if not task:
    30:         await send_reply(ctx.chat_id, f"Не нашел зачу id={task_id}")
    31          return

    36      text, kb = await render_today(ctx, args=[])
    37:     await send_reply(ctx.chat_id, f"Удалено 🗑️\n\n{text}", reply_markup=kb)

    focus/backend/services/telegram/commands/done.py:
    7  from focus.backend.services.tasks import change_task_status
    8: from focus.backend.services.telegram.api import send_reply
    9  from focus.backend.services.telegram.formatters import format_task_line

    28      if not args or not args[0].isdigit():
    29:         await send_reply(chat_id, "Использование: /done <id>")
    30          return

    37      if not task:
    38:         await send_reply(
    39              chat_id, f"Не нашёл задачу с id {task_id}. Попробуй /today или /tasks"

    44      if old_status == TaskStatus.DONE.value:
    45:         await send_reply(
    46              chat_id,

    56      next_line = await suggest_next_action_line(ctx)
    57:     await send_reply(chat_id, _build_done_reply(task, old_status, next_line))

    focus/backend/services/telegram/commands/help.py:
    2  
    3: from focus.backend.services.telegram.api import send_reply
    4  from focus.backend.services.telegram.consts import HELP_TEXT

    8  async def command_help(ctx: TelegramContext, args: Sequence[str]) -> None:
    9:     await send_reply(ctx.chat_id, HELP_TEXT)

    focus/backend/services/telegram/commands/status.py:
    4  from focus.backend.services.tasks import change_task_status
    5: from focus.backend.services.telegram.api import send_reply
    6  from focus.backend.services.telegram.formatters import format_task_line

    26      if task_id is None or status_raw is None:
    27:         await send_reply(
    28              chat_id, "Использование: /status <id> <inbox|planned|done|snoozed>"

    33      if not new_status:
    34:         await send_reply(
    35              chat_id, "Неизвестный статус. Используй: inbox | planned | done | snoozed"

    42      if not task:
    43:         await send_reply(
    44              chat_id, f"Не нашёл задачу с id {task_id}. Попробуй /today или /tasks"

    49      if before == new_status.value:
    50:         await send_reply(
    51              chat_id,

    59  
    60:     await send_reply(
    61          chat_id,

    focus/backend/services/telegram/commands/tasks.py:
    3  from focus.backend.repositories.tasks_repo import TaskRepo
    4: from focus.backend.services.telegram.api import send_reply
    5  from focus.backend.services.telegram.formatters import format_task_line

    36      if not tasks:
    37:         await send_reply(chat_id, "Задач пока нет.")
    38          return

    54  
    55:     await send_reply(chat_id, "\n".join(lines))

    focus/backend/services/telegram/commands/today.py:
    4  from focus.backend.services.focus import get_plan_today
    5: from focus.backend.services.telegram.api import send_reply
    6  from focus.backend.services.telegram.consts import STATUS_EMOJI

    74      text, kb = await render_today(ctx, args)
    75:     await send_reply(ctx.chat_id, text, reply_markup=kb)

3. answer
    23 results - 4 files

    focus/backend/services/telegram/api.py:
    46  
    47: async def answer_callback_query(
    48      callback_query_id: Optional[str],

    59  
    60:     url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    61      payload: dict[str, Any] = {

    71      except Exception:
    72:         log.exception("Failed to answer callback_query_id=%s", callback_query_id)
    73  

    focus/backend/services/telegram/callbacks.py:
        5  from focus.backend.services.telegram.api import (
        6:     answer_callback_query,
        7  )

    40              msg = "Без изменений" if data == "today_refresh" else "План уже оптимален"
    41:             await answer_callback_query(callback_query_id, text=msg)
    42          else:
    43:             await answer_callback_query(callback_query_id)
    44          return True

    55          except ValueError:
    56:             await answer_callback_query(
    57                  callback_query_id, text="Некорректный id", show_alert=True

    70          await handle_tasks_planned(ctx)
    71:         await answer_callback_query(callback_query_id)
    72          return True

    75          await handle_task_add(ctx)
    76:         await answer_callback_query(callback_query_id)
    77          return True

    88          except ValueError:
    89:             await answer_callback_query(callback_query_id, text="Некорректный id", show_alert=True)
    90              return True

    100          except ValueError:
    101:             await answer_callback_query(callback_query_id, text="Некорректный id", show_alert=True)
    102              return True

    focus/backend/services/telegram/callback_handlers/delete.py:
    3  from focus.backend.repositories.tasks_repo import TaskRepo
    4: from focus.backend.services.telegram.api import answer_callback_query, edit_message_text
    5  from focus.backend.services.telegram.commands.delete_pick import render_delete_pick

    17      await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    18:     await answer_callback_query(callback_query_id)
    19  

    30      if not task:
    31:         await answer_callback_query(callback_query_id, text="Не нашёл задачу", show_alert=True)
    32          return

    45      await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    46:     await answer_callback_query(callback_query_id)
    47  

    58      if not task:
    59:         await answer_callback_query(callback_query_id, text="Уже удалена/не найдена", show_alert=True)
    60          return

    66      await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    67:     await answer_callback_query(callback_query_id, text="Удалено 🗑️")
    68  

    77      await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    78:     await answer_callback_query(callback_query_id)

    focus/backend/services/telegram/callback_handlers/done.py:
    5  from focus.backend.services.tasks import change_task_status
    6: from focus.backend.services.telegram.api import answer_callback_query, edit_message_text
    7  from focus.backend.services.telegram.commands.today import render_today

    19      await edit_message_text(ctx.chat_id, message_id, text, reply_markup=kb)
    20:     await answer_callback_query(callback_query_id)
    21  

    33      if not task:
    34:         await answer_callback_query(
    35              callback_query_id, text=f"Не нашёл задачу id={task_id}", show_alert=True

    39      if task.status == TaskStatus.DONE.value:
    40:         await answer_callback_query(
    41              callback_query_id, text="Уже закрыта ✅", show_alert=False

    50  
    51:     await answer_callback_query(callback_query_id, text="Готово ✅", show_alert=False)
