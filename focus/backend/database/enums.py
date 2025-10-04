from enum import StrEnum

class TaskSource(StrEnum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    MANUAL = "manual"

class TaskStatus(StrEnum):
    INBOX = "inbox"
    PLANNED = "planned"
    DONE = "done"
    SNOOZED = "snoozed"
