# FocusMate Development Flow

Short operating guide to keep delivery stable and avoid context chaos.

## Branching
- `main` is always deployable.
- Every task goes into `feature/<short-name>`.
- One branch = one clear goal (no mixed scopes).

## Daily workflow
1. Create/update feature branch.
2. Implement small atomic changes.
3. Run checks locally:
   - backend: `make test`
   - web: `cd focus/web && npm run build`
4. Update docs briefly (`focus/docs/FEATURE_BOARD.md`, `focus/docs/PROJECT_MAP.md`).
5. Commit with focused message.
6. Push branch, review, merge to `main`.

## Commit discipline
- Prefer small commits with explicit intent:
  - `feat(life): add repeat shortcut endpoint`
  - `fix(web): serve assets from /web base`
  - `docs(roadmap): update sprint 2 progress`

## Environments
- Local web dev:
  - `cd focus/web`
  - `VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev`
- Production web:
  - same-origin by default (no `VITE_API_BASE_URL` required)
  - UI served from `/web` by backend image

## PR/Merge checklist
- Tests/build green.
- No generated artifacts in commit (`*.tsbuildinfo`, generated vite config outputs).
- Docs updated with what was done + next step.
- Smoke scenario executed for changed feature.

## Scope guardrails
- If task is > 1 session, split into phases and finish one phase fully.
- No refactors unless they unblock current feature.
- Keep critical path first: correctness -> UX clarity -> visual polish.
