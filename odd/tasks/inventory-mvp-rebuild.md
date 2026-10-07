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
- **Offline read consistency (T6b):** item fetch + outbox fold run inside the flush lock, so a read never interleaves with a flush pass; trade-off: a read can wait behind a slow pass (bounded by the 20 s per-request timeout).
- **Delivery strategy:** `single-pr` (user policy: one task = one branch = one PR, atomic commits). If the final size is unreasonable for one review, agree a cut with the user before splitting.

## Tasks

Route per task: delegated direct (one bounded writer) unless stated. Trigger evidence: each task touches 2+ non-trivial files.

- [x] **T0** Repo hygiene: ignore local tooling dirs, commit research docs, this plan and the legacy CLAUDE.md. Route: inline (mechanical).
- [x] **T1** API scaffold: uv project, app factory, settings, DB session, Alembic, `/api/health` with DB check, docker-compose Postgres, ruff + pytest setup.
- [x] **T2** Identity + workshops: register workshop with owner, login/logout via cookie, `me`, password hashing, authenticated workshop dependency.
- [x] **T3** Inventory API: items (create, update, archive, list with stock + search + low-stock filter), idempotent movements (in/out/adjust), item history, tenant isolation.
- [x] **T3b** Inventory API hardening from the T3 verifier: cross-tenant id collision returns 409 instead of an unhandled 500; upper bounds on quantities and prices (no integer overflow 500s); `initial_stock` covered by item replay idempotency (deterministic initial-movement id); escape `%`/`_` in search. Runs after T4 (single writer).
- [x] **T4** Web scaffold + auth: Vite React TS, Tailwind, router, query client, API client, PWA manifest, Vitest, login/register screens, protected routes.
- [x] **T5** Inventory UI: list + search, +/- stepper, add/edit item, item detail with history, low-stock view, physical count.
- [x] **T5b** Inventory UI fixes from the T5 verifier: accept thousands-grouped lempira amounts with `format.ts` tests, client-side upper bounds with Spanish messages, no `<button>` nested in `<a>` on the detail page, a 404 detail test. Runs after T6 (single writer).
- [x] **T6** Offline: persisted query cache, movement outbox in IndexedDB with sync on reconnect, online/offline indicator.
- [x] **T6b** Offline fixes from the T6 verifier: a refetch landing between a successful PUT and the outbox removal double-counts the movement (fetch + fold must not interleave with a flush); `nextSeq()` read-then-write is not atomic across tabs; add a flush-time 401 test. Runs after T5b (single writer).
- [x] **T7** Remove legacy code; rewrite README (Spanish) and CLAUDE.md for the new architecture.
- [x] **T8** End-to-end check in a real browser (register, add item, move stock, offline queue + sync). Ran; defects found → T8b.
- [x] **T8b** Fixes from T8: (D1) offline taps never reach the outbox because the movement mutation uses TanStack's default `networkMode: 'online'`, so it pauses, persists as a paused mutation with no resumable defaults, and is lost on reload; plus a reload while offline (or on "lie-fi") must keep a cached session usable instead of blocking on "Sin conexión"; (D2) the offline banner must show the pending-change count; (D3) the edit form and "Archivar" must be disabled offline with a message, like create; (D4) the item detail must show the sale price. Runs as one writer.
- [ ] **T9** Final checks before the PR: re-run the offline-reload scenario in a real browser; one independent review of all branch code (API and web, lockfiles excluded); Test Value Gate Pass 3 list of every new test.
- [ ] **T9b** Fixes from T9 plus the T8b follow-ups: inventory cache must never show one workshop's items to another workshop logging in on the same phone (after a 401 or a re-login); the service-worker `/api/` NetworkOnly rule never matches (Workbox matches the full URL); confirmed review findings.

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
| T2 | delegated (writer; 2+ non-trivial files) | 58ffa4a (+ fixes 0316d68) | ruff clean, pytest 26 passed, migration up/down/up ok, boot register→me→logout→me = 201/200/204/401; parent spot check pytest 26 passed | high (auth; assess unassessable → treated high); independent verifier: pass with follow-ups (bound login password length, deterministic tampered-token test, narrow IntegrityError mapping, `secure=` on delete_cookie; fixed in 0316d68 with a RED→GREEN test for the login bound; pytest 61 passed) |
| T3 | delegated (writer; 2+ non-trivial files) | 8cd5db6 | ruff clean, pytest 60 passed, migration up/down/up ok, boot: initial_stock 5 → out 2 → replay = 201/201/200, final stock 3; parent spot check pytest 60 passed | high (tenant isolation, row locking); independent verifier: pass with follow-ups → T3b |
| T4 | delegated (writer; 2+ non-trivial files) | 896d9fe | lint, typecheck clean; vitest 9 passed; build emits sw.js + Spanish manifest; smoke via Vite proxy: health 200, register 201, me 200; parent spot check vitest 9 passed | high (auth signal); independent verifier: pass with follow-ups (RegisterForm lacks the 128-char password max; folded into T5) |
| T3b | delegated (writer) | 104c8b3 | ruff clean, pytest 79 passed (RED per defect observed by stashing the fix); parent spot check pytest 79 passed | follow-up of a verified high-risk task; fixes only |
| T5 | delegated (writer; 2+ non-trivial files) | 2ba80bc | lint, typecheck clean; vitest 24 passed; build ok; smoke via proxy: register 201, item initial 3, in +1, stock 4; parent spot check vitest 24 passed. Test-first exception: writer wrote most code and tests together; RED proven retroactively for 7 behaviors by reverting each fix | high (auth signal from RegisterForm); independent verifier: pass with follow-ups: out-of-order reconciliation of concurrent taps (sent to the T6 writer, same code); thousands-grouped prices rejected, missing client upper bounds, Button nested in Link, no 404/format tests → T5b |
| T6 | delegated (writer; 2+ non-trivial files) | 48868cf | lint, typecheck clean; vitest 50 passed (stable x3); build: sw.js routes `/api/` NetworkOnly, shell precached; RED observed before implementing each module, plus the reverse-order taps regression test failing on the old transport; parent spot check vitest 50 passed | high (auth signal); independent verifier: pass with follow-ups → T6b |
| T5b | delegated (writer) | 1e75372 | lint, typecheck clean; vitest 72 passed; build ok; RED observed per item before fixing; parent spot check vitest | follow-up of a verified high-risk task; fixes only |
| T6b | delegated (writer) | b647f9d | lint, typecheck clean; vitest 76 passed x3; build ok; RED reproduced by reverting each fix (double count 12 vs 11, seq [1,1,1]); 401 test passed without code change; parent spot check vitest | follow-up of a verified high-risk task; fixes only |
| T7 | delegated (writer) | 92d1b7e | legacy tree removed (120 files, −6820 lines); README (es) and CLAUDE.md rewritten; api and web checks green | passive (docs + deletions) |
| T8 | delegated (read-only browser checker, Playwright 390×844 against `vite preview` + API) | — (no code) | PASS: register, add items, +/−, badges, search, count + history, logout/login, no `/api` from the SW, ≥48px targets, no overflow. FAIL: D1 (reload offline blocks the app and loses queued taps; the same taps without a reload sync exactly once), D2, D3, D4 → T8b | n/a (check only) |
| T8b | delegated (writer; 2+ non-trivial files) | 70a3364, 5462a33, a440ef1, b9d327d | lint, typecheck clean; vitest 88 passed x3; build ok; RED observed per defect (outbox `[]` after an offline tap; second offline reload showed "Sin conexión"; edit form enabled offline; price missing); parent spot check vitest 88 passed | follow-up of T8; root causes: default `networkMode: 'online'` paused taps before the outbox write; the persister only kept `success` queries, so one failed offline refetch erased the cached session; `useOnlineStatus` re-read `navigator.onLine` per screen. Not yet re-checked in a real browser (T9) |

T6 decisions: creating/editing items requires a connection (disabled offline with a message); the outbox is the only movement transport (FIFO, one at a time, Web Locks + in-tab mutex, 20 s timeout) so responses cannot reconcile out of order; pending outbox entries are folded onto fetched/persisted item data so a refetch never hides a queued tap; persisted query cache max age 7 days, busted by app version, cleared on logout; outbox entries carry the workshop id and only flush for the matching session.

T3 decisions: quantities are integers; movement replay compares `{item_id, kind, quantity, note}` (not `occurred_at`); `initial_stock` always records an `adjust` (even 0); simple UUID primary keys; concurrent insert races retried once after `IntegrityError`; accent-insensitive search and name uniqueness via an IMMUTABLE plpgsql wrapper `taller_unaccent_lower`.

## Next step

T9 (browser re-run of the offline-reload scenario and the independent review of all code, in parallel, both read-only), then T9b with every confirmed finding, then propose the PR to the user.

T8b known limitations (accepted for the MVP): on "lie-fi" (the phone reports online but requests fail) the banner shows the pending count but not "Sin conexión", and a tap stays pending until the 20 s send timeout; paused mutations saved by the pre-T8b build are dropped (no build reached users).

T8 decision: the "Por acabarse" filter keeps returning negative-stock items (they are at or below the minimum too, and need restocking); the badge shows "Revisar" because it takes precedence. By design, no change.
