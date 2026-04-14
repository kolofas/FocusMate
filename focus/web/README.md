# FocusMate Web MVP

Minimal web layer for FocusMate, built with React + Vite + TypeScript.

## Run

1. Install dependencies:

```bash
cd focus/web
npm install
```

2. Start dev server:

```bash
npm run dev
```

3. Optional API base override:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Stage scope

- Read-only MVP screens:
  - All tasks
  - Today focus list
- Shows `deadline` and `reminder_at`.
- Next stage: edit/status/deadline/reminder actions.
