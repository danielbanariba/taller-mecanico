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

Tests mock the API with MSW (`web/src/test/server.ts`, `web/src/test/handlers.ts`); a test overrides one handler for its case with `server.use(http.get("/api/...", () => HttpResponse.json({...})))`. `beforeAll(() => server.listen({ onUnhandledFrame: "error" }))` (`web/src/test/setup.ts`) covers both HTTP requests and WebSocket connections (MSW 3 replaced 2.x's `onUnhandledRequest` with this one option), but its `"error"` strategy only logs a console error and answers the request with a network error — it does not fail the test by itself, so a component that silently falls back when a request errors would still pass with an endpoint nobody mocked. `setup.ts` closes that gap: it also subscribes to MSW's `request:unhandled` life-cycle event and fails the test in `afterEach` if any request went unmocked. IndexedDB (the outbox, the persisted query cache) is polyfilled once in `web/src/test/setup.ts` via `fake-indexeddb/auto`, which also clears the outbox and query-cache IndexedDB stores after every test to stop state leaking between tests.

## Architecture

### API: hexagonal per feature

`api/src/taller/<feature>/` (`identity`, `inventory`, `customers`, `workorders`; `health` is just a router) each split into:

- `domain/` — entities and errors, no framework imports.
- `application/` — use cases (plain functions) and `Protocol` ports (`UserRepository`, `ItemRepository`, `MovementRepository`, `TokenService`, ...) that the use cases depend on without knowing the implementation.
- `adapters/` — SQLAlchemy repositories implementing those ports, Pydantic request/response schemas, and the FastAPI `router.py`.

`taller/shared/` holds cross-feature plumbing (`db.py` session factory, `config.py` settings). `taller/main.py` is the only place routers get assembled into the `FastAPI` app, each mounted under `/api`.

`customers` (phase 1 of the `workshop-core` change, see "Planning and history") holds customers and their vehicles. A customer's phone reuses identity's `PhoneNumber` value object unchanged — `phone_is_mobile` is a derived property (`phone[0] != "2"`), not a stored column. A vehicle's plate is normalized in Python (`domain/plate.py`) and kept unique per workshop among active vehicles through a partial index; archiving a customer cascades to its own active vehicles in one transaction, freeing their plates.

`workorders` (phase 2 of `workshop-core`) holds work orders, their quote lines (`labor`, `inventory_part`, `external_part`) and the status lifecycle that consumes and reverses stock. It is the codebase's first application-to-application dependency between features, accepted explicitly: `taller.workorders.application.use_cases` imports `record_movement`/`get_item` straight from `taller.inventory.application.use_cases` (plus the `ItemRepository`/`MovementRepository` port types), because `record_movement` already owns every ledger invariant — the row lock, the delta, the out-of-range guard, idempotent replay — and reusing it keeps one way to change stock. Work orders never import inventory's models or touch `Item.stock` directly; the reverse reference (inventory's `inventory_movements` pointing at `work_orders`/`work_order_lines`) is schema-only, by table-name string, never a Python import. Order numbers are per-workshop and gap-free (`workshop_counters`, an `INSERT ... ON CONFLICT DO UPDATE ... RETURNING value` upsert, retried once on a numbering race). Resolving an order's vehicle and owner for a response goes through `customers.application.describe_vehicles` (batched, one query per table), never a SQL join across features.

**Stock consumption.** Each `work_order_lines` row carries `stock_posted_quantity`/`stock_revision`. Every use case that changes an order's status or its lines finishes by running `plan_reconciliation` (pure, unit-tested on its own): for each line whose target quantity (its own quantity while the order is in a consuming status and the line is an unremoved `inventory_part`, otherwise zero) differs from what is already posted, it posts one `record_movement` call — `out` or `in` depending on the sign of the delta — with a deterministic id (`uuid5` of `order:line:revision`) and `order_id`/`order_line_id` set, then advances the line's posted quantity and revision. An edit mid-job posts only the delta (2 → 5 posts `out 3`; 5 → 2 posts `in 3`), never a full re-post; cancelling after consumption restores stock exactly. Every linked movement and the status write commit in one transaction (the router builds inventory's repositories on the same request session), so a failure partway through a multi-line consumption leaves nothing committed. Lines are locked in `(item_id, line_id)` order, never line-declaration order, to avoid a deadlock against another order consuming the same items in the opposite order.

**Payments, cash summary and export** (phase 3 of `workshop-core`) add no new feature package: payments live in `workorders` (`Payment`, `PaymentMethod`), and export is its own top-level `taller.export` package (`application/csv_zip.py`'s pure builder, `adapters/sources.py`'s per-entity reads, `adapters/router.py`'s `GET /export`). A payment's `method` is one of four English wire values (`cash`, `transfer`, `card`, `other`; Spanish labels only in the web's `copy.ts`). An order's `paid_cents`/`balance_cents` are always derived from its *non-voided* payments (`domain/money.py`), never stored; several partial payments are allowed while the order is `approved`, `in_progress`, `completed` or `delivered` (`domain/status.py`'s `PAYABLE`), and a payment can never push the balance negative. Voiding (`POST .../payments/{id}/void`) requires a reason, keeps the record (never deletes it), is idempotent, and excludes that payment from the paid total, the balance and the daily cash summary; voiding a payment that exists but not under the given order/workshop raises `PaymentNotFound` → 404 `payment_not_found` — a spec delta beyond the cross-workshop `work_order_not_found` case, added because the lookup is scoped to `(workshop_id, order_id, payment_id)` together. Cancelling an order is blocked (`work_order_has_payments`, 409) while it has any non-voided payment; an order whose only payments were voided stays cancellable. `daily_cash_summary` (`use_cases.py`) buckets payments by calendar day in `America/Tegucigalpa` (`ZoneInfo`, via the same injectable `Clock` identity's login throttling uses), as a sargable `paid_at` range — never UTC or the server's own zone — and always reports all four method totals, zero when a method had no payments that day. The export's `GET /export` streams a ZIP (built fully in memory, under one request's `READ COMMITTED` session) of one `utf-8-sig` CSV per entity — customers, vehicles, items, inventory movements, work orders, work order lines, payments, and, since `sar-invoicing` phase B, issued Facturas, their lines and Notas de Crédito, ten files in total (`fiscal_invoices.csv`/`fiscal_invoice_lines.csv` order by the invoice's own `issued_at, number`, `fiscal_credit_notes.csv` by its own) — with a formula-injection guard on text cells (covering a credit note's free-text `reason` the same way it covers any other text cell) and lempira amounts as plain decimals; it ignores any client-supplied workshop id and is read-only (two consecutive exports never create, modify or delete a row).

A work order's non-fiscal receipt (`web/src/features/workorders/receipt/`) is a **web-only** concern — no API endpoint renders it. `ReceiptBody` (shared content) backs two routes outside the app shell (`/ordenes/:id/recibo/58mm`, `/ordenes/:id/recibo/carta`, siblings of `<AppShell>` under the same `RequireSession` guard, per AD-16, so no navigation chrome ever prints), gated to `completed`/`delivered` orders by `useReceiptOrder`. The 58 mm layout measures its own rendered height (`useLayoutEffect` + `getBoundingClientRect`) to emit `@page { size: 58mm <height>mm; margin: 0 }`, falling back to `58mm 297mm` before that measurement resolves; the full-page layout only sets `@page { margin: 12mm }` (no `size`), so Letter and A4 both work. Both carry "DOCUMENTO NO FISCAL — No válido como factura" and `print:hidden` on their action bar; `OfflineStatusBanner` (which renders above every route, receipts included) also gets `print:hidden`. The order detail screen links to both routes ("Recibo 58 mm", "Recibo carta") only for an eligible order, through the same `isReceiptEligible` rule `useReceiptOrder.ts` exports, so the link and the route can never disagree.

### Invoicing (SAR/CAI, `sar-invoicing`)

`taller/invoicing/` is a new hexagonal feature holding the fiscal profile (one row per workshop, `fiscal_profiles`), CAI ranges (`cai_ranges`, bounded correlative counters per document type) and issued Facturas (`fiscal_invoices`/`fiscal_invoice_lines`). A workshop that never saves a profile has no row and sees no invoicing UI anywhere; `GET /invoicing/settings` and `issue_invoice` both compute readiness from the same pure function, so the button a mechanic sees and the rule the server enforces can never disagree. `invoicing.application` depends on `workorders.application` one way only (reading order status, lines and totals through its existing `WorkOrderRepository`/`order_total_cents`), the same newer-to-older dependency direction `workorders` already has on `inventory`.

**Invoiced-order lock.** `workorders` never imports `invoicing`: `WorkOrderRepository.active_invoice(*, workshop_id, order_id)` reads the `fiscal_invoices` table by table-name string only (`sqlalchemy.table(...)`, no model import), the same schema-only pattern `inventory_movements` already uses to read `work_orders`. `add_line`/`update_line`/`remove_line` call it right after their existing `EDITABLE` check and raise `WorkOrderInvoiced` (409 `work_order_invoiced`) when it finds a non-credited Factura; `lines_editable` folds the same check in. Status changes and an order's own fields (`complaint`, `odometer_km`, `notes`) stay editable while invoiced.

**Lock order.** Every fiscal write extends the existing lock order with two more steps after the order row: the workshop's `fiscal_profiles` row (`SELECT ... FOR UPDATE`), always locked before a CAI range is read, selected or allocated, and the `cai_ranges` row itself (the allocation `UPDATE ... RETURNING` takes it implicitly). The profile row is the per-workshop fiscal mutex: issuance, range create/`PATCH` and profile `PUT` all take it, so overlap checks, range selection, allocation and code changes for one workshop serialize on one lock, while concurrent issuance across workshops never contends.

**Immutable snapshots.** `fiscal_invoices`/`fiscal_invoice_lines` are guarded by a Postgres trigger (`taller_fiscal_invoice_guard`/`taller_fiscal_append_only`) that rejects every `UPDATE` and `DELETE` except the single future `credited_at` transition a credit note writes — an application bug or an ad-hoc script cannot rewrite or delete a legal document. `fiscal_credit_notes` (phase B) is itself a full snapshot, guarded by the same `taller_fiscal_append_only` trigger with no mutable transition at all: it copies the original Factura's issuer, buyer, amounts and total in words at issuance and references that Factura's own CAI, number and date, so it never changes after creation. Every printed field (issuer, CAI, range, buyer, lines, tax split, total in words) is copied at issuance, so editing the profile or the customer afterward never changes a reprint.

**Credit notes and the lock release (AD-13, phase B).** `issue_credit_note` extends the same lock order (the order row, then the Factura, then the fiscal profile, then the range) to issue a full-amount Nota de Crédito (`06`) against an issued, not-yet-credited Factura, then stamps that Factura's own `credited_at` — the one `UPDATE` its trigger allows. `WorkOrderRepository.active_invoice` reads only *non-credited* Facturas, so the moment `credited_at` is set the order's `work_order_invoiced` lines lock lifts and a new Factura can be issued on the same order; an order can end up with two invoices, one credited and one not, both kept for custody. A second credit note on an already-credited Factura is rejected (409 `invoice_already_credited`); a replay of an identical credit note (same id, invoice and reason) returns before any of those checks and never consumes a `06` number.

**Range warnings (AD-18, phase B).** `range_warnings` (pure; called from `get_settings` per document type) warns over a document type's *usable* ranges: `range_expires_soon` once the latest usable range's fecha límite is 60 days or fewer away (`EXPIRY_WARNING_DAYS`, matching Art. 59's two-month window to request the next range), and `range_low_numbers` once those ranges' remaining numbers, summed, are 50 or fewer (`LOW_NUMBERS_THRESHOLD`, an absolute count so it warns sensibly at every range size, never a percentage). A pre-registered standby range silences both before the current one lapses. The web surfaces both through `RangeWarnings.tsx` on the settings page and inside the issue-Factura and credit-note dialogs, without ever blocking submission.

**Rollback.** Each phase's migration `downgrade()` refuses by itself once any row exists in its fiscal document table (`SELECT EXISTS (SELECT 1 FROM fiscal_invoices)`, phase B also `fiscal_credit_notes`), unless re-run with `-x discard_fiscal_documents=demo` (`design.md`'s AD-20) — a database holding real fiscal documents is never downgraded; a bad release is reverted in code only, and the tables stay for custody (Art. 5, 41, 43). The demo runbook (`deploy/demo/README.md`) dumps the database first and uses that flag, since every document there is fictional.

### Web: container/presentational + shared UI kit

`web/src/features/<feature>/` (`auth`, `inventory`, `customers`, `workorders`) hold screens (containers, wired to TanStack Query and the API client) and presentational components (props in, JSX out, no fetching) side by side, plus one `api.ts` and one `copy.ts` per feature. `web/src/shared/ui/` is the atomic kit (`Button`, `Spinner`, ...) shared across features; `web/src/shared/format/money.ts` holds the lempira formatting/parsing helpers and `web/src/shared/format/phone.ts` the Honduran phone formatter, each moved there once a second feature needed it. `web/src/app/` wires routing (`router.tsx`) and the session guard (`RequireSession.tsx`).

`copy.ts` holds every Spanish user-facing string for its feature in one object, plus a map from an API error `code` (the `detail` string FastAPI returns) to the Spanish message shown for it. The API itself never returns Spanish — it returns English error codes in `detail`, and the web layer is solely responsible for localizing them.

### App shell and navigation

`web/src/app/AppShell.tsx` is a layout route (`Inventario · Clientes · Órdenes`) rendered inside `RequireSession`, wrapping every protected screen's `<Outlet/>` with `web/src/app/BottomNav.tsx`'s three tabs. The active tab tracks the first path segment, so nested routes like a vehicle's own detail screen under `/clientes/...` still highlight `Clientes`. The `Órdenes` tab is the real `workorders` feature (Abiertas/Historial list, detail, status actions, WhatsApp sharing); a customer's and a vehicle's detail screens list their own work orders (newest first), and a vehicle's "Nueva orden" button jumps straight to the confirm step of `/ordenes/nueva?vehiculo=<id>`, skipping the customer/vehicle pickers.

A header button opens a "Más" menu (the shared `Dialog.tsx` pattern, like every other confirm/action sheet): "Caja del día" (`/ordenes/caja`, a lazy route still nested inside `<AppShell>`, showing `CashSummaryPage`'s today-by-method totals — always a live fetch, never persisted offline, since `useCashSummary`'s `meta: { persist: false }` is honored by `shouldPersistQuery` in `web/src/app/providers.tsx`), "Exportar todo" (dynamically imports `features/workorders/export/exportData.ts` on click, so the fetch/blob/anchor-download plumbing never loads into the main chunk for a mechanic who never exports; disabled offline), and "Cerrar sesión" (the logout mutation, moved out of `InventoryPage` in phase 1, which no longer renders its own header or logout control).

### Tenancy

Every workshop (tenant) owns its users and inventory. `get_current_workshop_id` (`api/src/taller/identity/adapters/dependencies.py`) reads the session, resolves the current user, and returns `user.workshop_id`; every inventory query and mutation is scoped by it, so cross-tenant access is structurally impossible rather than checked ad hoc per endpoint. A session is a JWT signed with `TALLER_JWT_SECRET`, carried in the httpOnly, `SameSite=Lax` cookie `taller_session`. Web and API are served same-origin — the Vite dev proxy forwards `/api` to the API in development — so the cookie needs no CORS configuration.

Login is throttled per normalized phone, registered or not (so a lockout never reveals which phones have accounts): after 5 consecutive failures the phone is locked for 15 minutes and every login returns `429 too_many_login_attempts` with `Retry-After`, without checking the password; a success resets the count. `attempt_login` (`api/src/taller/identity/application/use_cases.py`) holds a row lock on the phone's `login_throttles` row for the whole attempt, and the route commits even on a 401 — `get_db` never commits, so an uncommitted failure would vanish with the response. Time comes from the injectable `get_clock` dependency, which tests override instead of sleeping. The test `client` fixture rolls back each request's uncommitted work, the way the real `get_db` does, so a route that forgets to commit fails its tests.

### Stock ledger

Stock is never stored as a mutable counter the client edits directly: it is the sum of an append-only movement ledger (`in`, `out`, `adjust`), and the sum is cached on the `Item` row for cheap reads. `record_movement` (`api/src/taller/inventory/application/use_cases.py`) takes a row lock on the item (`item_repo.get_for_update`) before computing the new stock and saving it, so two concurrent movements on the same item can't race and lose an update.

Movements carry a client-generated UUID. If that id already exists with the exact same `{item_id, kind, quantity, note, order_id, order_line_id}` — the last two are `None`/`None` for every movement an outbox tap or a manual edit ever records, and set only by `workorders`' own reconciliation — the call is a replay and nothing changes (idempotent — this is what makes offline retry and replay safe); if it exists with a different payload, that's a real conflict (409). The order link also closes a planted-id attack: without it in the comparison, a client could pre-record an unlinked movement at a work-order line's own future id, and the order's real consumption would be silently taken as a harmless replay instead of a conflict. A movement's history entry exposes `order_id`/`order_number` (`null` for a manual or offline-queued one) through a `LEFT JOIN` to `work_orders` by table-name string, never a Python import of that feature's models. Item creation is idempotent the same way via a client-generated item id, and its `initial_stock` is always recorded as an `adjust` movement with a deterministic id derived from the item id — even when the initial stock is 0 — so replaying item creation never double-applies the initial stock.

Negative stock is allowed and flagged (`needs_review`/`is_low` on the item), never blocked: a mechanic mid-job must not be stopped by the app, and a queued offline movement must always apply once it reaches the server. Search is accent-insensitive via an `IMMUTABLE` plpgsql wrapper function, `taller_unaccent_lower`, used both for search filtering and for the name-uniqueness constraint.

### Offline

`recordMovement` (`web/src/features/inventory/commands.ts`) never calls the API directly — it only enqueues the movement into an IndexedDB outbox, then triggers a flush. `flushOutboxOnce` → `withFlushLock` (`web/src/features/inventory/offlineSync.ts`) sends the outbox's entries to the server FIFO, one at a time, serialized by a Web Locks–based mutex (with an in-tab `Promise` chain fallback where Web Locks aren't available, e.g. the test runner) — responses can never be reconciled out of order. Reading items (`fetchItemsFolded` / the single-item fetch in `hooks.ts`) runs inside that *same* lock and folds any still-pending outbox entries onto the fetched data, so a read can never land in the gap between a flush's PUT succeeding and it removing the entry, and a queued tap is never invisible because a refetch happened to win a race.

Creating or editing an item requires a live connection (disabled in the UI with a message when offline); only movements go through the outbox. Outbox entries are scoped by workshop id and only flush for the session's current workshop. The TanStack Query cache is persisted to IndexedDB for offline reads, capped at 7 days, busted on every build (`__APP_VERSION__` carries `package.json`'s version plus a per-build id — the git short SHA, or a build timestamp when git is unavailable — from `resolveBuildId` in `vite.config.ts`, so a deploy that changes a response shape never hydrates an older, incompatible cache), and cleared on logout. A render crash anywhere under `RequireSession` shows `AppErrorBoundary`'s Spanish screen (`router.tsx`'s `errorElement`); its "Recargar" drops the persisted query cache — never the outbox — before reloading, so a cached response the running code no longer understands can't crash the app again on the next load. Every query key holding one workshop's data starts with `workshopQueryKey(workshopId)` (`web/src/features/auth/hooks.ts`; inventory keys build on it in `web/src/features/inventory/hooks.ts`), so one workshop's cached data is never served to another's session; a login or registration removes every cached query that is not the session or the new workshop's own (the persister then rewrites IndexedDB without them), but never touches the outbox.

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
- jsdom implements neither `URL.createObjectURL`/`revokeObjectURL` nor a real anchor-click navigation; a test covering a download (e.g. `exportData.test.ts`) must stub `URL.createObjectURL`/`revokeObjectURL` itself and spy on `HTMLAnchorElement.prototype.click`, or it throws/warns instead of exercising the real download logic.
- `formatCents` inserts a non-breaking space (` `) between the currency symbol and the amount; `@testing-library/dom`'s text normalizer collapses it when matching rendered text, but only if the *expected* string also has a plain space — build it from `formatCents(...).replace(/ /g, " ")` (see `receipt/ReceiptBody.test.tsx`'s `money()` helper) rather than hardcoding a guessed literal.
- `taller_unaccent_lower` schema-qualifies `unaccent` because a `pg_dump` restores with an empty `search_path`.

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
- `openspec/changes/` — active spec-driven changes in progress: each change's `proposal.md`, capability `specs/`, `design.md` and `tasks.md`. A finished change moves to `openspec/changes/archive/<date>-<name>/` with its verify and archive reports (e.g. `2026-10-07-workshop-core`, the customers/vehicles, work orders and payments phases).
- `openspec/specs/` — the baseline specs for already-shipped capabilities, one folder per capability, promoted from a change's `specs/` when it is archived. Read these first to learn what a capability must do.
