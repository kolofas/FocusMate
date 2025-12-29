# FocusMate Architecture

## Goal
Keep the codebase maintainable as the product grows by enforcing clear boundaries between layers:
- HTTP/Telegram adapters do not contain business rules or SQL
- Business logic is isolated and testable
- Database access is centralized

## Layers

### Routers (HTTP)
Location: `focus/backend/routers/`

Responsibilities:
- Parse and validate HTTP input (Query/Body)
- Map input into DTOs (Pydantic models)
- Call services / repositories
- Return response models

Must NOT:
- Build SQLAlchemy queries
- Contain product rules beyond simple validation
- Contain commit/rollback orchestration unless it is the explicit use-case boundary

### Services (Use-cases)
Location: `focus/backend/services/`

Responsibilities:
- Implement business use-cases (create task from inbox, build today plan, change status rules)
- Orchestrate repositories and domain rules
- Be test-friendly (small functions, deterministic logic)

May:
- Own transaction boundaries for a use-case (commit/rollback) if that is the chosen pattern

Must NOT:
- Import Telegram layer (`focus.backend.services.telegram.*`)

### Repositories (DB access)
Location: `focus/backend/repositories/`

Responsibilities:
- Contain SQLAlchemy queries and persistence operations
- Provide clear methods like `get_user_task`, `list_tasks`, `add_inbox_event`, etc.

Must:
- Be free of FastAPI/Telegram concerns (no Request, no send_reply)

### Telegram (Adapter)
Location: `focus/backend/services/telegram/` and `focus/backend/routers/telegram.py`

Responsibilities:
- Parse Telegram updates, detect commands vs text
- Call core services/repositories
- Format human-friendly replies and send them

May:
- Commit/rollback for Telegram-specific flows if that flow is treated as a use-case boundary

## Import Rules
- Core layers MUST NOT import Telegram: `services/*` and `repositories/*` cannot import `services/telegram/*`
- `services/__init__.py` is not a public API; prefer explicit imports from modules

## Transaction Rules
- If a function performs `commit()`, it must have an explicit error strategy:
  - either `try/except -> rollback -> raise`
  - or be called inside a higher-level transaction boundary

## Naming
- `TaskRepo`, `InboxRepo` for repositories
- `create_task_from_parsed`, `get_plan_today` for services
- Telegram commands: `command_<name>`
