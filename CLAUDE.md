# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Taller Mecánico is a mobile-first parts inventory app for small Honduran auto/moto repair shops: phone-number login, one-tap stock changes, physical counts, low-stock alerts, movement history, and offline use. It replaced an unsalvageable university prototype (Reflex talking directly to Oracle with hardcoded credentials); none of that code remains. Product rationale and the roadmap after this MVP (customers/vehicles/quotes/work orders, then opt-in SAR/CAI invoicing, then multi-user roles) live in `odd/tasks/inventory-mvp-rebuild.md` and `docs/research/`.

Code, identifiers, and comments are in English. UI copy (web) and the README are in Spanish — this is the product's market language, not a translation step to add later.

## Commands

### API (`api/`, Python + uv)

```sh
docker compose up -d db                               # Postgres on localhost:5440
cd api
cp env.example .env                                     # then edit TALLER_* values; see below
uv run alembic upgrade head
uv run uvicorn taller.main:app --reload --port 8010

uv run ruff check .                                      # lint
uv run ruff format --check .                             # format check (uv run ruff format . to fix)
uv run pytest                                             # all tests
uv run pytest tests/inventory/test_items_api.py::test_name_of_test   # one test (standard pytest node id)

uv run alembic revision --autogenerate -m "add x"         # new migration
```

`api/.env` cannot be created by writing a dotfile directly in this sandbox (permissions deny any `.env*`-prefixed write); `api/env.example` is the checked-in template and is the one file to copy from, not invent from scratch. Settings are read by `pydantic-settings` from env vars prefixed `TALLER_` (`api/src/taller/shared/config.py`): `TALLER_DATABASE_URL`, `TALLER_JWT_SECRET` (required, ≥32 chars, no default), `TALLER_COOKIE_SECURE` (set `false` for local HTTP).

Tests need the `db` container reachable (`conftest.py` exits with a clear message otherwise) and a `taller_test` database, created by `docker/postgres/init/01-test-db.sql` **only on a fresh Postgres volume** — `docker compose down -v && docker compose up -d db` to recreate it if that database doesn't exist yet. Each test runs inside a SAVEPOINT (`conftest.py`'s `db_session` fixture) and is rolled back on teardown, so tests never leave data behind.

### Web (`web/`, npm)

```sh
cd web
npm install
npm run dev                                               # Vite dev server on 5173, proxies /api to :8010

npm run lint                                              # eslint .
npm run typecheck                                         # tsc -b --noEmit
npm test -- --run                                         # vitest, all tests, non-watch
npm test -- --run src/app/RequireSession.test.tsx         # one file
npm run build                                             # tsc -b && vite build
```

Tests mock the API with MSW (`web/src/test/server.ts`, `web/src/test/handlers.ts`): `beforeAll(() => server.listen({ onUnhandledFrame: "error" }))` fails a test loudly if it hits a route with no handler, and a test overrides one handler for its case with `server.use(http.get("/api/...", () => HttpResponse.json({...})))`. IndexedDB (the outbox, the persisted query cache) is polyfilled once in `web/src/test/setup.ts` via `fake-indexeddb/auto`, which also clears the outbox and query-cache IndexedDB stores after every test to stop state leaking between tests.

## Architecture

### API: hexagonal per feature

`api/src/taller/<feature>/` (`identity`, `inventory`; `health` is just a router) each split into:

- `domain/` — entities and errors, no framework imports.
- `application/` — use cases (plain functions) and `Protocol` ports (`UserRepository`, `ItemRepository`, `MovementRepository`, `TokenService`, ...) that the use cases depend on without knowing the implementation.
- `adapters/` — SQLAlchemy repositories implementing those ports, Pydantic request/response schemas, and the FastAPI `router.py`.

`taller/shared/` holds cross-feature plumbing (`db.py` session factory, `config.py` settings). `taller/main.py` is the only place routers get assembled into the `FastAPI` app, each mounted under `/api`.

### Web: container/presentational + shared UI kit

`web/src/features/<feature>/` (`auth`, `inventory`) hold screens (containers, wired to TanStack Query and the API client) and presentational components (props in, JSX out, no fetching) side by side, plus one `api.ts` and one `copy.ts` per feature. `web/src/shared/ui/` is the atomic kit (`Button`, `Spinner`, ...) shared across features. `web/src/app/` wires routing (`router.tsx`) and the session guard (`RequireSession.tsx`).

`copy.ts` holds every Spanish user-facing string for its feature in one object, plus a map from an API error `code` (the `detail` string FastAPI returns) to the Spanish message shown for it. The API itself never returns Spanish — it returns English error codes in `detail`, and the web layer is solely responsible for localizing them.

### Tenancy

Every workshop (tenant) owns its users and inventory. `get_current_workshop_id` (`api/src/taller/identity/adapters/dependencies.py`) reads the session, resolves the current user, and returns `user.workshop_id`; every inventory query and mutation is scoped by it, so cross-tenant access is structurally impossible rather than checked ad hoc per endpoint. A session is a JWT signed with `TALLER_JWT_SECRET`, carried in the httpOnly, `SameSite=Lax` cookie `taller_session`. Web and API are served same-origin — the Vite dev proxy forwards `/api` to the API in development — so the cookie needs no CORS configuration.

Login is throttled per normalized phone, registered or not (so a lockout never reveals which phones have accounts): after 5 consecutive failures the phone is locked for 15 minutes and every login returns `429 too_many_login_attempts` with `Retry-After`, without checking the password; a success resets the count. `attempt_login` (`api/src/taller/identity/application/use_cases.py`) holds a row lock on the phone's `login_throttles` row for the whole attempt, and the route commits even on a 401 — `get_db` never commits, so an uncommitted failure would vanish with the response. Time comes from the injectable `get_clock` dependency, which tests override instead of sleeping. The test `client` fixture rolls back each request's uncommitted work, the way the real `get_db` does, so a route that forgets to commit fails its tests.

### Stock ledger

Stock is never stored as a mutable counter the client edits directly: it is the sum of an append-only movement ledger (`in`, `out`, `adjust`), and the sum is cached on the `Item` row for cheap reads. `record_movement` (`api/src/taller/inventory/application/use_cases.py`) takes a row lock on the item (`item_repo.get_for_update`) before computing the new stock and saving it, so two concurrent movements on the same item can't race and lose an update.

Movements carry a client-generated UUID. If that id already exists with the exact same `{item_id, kind, quantity, note}`, the call is a replay and nothing changes (idempotent — this is what makes offline retry and replay safe); if it exists with a different payload, that's a real conflict (409). Item creation is idempotent the same way via a client-generated item id, and its `initial_stock` is always recorded as an `adjust` movement with a deterministic id derived from the item id — even when the initial stock is 0 — so replaying item creation never double-applies the initial stock.

Negative stock is allowed and flagged (`needs_review`/`is_low` on the item), never blocked: a mechanic mid-job must not be stopped by the app, and a queued offline movement must always apply once it reaches the server. Search is accent-insensitive via an `IMMUTABLE` plpgsql wrapper function, `taller_unaccent_lower`, used both for search filtering and for the name-uniqueness constraint.

### Offline

`recordMovement` (`web/src/features/inventory/commands.ts`) never calls the API directly — it only enqueues the movement into an IndexedDB outbox, then triggers a flush. `flushOutboxOnce` → `withFlushLock` (`web/src/features/inventory/offlineSync.ts`) sends the outbox's entries to the server FIFO, one at a time, serialized by a Web Locks–based mutex (with an in-tab `Promise` chain fallback where Web Locks aren't available, e.g. the test runner) — responses can never be reconciled out of order. Reading items (`fetchItemsFolded` / the single-item fetch in `hooks.ts`) runs inside that *same* lock and folds any still-pending outbox entries onto the fetched data, so a read can never land in the gap between a flush's PUT succeeding and it removing the entry, and a queued tap is never invisible because a refetch happened to win a race.

Creating or editing an item requires a live connection (disabled in the UI with a message when offline); only movements go through the outbox. Outbox entries are scoped by workshop id and only flush for the session's current workshop. The TanStack Query cache is persisted to IndexedDB for offline reads, capped at 7 days, version-busted on the Vite-injected app version (`__APP_VERSION__`, see `vite.config.ts`), and cleared on logout. Every query key holding one workshop's data starts with `workshopQueryKey(workshopId)` (`web/src/features/auth/hooks.ts`; inventory keys build on it in `web/src/features/inventory/hooks.ts`), so one workshop's cached data is never served to another's session; a login or registration removes every cached query that is not the session or the new workshop's own (the persister then rewrites IndexedDB without them), but never touches the outbox.

`RequireSession` (`web/src/app/RequireSession.tsx`) treats a `network_error` specially: if a cached session is still present (restored from the persisted cache, or just stale after a failed background refetch), protected content renders anyway — only a real 401 ("not logged in") redirects to `/login`. An offline user with no cached session at all sees a dedicated "sin conexión" screen instead of a login form they could fill in for nothing.

The service worker (`vite-plugin-pwa`, configured in `vite.config.ts`) precaches the app shell but routes every `/api/` request `NetworkOnly` — API responses are never served from the service worker's cache, because the persisted query cache above is the one offline data source, and a stale cached API response must never win a race against the real backend.

## Public test deployment

A shareable test instance runs at https://inventario-taller.danielbanariba.com from a detached worktree on the dev machine (its own Postgres container, two systemd user units, the `ceiba-demos` Cloudflare tunnel). `deploy/demo/README.md` is the runbook: what runs where, how to deploy an update, stop it, and read its logs.
Its build prefills a shared demo account on the login form from `VITE_DEMO_PHONE`/`VITE_DEMO_PASSWORD` (`web/src/features/auth/demoAccount.ts`); Vite compiles those into the public bundle, so never set them for any other build.

## Gotchas

- Local Postgres/API ports: `5432`–`5434` and `8000`–`8001` are taken on the usual dev machine, hence Postgres on `5440` and the API on `8010` (`docker-compose.yml`, `api/env.example`).
- `api/tests/test_migrations.py` runs `alembic check` and fails on any drift between the models and the migrations. Declare indexes on the models; an index the models cannot express (the functional, partial active-name index) must be listed in `MIGRATION_ONLY_INDEXES` in `api/migrations/env.py`, or autogenerate emits a `drop_index` for it.
- TypeScript is pinned to `6.0.x` (`web/package.json`) because `typescript-eslint@8.71.x` requires `<6.1`.
- FastAPI deprecates `HTTP_422_UNPROCESSABLE_ENTITY` in favor of `HTTP_422_UNPROCESSABLE_CONTENT` — the latter is what this codebase uses (`api/src/taller/inventory/adapters/router.py`); don't reach for the deprecated name out of habit.
- This agent sandbox denies writes to any path matching `.env*` by its own permission settings, regardless of content — `api/env.example` is the checked-in, writable template; `cp api/env.example api/.env` (shell copy, not a direct write to the `.env` path) then edit the values the task needs.

## Commits and pull requests

- Commit messages follow `templates/commit-template.en.git.txt`: Gitmoji + Conventional Commits, in English. Title `<gitmoji> <type>(<scope>): <description>` (for example `:sparkles: feat(inventory): add a physical count`), imperative, lowercase, no trailing period, at most 72 characters; the body explains what changed and why, wrapped at 72 characters.
- Pull requests use `.github/pull_request_template.md` (GitHub pre-fills it): a description readable in one minute whose first line follows the commit format, then the verification checklist for this stack.

## Agent skills

Shared project skills live in `.agents/skills/` (tracked, pinned in `skills-lock.json`): `vercel-react-best-practices`, `tanstack-query-best-practices`, `vite`, `vitest`, `playwright-best-practices`, `postgresql-best-practices`. Each was audited before install (documentation only: no scripts, no network calls, nothing that overrides repository rules). Claude Code reads them through symlinks in `.claude/skills/`, which is personal and git-ignored; after cloning, create the links with:

```sh
mkdir -p .claude/skills && for s in .agents/skills/*/; do n=$(basename "$s"); ln -sfn "../../.agents/skills/$n" ".claude/skills/$n"; done
```

Add or update a skill with `DO_NOT_TRACK=1 npx skills add <owner/repo> --skill <name> --agent claude-code codex --yes` (or `npx skills update -p`), audit the new content before committing, and keep the list above in sync.

## Planning and history

- `odd/tasks/` — feature documents: objective, decisions, task-by-task progress and verification evidence for each feature.
- `docs/research/` — the market research (Honduran workshop needs, adoption barriers, competitors) that the product decisions in `odd/tasks/` are based on.
