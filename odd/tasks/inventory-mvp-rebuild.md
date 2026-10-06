# Feature: inventory-mvp-rebuild

Locator: `odd/tasks/inventory-mvp-rebuild.md` · Engram mirror: `odd/inventory-mvp-rebuild/tasks` · Branch: `feat/inventory-mvp`

## Objective

Replace the university project (Reflex 0.4.8 frontend talking directly to Oracle, FastAPI backend that only does login) with a sellable MVP for small Honduran auto/moto repair shops: a dead-simple, mobile-first parts inventory counter.

## Problem and why

- Real lead: a small, low-budget mechanic who wants to know how many units of each part they have (shock absorbers, oil) and is not comfortable with Excel.
- Market research (`docs/research/Necesidades de talleres en Honduras.md`): software adoption in shops is 9–23.5%, cost is the main barrier, no competitor supports Honduras/HNL/CAI, users are Android + WhatsApp + cash, motorcycles are ~51% of the fleet, parts often have no standard part number.
- The current codebase is not salvageable (hardcoded Oracle credentials, hardcoded secret, mostly dead or static pages). See `CLAUDE.md` (legacy section) for the map.

## Scope (this feature)

- Multi-tenant API: a workshop (tenant) registers with an owner account; all data is scoped to the workshop.
- Inventory: items identified by name (optional category, unit, minimum stock, sale price in HNL, notes); stock is the sum of an append-only movement ledger (in, out, physical-count adjustment).
- Installable PWA in Spanish with big touch targets: list + search, +/- per item, add/edit item, item history, low-stock view, physical count.
- Offline: app shell cached; inventory readable offline; movements recorded offline queue in IndexedDB and sync when back online.
- Remove the legacy code and rewrite README/CLAUDE.md.

## Out of scope (next features, in this order)

1. Customers, vehicles (cars and motorcycles), quotes, and work orders that consume stock.
2. SAR/CAI invoicing as an opt-in module (CAI range, RTN, ISV 15% breakdown, HNL only).
3. Additional users per workshop with roles, password reset, WhatsApp sharing of quotes, photos per item, pricing/billing of the product itself.

## Decisions

- **Stack:** API in Python (FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, uv, ruff, pytest). Web in React + TypeScript + Vite + vite-plugin-pwa + TanStack Query + Tailwind CSS, tested with Vitest + Testing Library, npm as package manager. Reflex dropped: server-held state over a websocket needs a constant connection and is a poor fit for a phone-first, offline-tolerant app.
- **Architecture:** screaming, feature-first folders on both sides. API is hexagonal per feature (`domain` → `application` use cases + ports → `adapters` for SQLAlchemy and HTTP). Web uses container/presentational components and an atomic `shared/ui` kit.
- **Stock as a ledger:** stock = sum of movement deltas. Movements carry a client-generated UUID and are idempotent, so offline replay never double-counts and ordering conflicts disappear. A physical count is stored as an adjustment carrying the counted quantity; the delta is computed against the stock at the moment the server applies it.
- **Negative stock is allowed and flagged**, never blocked: a mechanic mid-job must not be stopped by the app, and offline replays must always apply. The UI marks negative stock as "revisar".
- **Identity:** login with a Honduran phone number (8 digits) + password; no email required. Session is a signed JWT in an httpOnly, SameSite=Lax cookie (web and API served same-origin; Vite proxies `/api` in dev).
- **Money** stored as integer cents of HNL.
- **Web toolchain pins:** TypeScript 6.0 (typescript-eslint 8.71 requires <6.1), react-router 7, MSW 3, Vitest 5, Vite 8.
- **Language:** code, identifiers, comments and CLAUDE.md in English; UI copy and README in Spanish (product market).
- **Local ports** (5432–5434 and 8000–8001 are taken on the dev machine): Postgres `5440`, API `8010`, web dev `5173`.
- **Review mode:** RDD disabled for this clone (user decision, 2026-10-06) after two `lens_context_budget_exceeded` stops caused by generated lockfiles (`api/uv.lock` was 903 of 1653 lines). Replacement: per-task checks, an independent verifier for high-risk tasks per `gentle-ai review assess`, and one independent review of all code (lockfiles excluded) before the PR.
- **Delivery strategy:** `single-pr` (user policy: one task = one branch = one PR, atomic commits). If the final size is unreasonable for one review, agree a cut with the user before splitting.

## Tasks

Route per task: delegated direct (one bounded writer) unless stated. Trigger evidence: each task touches 2+ non-trivial files.

- [x] **T0** Repo hygiene: ignore local tooling dirs, commit research docs, this plan and the legacy CLAUDE.md. Route: inline (mechanical).
- [x] **T1** API scaffold: uv project, app factory, settings, DB session, Alembic, `/api/health` with DB check, docker-compose Postgres, ruff + pytest setup.
- [x] **T2** Identity + workshops: register workshop with owner, login/logout via cookie, `me`, password hashing, authenticated workshop dependency.
- [x] **T3** Inventory API: items (create, update, archive, list with stock + search + low-stock filter), idempotent movements (in/out/adjust), item history, tenant isolation.
- [x] **T3b** Inventory API hardening from the T3 verifier: cross-tenant id collision returns 409 instead of an unhandled 500; upper bounds on quantities and prices (no integer overflow 500s); `initial_stock` covered by item replay idempotency (deterministic initial-movement id); escape `%`/`_` in search. Runs after T4 (single writer).
- [x] **T4** Web scaffold + auth: Vite React TS, Tailwind, router, query client, API client, PWA manifest, Vitest, login/register screens, protected routes.
- [ ] **T5** Inventory UI: list + search, +/- stepper, add/edit item, item detail with history, low-stock view, physical count.
- [ ] **T6** Offline: persisted query cache, movement outbox in IndexedDB with sync on reconnect, online/offline indicator.
- [ ] **T7** Remove legacy code; rewrite README (Spanish) and CLAUDE.md for the new architecture.
- [ ] **T8** End-to-end check in a real browser (register, add item, move stock, offline queue + sync).

## Acceptance criteria

- A new workshop can register, log in on a phone-sized screen, add parts, and change stock with one tap per unit.
- Stock always equals the sum of movements; replaying the same movement twice changes nothing.
- One workshop can never read or change another workshop's data.
- Movements made offline appear immediately and reach the server after reconnecting.
- `api`: ruff check, ruff format --check, pytest all green. `web`: lint, typecheck, vitest, build all green.

## Checks per task

- API: `cd api && uv run ruff check . && uv run ruff format --check . && uv run pytest`
- Web: `cd web && npm run lint && npm run typecheck && npm test -- --run && npm run build`
- DB for tests: `docker compose up -d db` (Postgres on 5440).

## Progress

| Task | Route | Commit | Checks | Review tier |
| --- | --- | --- | --- | --- |
| T0 | inline (mechanical) | b3c8fee (research), b50514b (CLAUDE.md, plan, .gitignore) | structural readback | b3c8fee passive (boundary advanced); b50514b medium, under budget (pending in slice). First attempt as one commit: consent granted, review stopped with lens_context_budget_exceeded, so it was split. |
| T1 | delegated (writer; 2+ non-trivial files) | 858d65a | ruff check/format clean, pytest 2 passed, alembic upgrade ok, boot + curl health 200; parent spot check pytest 2 passed | high (alembic.ini starts processes); consent granted, review stopped with lens_context_budget_exceeded; RDD then disabled; independent verifier: pass with follow-ups (add `connect_timeout` to `build_engine`, anchor `env_file` to the package path; folded into T3) |
| T2 | delegated (writer; 2+ non-trivial files) | see git log (`feat(api): add workshop registration...`) | ruff clean, pytest 26 passed, migration up/down/up ok, boot register→me→logout→me = 201/200/204/401; parent spot check pytest 26 passed | high (auth; assess unassessable → treated high); independent verifier: pass with follow-ups (bound login password length, deterministic tampered-token test, narrow IntegrityError mapping, `secure=` on delete_cookie; fixed in 0316d68 with a RED→GREEN test for the login bound; pytest 61 passed) |
| T3 | delegated (writer; 2+ non-trivial files) | see git log (`feat(api): add inventory items...`) | ruff clean, pytest 60 passed, migration up/down/up ok, boot: initial_stock 5 → out 2 → replay = 201/201/200, final stock 3; parent spot check pytest 60 passed | high (tenant isolation, row locking); independent verifier: pass with follow-ups → T3b |
| T4 | delegated (writer; 2+ non-trivial files) | see git log (`feat(web): scaffold the installable PWA...`) | lint, typecheck clean; vitest 9 passed; build emits sw.js + Spanish manifest; smoke via Vite proxy: health 200, register 201, me 200; parent spot check vitest 9 passed | high (auth signal); independent verifier: pass with follow-ups (RegisterForm lacks the 128-char password max; folded into T5) |
| T3b | delegated (writer) | see git log (`fix(api): harden inventory...`) | ruff clean, pytest 79 passed (RED per defect observed by stashing the fix); parent spot check pytest 79 passed | follow-up of a verified high-risk task; fixes only |

T3 decisions: quantities are integers; movement replay compares `{item_id, kind, quantity, note}` (not `occurred_at`); `initial_stock` always records an `adjust` (even 0); simple UUID primary keys; concurrent insert races retried once after `IntegrityError`; accent-insensitive search and name uniqueness via an IMMUTABLE plpgsql wrapper `taller_unaccent_lower`.

## Next step

T5 (inventory UI) + T4 follow-up (password max length).
