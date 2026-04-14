# FocusMate - PROJECT_MAP (Single Source of Truth)

> Status: Active
> Updated: 2026-04-14
> Rule: if something conflicts with this file - this file wins.

## 0) Current state(TL;DR)
- Prod: ✅ deployed (Docker)
- Core stack: FastAPI + async SQLAlchemy + asyncpg + Alembic
- Interface: Telegram-first UX (/today + callbacks, single-screen update contract)
- Quality: tests + pre-commit (ruff) + CI
- Delivery: Docker build + CD deploy with healthcheck + rollback

## 1) What FocusMate is
Personal focus / productivity system with Telegram IX and backend API.
Main areas:
- Tasks
- Focus (sessions)
- Inbox (capture)
- Planner (planning)
- Telegram users + Telegram UX flows
- Parsing/Tags/Normalize (text utilities)

## 2) Repo map (where to look)
### App core
- `focus/backend/app.py` - FastAPI entrypoint
- `focus/backend/settings.py` - settings/env

### Layers
- `focus/backend/routers/` - HTTP API endpoints
- `focus/backend/services/` - business logic
- `focus/backend/repositories/` - DB access layer
- `focus/backend/database/` - engine/sessions/models/enums/migrations
- `focus/backend/schemas/` - DTO / query models
- `focus/backend/utils/` - helpers (datetime/normalize/tags)

### Tests
- `focus/backend/tests` - regression suite

### Infra
- `.github/workflows/ci.yml` - CI/CD workflows
- `Dockerfile` + `focus/docker-compose.yml` - containerization
- `alembic.ini` + `focus/backend/database/migrations/` - migrations

### Docs
- `focus/docs/architecture.md`
- `focus/docs/roadmap.md`
- `focus/docs/concept.md`
- `focus/docs/development_diary.md` (historical; prefer development_diary_v2.md)

## 3) Runtime map (how it works)
- Routers: `routers/tasks.py`, `routers/focus.py`, `routers/inbox.py`, `routers/telegram.py`, `routers/health.py`
- Services: `services/tasks.py`, `services/focus.py`, `services/inbox.py`, `services/planner.py`, `services/telegram_users.py`, `services/parsing.py`

## 4) Feature map (what exists)
### Telegram UX
- /today keyboard + callback routing (Telegram UX v1)
- editMessageText refresh/replan mechanics
- next-actions UX for /done and /status
- task delete integrated into today flow
- callbacks unified to one-screen behavior (`message_id` from callback -> `screen_message_id` fallback)
- unified back navigation (`today_refresh`, `⬅️ Назад`)
- explicit `/refresh` command alias and `/today` force-show behavior (new screen message)
- action confirmations on Today screen (`✅`/`⚠️`/`ℹ️`)

### Architecture improvements already done
- asyncpg migration + stable async DB flows
- layering: routers → services → repositories
- extracted repos for tasks/inbox/planner
- telegram commands no longer query DB directly (use repos)
- logging cleanup + ruff
- reminders worker MVP in app-process (APScheduler polling)

### CI/CD / Prod
- pytest in CI
- .env optional for CI
- build docker image in CI
- CD auto deploy with healthcheck + rollback
- forced rollback test removed (kept pipeline sane)

## 5) Roadmap (near-term)
### Now (1–2 weeks)
- [x] Keep PROJECT_MAP always updated after sessions
- [ ] Make production runbook (start/stop/logs/health/migrate)
- [x] Tighten module boundaries in `services/telegram/` (if needed)
- [x] Task Edit MVP v1 (title/status/deadline commands in Telegram)
- [x] Reminders MVP (set/cancel/deliver)
- [ ] Reminders infra-next: move send delivery to Redis worker (post-MVP)
- [x] Show task deadline/reminder on Today screen (visibility for urgency/reminders)
- [ ] Progress Feedback MVP (`/summary today`, `/summary week`)
- [x] Expand regression tests for planner consistency + edit/deadline command parsing
- [ ] Code health: targeted refactor of telegram/services layers (reduce duplication and tighten boundaries)
- [ ] Sprint pivot (while Telegram is network-blocked on current server):
  - [x] API/domain hardening: Web UI API contract v1 freeze (`/tasks`, `/focus/today`, `/tasks/{id}/status`)
  - [ ] API/domain hardening: reminder write-contract (HTTP)
  - [ ] Web UI MVP (tasks/today/status/edit/deadline/reminder)
  - [ ] Onboarding v1 (first-run clarity)
  - [ ] Test expansion for non-Telegram core paths

### Requested backlog (from FocusMate tasks)
- [ ] [id:23] Implement reminder setup
- [ ] [id:24] Implement "query items index +1"
- [ ] [id:97] Expand tests toward full-project coverage
- [ ] [id:98] Add buttons for task status change
- [ ] [id:99] Improve onboarding (reduce first-use complexity)

### Next (2–4 weeks)
- [ ] Extend Telegram UX (batch operations, smoother navigation)
- [ ] More tests around Telegram flows + planner
- [ ] Observability: structured logs + basic metrics (optional)

### Later / Ideas
- [ ] Gamification (streaks, points)
- [ ] Web UI
- [ ] Analytics dashboard
- [ ] Event-driven internals (optional)

## 6) Production runbook (fill this in)
> Keep this short and practical.

- Deploy method:
- Restart services:
- View logs:
- Healthcheck endpoint:
- Run migrations:
- Rollback:

## 7) Recent history (from git)
> Use this to quickly restore context.

- 2026-04-14 — Sprint pivot: temporarily shift focus from Telegram delivery to API/Web/quality layer due server network route issues to `api.telegram.org:443`
- 2026-04-09 — Reminders MVP v1 (set/clear + timezone-aware parsing) + app-process APScheduler delivery; infra-next fixed to Redis worker
- 2026-03-31 — Planner consistency fix + real replan; `/edit` + `/deadline` commands; Today action confirmations; `/refresh` alias; tests to 20 passed
- 2026-03-26 — Telegram UX stabilization: single-screen callbacks, del_no fix, unified Back, UX-contract tests, deployed and smoke-checked in prod
- 2026-02-20 — Telegram: task delete in today flow (`dab50de`)
- 2026-01-27 — CD: auto deploy with healthcheck + rollback (`18e263b`, `0f69e22`)
- 2026-01-23 — Docker + CI image build (`c6cc919`, `534dff1`, `62cd40d`)
- 2025-12-29..2026-01-04 — Telegram UX v1: /today + callbacks (`f9fc9c3`, `3fd5408`, `2658c18`, `fcfe27c`)
- 2025-12-26..2025-12-28 — Service/Repo layering (`30a4cec`, `556e359`, `fe35f12`, `cd85f59`, `1bf5169`)
- 2025-12-25 — asyncpg migration + stable async tests (`4dbc3ce`)
- 2025-12-22..2025-12-24 — Telegram refactor: flows + unified context (`f8ffcad`, `64baee5`, `a3833f7`)
- 2025-12-21 — migrations + telegram commands MVP (`7bec500`)

## 8) Rules (to prevent chaos)
- PROJECT_MAP.md is the only source of truth.
- Any doc not updated in 30+ days becomes STALE unless explicitly marked Active.
- After each coding session: update sections 0, 5, 7 (2 minutes).

---

## 9) Русский перевод (ниже основной версии)

### 0) Текущее состояние (кратко)
- Прод: ✅ развернут в Docker
- Стек: FastAPI + async SQLAlchemy + asyncpg + Alembic
- Интерфейс: Telegram-first UX (`/today` + callbacks, контракт одного экрана)
- Качество: тесты + pre-commit (ruff) + CI
- Доставка: Docker build + CD deploy с healthcheck и rollback

### 1) Что такое FocusMate
Личная система фокуса/продуктивности с Telegram-интерфейсом и backend API.
Ключевые области:
- Задачи
- Фокус (сессии)
- Inbox (захват)
- Planner (планирование)
- Telegram users + Telegram UX сценарии
- Parsing/Tags/Normalize

### 2) Карта репозитория (где смотреть)
- `focus/backend/app.py` — вход FastAPI
- `focus/backend/settings.py` — настройки/env
- `focus/backend/routers/` — HTTP API
- `focus/backend/services/` — бизнес-логика
- `focus/backend/repositories/` — доступ к БД
- `focus/backend/database/` — engine/sessions/models/migrations
- `focus/backend/schemas/` — DTO/контракты
- `focus/backend/tests` — регрессионные тесты
- `.github/workflows/ci.yml` — CI/CD
- `Dockerfile`, `focus/docker-compose.yml` — контейнеризация

### 3) Карта выполнения (runtime)
- Роутеры: tasks/focus/inbox/telegram/health
- Сервисы: tasks/focus/inbox/planner/telegram_users/parsing

### 4) Карта фич (что уже есть)
- Telegram UX: `/today`, callbacks, refresh/replan, done/delete, подтверждения действий
- Архитектура: стабильный async DB flow, layering `routers -> services -> repositories`
- Прод/CI: pytest в CI, сборка image, CD deploy с проверкой здоровья
- Напоминания: MVP delivery через APScheduler в app-процессе

### 5) Ближайшая дорожная карта
Сейчас (1–2 недели):
- Production runbook
- Redis worker для reminder-delivery (post-MVP)
- Progress Feedback MVP (`/summary today`, `/summary week`)
- Рефакторинг слоев telegram/services
- Временный pivot спринта (пока текущий сервер нестабилен по Telegram):
  - укрепление API/domain слоя,
  - Web UI MVP,
  - onboarding v1,
  - расширение тестов для non-Telegram сценариев.

### 6) История (контекст)
- 2026-04-14 — Pivot спринта на API/Web/quality из-за сетевой недоступности `api.telegram.org:443` на текущем сервере
- 2026-04-09 — Reminders MVP v1 + APScheduler delivery
- 2026-03-31 — Planner consistency fix + `/edit`, `/deadline`, `/refresh`
- 2026-03-26 — стабилизация Telegram UX одного экрана

### 7) Правила
- `PROJECT_MAP.md` — источник истины.
- Если документ не обновлялся 30+ дней и не помечен Active — считать stale.
- После каждой сессии обновлять разделы состояния/roadmap/истории.
