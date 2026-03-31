from ..types import CommandHandler
from .help import command_help
from .today import command_today
from .tasks import command_tasks
from .done import command_done
from .status import command_status
from .delete import command_delete
from .edit import command_edit

COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "/today": command_today,
    "/focus": command_today,
    "/tasks": command_tasks,
    "/help": command_help,
    "/start": command_help,
    "/done": command_done,
    "/status": command_status,
    "/d": command_done,
    "/s": command_status,
    "/del": command_delete,
    "/rm": command_delete,
    "/edit": command_edit,
    "/e": command_edit,
}
