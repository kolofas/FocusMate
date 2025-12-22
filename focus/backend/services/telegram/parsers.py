from typing import Sequence, Optional

from focus.backend.database.enums import TaskStatus
from .consts import _ALLOWED_STATUS


def parse_status(value: str) -> TaskStatus | None:
    value = value.strip().lower()
    for st in TaskStatus:
        if st.value == value:
            return st
    return None


def parse_task_filters(
    args: Sequence[str],
) -> tuple[Optional[str], Optional[str], Optional[int], bool]:
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
        arg = raw.strip().lower()
        if not arg:
            continue
        if arg == "all":
            show_all = True
        elif arg.isdigit():
            value = int(arg)
            if value > 0:
                limit = value
        elif arg.startswith("#"):
            tag = arg.lstrip("#")
        elif arg in _ALLOWED_STATUS:
            status = arg

    return status, tag, limit, show_all


def parse_today_filters(args: Sequence[str]) -> tuple[Optional[str], bool]:
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
        argument = raw.strip().lower()
        if not argument:
            continue

        if argument in _ALLOWED_STATUS:
            status = argument
        elif argument == "all":
            include_done = True

    return status, include_done
