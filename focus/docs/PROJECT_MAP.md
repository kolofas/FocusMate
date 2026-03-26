# FocusMate - PROJECT_MAP (Single Source of Truth)

> Status: Active
> Updated: 2026-03-26
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

### Architecture improvements already done
- asyncpg migration + stable async DB flows
- layering: routers → services → repositories
- extracted repos for tasks/inbox/planner
- telegram commands no longer query DB directly (use repos)
- logging cleanup + ruff

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
- [ ] Task Edit MVP (title/status/deadline in Telegram)
- [ ] Reminders MVP (set/cancel/deliver)
- [ ] Progress Feedback MVP (`/summary today`, `/summary week`)

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
