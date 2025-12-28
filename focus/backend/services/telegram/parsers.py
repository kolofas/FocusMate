from __future__ import annotations

from typing import Sequence, Optional

from focus.backend.database.enums import TaskStatus
from .consts import _ALLOWED_STATUS


def _norm(raw: str) -> str:
    return raw.strip().lower()


_STATUS_BY_VALUE: dict[str, TaskStatus] = {st.value: st for st in TaskStatus}


def parse_status(value: str) -> TaskStatus | None:
    return _STATUS_BY_VALUE.get(_norm(value))


def parse_task_filters(
    args: Sequence[str],
) -> tuple[str | None, str | None, int | None, bool]:
    """
    Разбирает аргументы /tasks:
      статус (inbox/planned/done/snoozed),
      тег (#work),
      лимит (целое число),
      флаг all (показать все, без лимита).
    Возвращает (status, tag, limit, show_all).
    """
    status: Optional[str] = None
    tag: Optional[str] = None
    limit: Optional[int] = None
    show_all = False

    for raw in args:
        arg = _norm(raw)
        if not arg:
            continue

        if arg == "all":
            show_all = True
            continue

        if arg.isdigit():
            value = int(arg)
            if value > 0:
                limit = value
            continue

        if arg.startswith("#"):
            tag_value = arg[1:].strip()
            if tag_value:
                tag = tag_value
            continue

        if arg in _ALLOWED_STATUS:
            status = arg

    return status, tag, limit, show_all


def parse_today_filters(args: Sequence[str]) -> tuple[str | None, bool]:
    """
    Для /today поддерживаем:
      /today                 -> без фильтров, без done
      /today planned         -> только planned, без done
      /today planned all     -> только planned, с учётом done
      /today all             -> все статусы, включая done
    Возвращает (status_filter, include_done).
    """
    status: Optional[str] = None
    include_done = False

    for raw in args:
        argument = _norm(raw)
        if not argument:
            continue

        if argument in "all":
            include_done = True
            continue
        if argument in _ALLOWED_STATUS:
            status = argument

    return status, include_done
