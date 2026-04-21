# FocusMate — FEATURE_BOARD

> Этот файл — управление продуктом.
> Здесь фиксируются фичи, приоритеты и прогресс.
> Обновляется после каждой рабочей сессии (1–3 минуты).

---

# 🎯 Финальная точка спринта

Спринт-пивот: до переезда на новый сервер фокус на платформенном слое (API + Web UI + качество),
чтобы не блокироваться на сетевой доступности Telegram.

Definition of Done (спринт закрыт, если):
1. Web UI MVP покрывает базовый daily-flow: список, today, смена статуса, edit, deadline/reminder.
2. API-контракты по задачам/фокусу/reminder стабильны и покрыты регрессией.
3. Onboarding v1 делает первый запуск понятным за 1-2 минуты.
4. Критичные пользовательские сценарии проходят локально и в CI.
5. Telegram-слой не ломается, но не является блокером для выпуска ценности.

---

# 🧭 Product Direction v2 (freeze)

FocusMate = панель улучшения жизни, а не только таск-менеджер.

Core loop:
`быстрое действие (1-2 тапа) -> рост категории жизни -> видимый прогресс (день/неделя)`

Категории MVP:
- здоровье
- работа/деньги
- развитие/учёба
- состояние/энергия
- личное

UX принцип:
- минимум ввода, максимум выбора/пресетов
- повтор "как вчера"
- мгновенный визуальный отклик

Что не делаем в первой волне:
- сложная геймификация
- социальные механики
- AI-коуч
- тяжелая кастомизация

---

# 1️⃣ Текущее состояние продукта

## Ядро (стабильно работает)
- Tasks (CRUD, теги, статусы)
- Inbox (быстрое добавление + dedup)
- Planner (интеграция с today)
- Focus (базовая логика)
- Telegram UX (/today + callbacks + delete/done flow + action confirmations)
- CI/CD + Docker + тесты

---

# 2️⃣ Продуктовые проблемы (по реальному использованию)

## UX
- Где-то ещё создаются новые сообщения вместо ожидаемого поведения
- Много шагов в некоторых сценариях
- Нет ощущения “экрана”, иногда ощущение “чата”

## Ценность
- Нет статистики
- Нет истории фокуса
- Нет напоминаний
- Нет редактирования задач
- Нет ощущения прогресса

---

# 3️⃣ Приоритеты

## 🔴 P0 — Критичный UX (ощущение приложения)
- [x] Унифицировать editMessageText во всех flow
- [x] Уменьшить спам новых сообщений
- [x] Сделать единый render/update механизм

Definition of Done:
- /today, /tasks, /status, /done, /delete работают без лишних сообщений
- Callback сценарии обновляют одно и то же сообщение

---

## 🟠 P1 — Базовая полезность
- [x] Task Edit MVP (title/status/deadline)
- [x] Reminders MVP (set/cancel/deliver)
- [ ] Planner UX v2 (явный сбор плана + replan без хаоса)

Definition of Done:
- Можно изменить текст задачи
- Можно поставить напоминание
- Можно отменить напоминание

---

## 🟡 P2 — Усиление ценности
- [ ] Progress Feedback MVP (/summary today, /summary week)
- [ ] История фокус-сессий
- [ ] Статистика по времени
- [ ] Стрики

---

## 🟢 P3 — Долгосрочные идеи
- [ ] Геймификация
- [ ] Очки / уровни
- [ ] Web UI
- [ ] Аналитика

---

# 4️⃣ Вектор развития (выбирается на неделю)

Возможные стратегии:

A — UX-стабилизация  
Фокус: довести Telegram до ощущения “приложения”

B — Focus-углубление  
Фокус: таймер + статистика + история

C — Planner-центр  
Фокус: план дня + перенос задач

---

# 5️⃣ План текущей недели

Главный фокус недели:
- Пивот на non-Telegram слой (API/Web/качество), чтобы не тормозить спринт.
Конкретные задачи:
1. API/domain hardening
    [x] Этап 1: зафиксировать Web UI API contract v1 (`/tasks`, `/focus/today`, `/tasks/{id}/status`)
    [x] Этап 2: добавить reminder-поля в write-контракты (`TaskCreate/TaskUpdate`) и PATCH-handlers
    [x] Этап 3: единый формат ошибок/валидации для пользовательских операций
2. Web UI MVP (минимальный контур)
    [x] Этап 1: каркас React+Vite+TS + минималистичный UI shell
    [x] Экран "All tasks" (read-only)
    [x] Экран "Today" (read-only)
    [ ] Быстрая смена статуса
    [ ] Edit title + установка/сброс deadline/reminder
3. Auth & personalization (web-first)
    [x] Web auth MVP (session/token) for personal workspace
    [x] Bind API requests to current user (remove shared/global web state)
    [ ] "My data only" smoke-check in prod
4. Targeted refactor budget (before onboarding, no full rewrite)
    [x] 1-2 focused sessions only on overloaded backend functions that block auth/personalization
    [x] Split responsibilities (validation/repo/orchestration), keep behavior and API contracts unchanged
    [x] Add/adjust focused regression tests for touched flows
5. Onboarding v1
    [ ] [id:99] Пошаговый "первый запуск" (что делать в первые 2 минуты)
    [ ] In-app onboarding hints for Life tab (first 3 actions)
6. UI/visual polish
    [ ] Improve visual hierarchy (primary CTA, spacing, contrast)
    [ ] Compact Recent list + progressive reveal ("Show more")
    [ ] Mobile readability pass
7. Quality
    [ ] [id:97] Расширить тесты на core API/use-cases
    [ ] Точечные контрактные тесты для будущего Web UI
8. Reminders (infra-next)
    [ ] Вынести delivery в Redis worker после стабилизации базового MVP
9. Telegram compatibility (без блокировки спринта)
    [ ] [id:98] Кнопки смены статуса в Telegram
    [ ] [id:24] Реализовать "Индекс элементов запроса +1"
10. Ops/docs
    [ ] Короткий production runbook в docs (deploy/restart/logs/migrate/rollback)
    [ ] Зафиксировать сетевой риск текущего сервера (недоступность api.telegram.org:443)
    [ ] Настроить production-deploy Web UI на сервере (build `focus/web`, раздача `dist`, API proxy/CORS, smoke-check)

---

## 5.2 Plan for 3 sprints (v2)

### Sprint 1 — Foundation (backend-first)
- Новые сущности: `LifeCategory`, `ActionTemplate`, `UserAction`, `ProgressEntry`
- Миграции и сервисные правила начисления прогресса
- API:
  - `GET /life/categories`
  - `GET /life/actions/quick`
  - `POST /life/actions/log`
- Тесты для core use-cases

Status:
- [x] Foundation model/tables added
- [x] Core read/write life endpoints added
- [ ] Core automated tests expansion (next atomic step)

### Sprint 2 — Dashboard + Fast UX
- API:
  - [x] `GET /life/dashboard/today`
  - [x] `GET /life/dashboard/week`
  - [x] `GET /life/actions/recent`
  - [x] `POST /life/actions/repeat`
- Web UI:
  - экран категорий
  - быстрые пресеты действий
  - повтор последнего/вчерашнего
- Фокус на 1-2 тапа до результата

Status:
- [x] Read/dashboard API for day/week/recent
- [x] Fast repeat API (reuse previous action in 1 call)
- [x] "Repeat last/yesterday" shortcut endpoint
- [x] Web UI wiring for new life endpoints
- [ ] UI polish pass (visual hierarchy, compact recent, primary CTA)

### Sprint 3 — Product polish
- Auth + personal workspace for web
- Onboarding v1 (первые 2 минуты)
- UI polish pass (clarity first, then aesthetics)
- Простые unlock-механики (без магазина)
- Подсветка перекосов и базовые рекомендации
- Beta-ready smoke + регрессия

---

## 5.1 Web UI API contract v1 (freeze)

Цель: собрать Web UI MVP без зависимости от Telegram.

### Read API
- `GET /tasks/`
  - query:
    - `limit` (1..200), `offset` (>=0)
    - `status` (`inbox|planned|done|snoozed`)
    - `q` (поиск по title, case-insensitive)
    - `tag` (без `#`)
    - `order_by` (`created_at|deadline`)
    - `dir` (`asc|desc`)
    - `user_id` (optional)
  - response: `TaskRead[]`
- `GET /tasks/{id}`
  - response: `TaskRead`
  - `404`: `{"error":{"code":"not_found","message":"Task not found"}}`
- `GET /focus/today?user_id=<id>`
  - response: `PlanTodayResponse { date, items[] }`
  - `items[i]`: `{ rank, score, task: TaskRead }`

### Write API
- `POST /tasks/`
  - body: `TaskCreate { title, description?, source?, deadline?, reminder_at?, tags[] }`
  - response: `201 TaskRead`, `Location: /tasks/{id}`
- `PATCH /tasks/{id}`
  - body: `TaskUpdate { title?, description?, deadline?, reminder_at?, tags? }`
  - response: `TaskRead`
  - `404`: `{"error":{"code":"not_found","message":"Task not found"}}`
- `POST /tasks/{id}/status`
  - body: `{ "status": "inbox|planned|done|snoozed" }`
  - response: `TaskRead` (+ пересборка today-плана)
- `DELETE /tasks/{id}`
  - response: `204`
  - `404`: `{"error":{"code":"not_found","message":"Task not found"}}`

### Error contract v1 (for Web UI)
- `400`: `{"error":{"code":"bad_request","message":"..."}}`
- `404`: `{"error":{"code":"not_found","message":"..."}}`
- `409`: `{"error":{"code":"conflict","message":"..."}}`
- `422`: `{"error":{"code":"validation_error","message":"Validation failed","details":[...]}}`

### TaskRead v1 (для Web UI)
`id, title, description, source, status, deadline, reminder_at, tags, created_at, updated_at`

### Known gap for next atomic step
- Reminder write-contract еще не зафиксирован в HTTP API:
  - нет отдельного endpoint-а set/clear reminder (сейчас через `POST/PATCH /tasks`).
  - Это отдельный шаг после Web UI MVP скелета.

---

# 6️⃣ Done log

- 2026-03-31 —
    Починили консистентность planner: после status-change (в т.ч. snoozed -> planned) Today пересобирается корректно.
    Реализовали Task Edit MVP v1: /edit (/e) для title, /deadline (/dl) для установки/сброса дедлайна.
    Добавили UX-подтверждения действий прямо на экране Today (✅/⚠️/ℹ️), без лишнего спама.
    Добавили /refresh alias и сделали /today явным "показать экран снова" (новое сообщение).
    Расширили тесты, итог: 22 passed.
- 2026-04-09 —
    Запустили Reminders MVP v1: установка/сброс напоминания + timezone-aware parsing.
    Добавили отправку due-reminders через APScheduler в app-процессе (single-instance friendly).
    Зафиксировали следующий инфраструктурный шаг: вынос отправки в Redis worker после стабилизации MVP.
- 2026-04-14 —
    Подтвердили сетевую проблему текущего сервера: недоступен `api.telegram.org:443` (timeout с хоста и из контейнера).
    Сделали спринт-пивот: продолжаем развивать продукт через API/Web/качество, не блокируясь на Telegram-доставке.
- 2026-04-14 (этап API hardening) —
    Завершили Этап 2: `reminder_at` добавлен в HTTP write-контракты (`TaskCreate`/`TaskUpdate`) и в create/update flow.
    Завершили Этап 3: введен единый error-contract API (`error.code`, `error.message`, `error.details`), добавлены контрактные тесты.
    Smoke-check через Postman и логи: `400/404/422/201/200` ожидаемо, `make test` -> 33 passed.
- 2026-04-14 (Web UI Stage 1) —
    Подняли каркас `focus/web` (React + Vite + TypeScript) в минималистичном стиле.
    Реализовали read-only экраны `All tasks` и `Today` с отображением `deadline/reminder`.
    Подготовили API-связку и добавили CORS-настройку для локального веб-режима.
- 2026-04-16 —
    Зафиксировали product direction v2: FocusMate как life-panel.
    Утвердили глобальный план на 3 спринта: Foundation -> Dashboard/Fast UX -> Product polish.
- 2026-04-18 (Sprint 1 / Step 3) —
    Добавили доменные foundation-сущности и миграции: `LifeCategory`, `ActionTemplate`, `UserAction`, `ProgressEntry`.
    Подняли core API `/life`: `GET /life/categories`, `GET /life/actions/quick`, `POST /life/actions/log`.
    Прогнали smoke в Postman: успешные ответы `200 OK` для сценариев log action (template/manual).
    Провели рефактор `log_user_action`: разбили перегруженный метод на helper-функции для читаемости и поддержки.
- 2026-04-18 (Sprint 2 / API progress) —
    Добавили life-dashboard endpoints: `GET /life/dashboard/today`, `GET /life/dashboard/week`.
    Добавили ленту действий `GET /life/actions/recent` и быстрый re-use `POST /life/actions/repeat`.
    Прогнали smoke-check в Postman: `log -> repeat -> dashboard(today/week) -> recent`, ответы стабильные `200 OK`.
- 2026-04-19 (Sprint 2 / shortcut + web wiring) —
    Добавили shortcut endpoint `POST /life/actions/repeat-shortcut` (`last`/`yesterday` + optional `reference_date`).
    Подключили Web UI к life-слою: новый таб `Life`, quick-actions, recent-list, `Repeat last/yesterday` и `Repeat` на последних действиях.
    Локально проверили работоспособность flow после миграций; на следующий шаг вынесли визуальный polish.
- 2026-04-20 (planning update) —
    После первого production запуска Web UI зафиксировали следующую приоритетную волну:
    `Auth/Personalization -> Onboarding -> UI polish`.
    Добавили отдельный `DEVELOPMENT_FLOW.md` для дисциплины веток, атомарных PR и стабильного merge в `main`.
- 2026-04-21 (refactor policy update) —
    Уточнили подход к рефакторингу: перед Onboarding не делаем полный рефактор проекта.
    Фиксируем ограниченный `refactor budget` (1-2 сессии) только для перегруженных backend-функций, критичных для `Auth/Personalization`.
    Порядок работ закреплен как: `Auth/Personalization -> targeted refactor -> Onboarding -> UI polish`.
- 2026-04-23 (auth/personalization + stability update) —
    Закрыли Web auth/personalization MVP: подключили `fastapi-users`, добавили `web_users`, привязали Web scope к персональному workspace (`telegram_user_id`) и подключили login/register/logout в Web UI.
    Добавили регрессионный тест `test_web_auth_personalization` и подтвердили запись life-действий в персональный `user_id` (без `NULL` shared-scope).
    Устранили race-condition в life seed (`_ensure_seeded`), который вызывал редкие `500` при конкурентных запросах.
- 2026-03-26 —
    Закрыли UX-стабилизацию Telegram v1: callback-сценарии держат один экран (edit вместо спама).
    Починили del_no и унифицировали Back-навигацию на today_refresh.
    Добавили регрессионные тесты UX-контракта; smoke-check на проде по логам успешный.
- 2026-02-23 —
    Добавили send_or_edit (edit с fallback на send).
    Научили бот редактировать экран Today вместо спама.
    Протащили хранение screen_message_id в telegram_users и прогнали миграцию на сервере.
    Проверили по логам: все действия Today работают через edit одного message_id (1221).
- YYYY-MM-DD —

---

# 7️⃣ Правила управления продуктом

1. Одновременно развивается только один вектор.
2. Не более 5 задач в активной неделе.
3. После завершения задачи — фиксировать в Done log.
4. Новые идеи добавлять в P3, а не в текущую неделю.
