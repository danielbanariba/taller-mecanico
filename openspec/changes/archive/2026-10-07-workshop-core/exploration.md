## Exploration: workshop-core (customers/vehicles → work orders+WhatsApp → payments/receipt/export)

### Current State

**API.** `api/src/taller/<feature>/` is hexagonal per feature (`identity`, `inventory`):

- `domain/`: entities and errors, no framework imports.
- `application/`: plain-function use cases and `Protocol` ports.
- `adapters/`: SQLAlchemy repositories, Pydantic schemas, FastAPI `router.py`.

`main.py` is the only place routers are mounted. Tenancy is enforced by `get_current_workshop_id`, which scopes every query and mutation.

Stock is an append-only movement ledger. `record_movement` (`api/src/taller/inventory/application/use_cases.py:307`):

- Takes `item_repo.get_for_update` before computing the new stock.
- Is idempotent by client-generated movement UUID. A replay matches on `{item_id, kind, quantity, note}`; a different payload is a real conflict (409).
- Never blocks negative stock. It only flags `needs_review`/`is_low` on the `Item` entity.

Item creation is idempotent the same way, via a client-generated item id. `initial_stock` always records an `adjust` movement with a deterministic id (`_initial_movement_id` = `uuid5(namespace, item_id)`), so a replay never applies it twice. Items are soft-archived (`archived_at`), never hard-deleted.

Search and name uniqueness both go through `taller_unaccent_lower`, an `IMMUTABLE` plpgsql wrapper. It backs a partial unique index that the SQLAlchemy models cannot express. That index is listed in `MIGRATION_ONLY_INDEXES` in `api/migrations/env.py:32`; otherwise `alembic check` and autogenerate would drop it. This already caused one regression (T9b in `odd/tasks/inventory-mvp-rebuild.md`). `LIKE` search escapes `%`/`_` explicitly.

Identity's `PhoneNumber.from_raw` (`api/src/taller/identity/domain/phone_number.py:30`) strips separators and an optional `+504` prefix. It then validates an 8-digit local number whose first digit is between 2 and 9 (`_FIRST_DIGITS = "23456789"`, line 16), so landlines starting with 2 are already accepted. An earlier version of this exploration said "3/7/8/9", which was wrong. It discards the original formatting and stores only the clean digits. The phone is currently a mandatory field on `User`.

**Web.** `web/src/features/<feature>/` holds containers, presentational components, one `api.ts` and one `copy.ts` per feature. `web/src/shared/ui/` is the shared atomic kit (`Button`, `Spinner`, `Alert`, `TextField`, `Chip`, `Dialog`, `LinkButton`, ...).

- **Query keys.** `workshopQueryKey(workshopId)` (`web/src/features/auth/hooks.ts:18`) prefixes every workshop-scoped TanStack key. Login and register (`startSession`) drop every cached query that isn't the session or the new workshop's own.
- **Persisted cache.** The query cache is persisted to IndexedDB (`idbPersister.ts`) with a 7-day `maxAge` and is version-busted via `__APP_VERSION__`. It uses `shouldDehydrateMutation: false`, because a resumed paused mutation would have no transport.
- **Copy.** `copy.ts` holds every Spanish string for its feature, plus a map from API error `code` to Spanish message (`getAuthErrorMessage`/`getInventoryErrorMessage`). The API itself only ever returns English `detail` codes.

The offline outbox (`web/src/features/inventory/outbox.ts` + `offlineSync.ts`) is FIFO and single-flight:

- `flushOutboxOnce` → `withFlushLock` serializes via the Web Locks API, with an in-tab `Promise`-chain fallback for environments without it (e.g. the test runner).
- A send stalled for more than 20s is a `network_error`, not a silent hang.
- Reads (`fetchItemsFolded`) run inside the *same* lock, so a refetch can never land between a successful PUT and the outbox's removal of that entry.
- Item create/edit require a live connection today (disabled in the UI with a message when offline). **Only movements go through the outbox.**

There is **no shared app shell or navigation today**. `router.tsx` nests `InventoryPage`/`NewItemPage`/`ItemDetailPage`/`EditItemPage` directly as children of `RequireSession`'s `<Outlet/>`, and `InventoryPage` renders its own header and logout button. Adding Clientes and Órdenes as new top-level sections needs a shared shell, not just more sibling routes.

### Affected Areas

- **API, new features:**
  - `api/src/taller/customers/{domain,application,adapters}/*`: phase 1 (Customer + Vehicle).
  - `api/src/taller/workorders/{domain,application,adapters}/*`: phase 2. Its use cases call `taller.inventory.application.use_cases.record_movement` directly, the first cross-feature application-layer dependency in this codebase.
- **API, existing inventory:** `api/src/taller/inventory/domain/entities.py`, `application/ports.py` and `adapters/{repositories.py,models.py}`. Phase 2 adds nullable `order_id`/`order_line_id` to `StockMovement`, so an item's history can show which order consumed it.
- **API wiring and migrations:**
  - `api/src/taller/main.py`: mount the new routers.
  - `api/migrations/env.py` (`MIGRATION_ONLY_INDEXES`) and `api/migrations/versions/*.py`: new tables and partial indexes per phase.
- **API, reused unchanged:** `api/src/taller/identity/domain/phone_number.py`, for the customer's optional phone. Validate only when a value is present.
- **Web:**
  - `web/src/features/customers/*` and `web/src/features/workorders/*`: new, following the inventory shape (`api.ts`, `copy.ts`, `hooks.ts`, container/presentational screens).
  - `web/src/app/router.tsx` plus a new `web/src/app/AppShell.tsx`: a mobile bottom-nav shell (Inventario / Clientes / Órdenes) wrapping `RequireSession`'s children. The logout action moves there.
- **Demo:** `deploy/demo/seed-demo-account.sh`, extended with the same deterministic-UUIDv5-per-fixed-key idempotent seeding idiom already used for items.

### Approaches / Open Decisions

#### 1. Plate normalization and uniqueness per workshop

**Option 1: DB-function partial index (mirror item name).** Add an `IMMUTABLE` SQL normalize function plus a partial unique index over it.

- Pros: consistent with the one existing precedent; keeps the plate exactly as typed for display.
- Cons: a second SQL function to maintain and list in `MIGRATION_ONLY_INDEXES`. Item names needed this because they must keep their display casing and accents while folding for comparison; a plate has no such display requirement.
- Effort: Medium.

**Option 2: normalize in Python at write time and store only the normalized form.** Strip separators, uppercase, then use a plain partial unique index `(workshop_id, plate) WHERE archived_at IS NULL AND plate IS NOT NULL`.

- Pros: mirrors `PhoneNumber.from_raw`, where normalize-and-discard-original is already an established idiom. No new SQL function; trivial index.
- Cons: the user's original formatting (e.g. dashes) isn't kept for display. That is acceptable: plates have no stylistic reason to preserve input formatting.
- Effort: Low.

**Recommendation:** Option 2. Make `plate` nullable, because not every intake vehicle is plated (e.g. a just-imported car). The partial index guards only non-null values, so an unplated vehicle can still be entered without blocking the workflow.

#### 2. Human-readable order numbers per workshop (concurrency-safe)

Use a `workshop_counters` table, one row per workshop, bumped with a single atomic `UPDATE workshop_counters SET value = value + 1 WHERE workshop_id = :id RETURNING value`. The `UPDATE` takes the row lock implicitly. This is the same contention class already proven safe in this codebase for login throttling (`get_for_update` row lock) and item stock.

The alternative, per-workshop native Postgres `SEQUENCE` objects created dynamically, is rejected. It is operationally messy at scale (one sequence object per workshop, no clean cleanup story) and has no real benefit over a counter table.

**Recommendation:** the counter table with an atomic `UPDATE ... RETURNING`.

#### 3. When a work order consumes stock

- **Consume at quote/approval.**
  - Pros: simple, one trigger point.
  - Cons: a quote may never be approved, so this removes stock for work that may never happen.
- **Consume at delivery/completion.**
  - Pros: fewest ledger writes.
  - Cons: stock stays *wrong* while the mechanic has already pulled the part mid-job. That contradicts the ledger's whole purpose ("always know what's on hand") and risks selling the same part to someone else.
- **Consume when work starts (status → "in progress").**
  - Pros: stock reflects reality the moment the part leaves the shelf; consistent with "never block mid-job".
  - Cons: needs reversal logic for edits and cancellation after that point.

**Recommendation:** consume when work starts, via the existing idempotent `record_movement`, for every inventory-sourced part line. Retries and replays stay safe because every movement id is deterministic, the same idiom as `_initial_movement_id`:

- An edit after that point becomes a new delta movement (`in`/`out`, quantity = the difference) with id `uuid5(namespace, f"{order_id}:{line_id}:edit:{revision}")`.
- A cancellation becomes a reversal movement with id `uuid5(namespace, f"{order_id}:{line_id}:reversal")`.

Negative stock still only flags `needs_review`; it never blocks.

**Linking movements to orders:** add nullable `order_id`/`order_line_id` plain UUID columns to `inventory_movements`. They may be FK-constrained at the DB level only, with no code-level import from inventory into work orders. Do not encode the reference in the existing free-text `note` field: a structured column is queryable ("show every movement this order caused"), and `note` is not.

#### 4. Offline boundary for the new writes

- **Online-only**, the same treatment as item create/edit today (disabled in the UI with a message): customer create/edit, vehicle create/edit, work order create/edit/status change, and payment recording. The outbox's idempotent-replay design is movement-shaped and single-entity. Extending it to multi-entity writes introduces FK-existence races the current design doesn't handle, e.g. an order referencing a vehicle that was created offline and hasn't synced yet.
- **The stock movement a work start triggers.** The order's own status write stays online-only. The movement it triggers could still flow through the existing outbox unchanged, since it's just another movement tagged with `order_id`, if "start work" is ever allowed offline later.
- **Reads** (customer, vehicle and order lists and details): the same persisted-cache pattern with `workshopQueryKey`-prefixed keys, so they stay readable offline exactly like inventory today.

#### 5. WhatsApp sharing

- **Link format** for Honduras: `https://wa.me/504<8-digit-number>?text=<url-encoded summary>`. Hide or disable the share action when the customer has no phone, since the phone is optional.
- **Photos via Web Share API level 2** (file sharing). Feature-detect with `typeof navigator.canShare === "function" && navigator.canShare({ files })`. It is supported on Android Chrome, where level 2 file sharing has shipped for several Chrome versions, and on iOS Safari 15+.
- **Fallback:** where file sharing is unsupported (desktop browsers, older mobile browsers), open the text-only `wa.me` link in a new tab. That path has no photo attachment.
- **No WhatsApp Business API** anywhere in this design. Everything is client-side URL construction plus the standard Web Share API, so there is no backend integration, no approval process and no recurring cost.

#### 6. Receipt printing

- Two independent printable layouts, each its own route/component, because that keeps the CSS simpler than one conditional ruleset:
  - 58mm thermal via `@page { size: 58mm auto; margin: 2mm; }` with a compact font.
  - A standard full-page layout for a regular printer.
- Both **must** carry a visible "DOCUMENTO NO FISCAL — No válido como factura" label. SAR/CAI fiscal invoicing is explicitly out of scope, and this must never be mistaken for a tax document.

#### 7. CSV export

- A `StreamingResponse` with a `csv.writer` generator per entity, scoped through `get_current_workshop_id` exactly like every other inventory query (never a client-supplied workshop id).
- Prepend a UTF-8 BOM (`utf-8-sig` encoding), so Excel on Windows renders Spanish accented characters correctly instead of mojibake.
- **One CSV per entity, bundled into a single ZIP** (`zipfile` + `BytesIO`) for a one-tap "export everything". A single CSV mixing differently-shaped entities (customers, vehicles, items, movements, orders, order lines, payments) isn't cleanly tabular; a ZIP of per-entity CSVs is the standard shape for a multi-entity export.

#### 8. Demo seeding

Grow `deploy/demo/seed-demo-account.sh` with the idiom already there: fixed keys → `uuidgen --sha1 --namespace @url --name "<namespace>/<key>"` → idempotent `POST`, safe to rerun. Grow it with each phase's own PR rather than all at once:

- Phase 1: customers and vehicles.
- Phase 2: orders referencing those vehicles and items.
- Phase 3: one sample payment.

### Architecture decision flagged for sdd-design

Work orders' use cases call inventory's `record_movement` directly: application to application, never reaching into inventory's `adapters` or ORM models. This is the **first cross-feature use-case dependency** in this codebase. Until now `inventory` and `identity` share only an *adapter*-level dependency (`get_current_workshop_id`/`get_current_user`), not an application-level one.

Recommend accepting the direct call. It is still hexagonal: domain and application boundaries are respected, and no feature reaches into another's adapters or database. An abstraction port purely to decouple two features inside one monolith isn't justified at this scope. `sdd-design` should confirm this explicitly as a decision.

Also left open for `sdd-design`/`sdd-propose`: the work order status enum itself. This exploration assumes something like quote → approved → in_progress → completed → delivered, plus cancelled, only because "in_progress" is the stock-consumption trigger. The full state machine needs to be pinned down there.

### Risks

- **Migration drift.** `api/tests/test_migrations.py` (`alembic check`) already caught a real regression once (T9b): autogenerate drops any new functional or partial index not declared in `MIGRATION_ONLY_INDEXES`. Every new table in this feature needs this checked explicitly.
- **Counter contention.** The new order-counter row is a fresh hot-row contention point under concurrent order creation for the same workshop. It needs a concurrency test, the same class as the existing login-throttle and stock-lock tests.
- **Phase 2 size and risk.** Phase 2 (work orders + stock consumption + WhatsApp) is the largest and riskiest slice, since it reaches into inventory's ledger. It is the phase most likely to need internal task-chaining under the 400-line PR review budget.
- **Bundle size.** New screens (WhatsApp share, print CSS, CSV export) should be lazy-loaded (`React.lazy`/dynamic import) rather than bundled into the main chunk. That keeps the PWA app-shell precache lean for users on Honduran mobile networks.
- **Data leaving the app.** CSV export and WhatsApp sharing both move data outside the app (a downloaded file, a chat message). That is not a tenancy bug by itself, but export must only ever scope by `get_current_workshop_id`, never a client-supplied id, exactly like every existing inventory query.
- **Test surface.** The test strategy stays the same in kind but grows in surface. pytest needs the real Postgres `db_session` SAVEPOINT-rollback fixture for every new repository test. vitest/MSW needs a handler for every new endpoint, or `onUnhandledFrame: "error"` fails loudly. Both disciplines are already proven; they just need to cover three new feature areas.

### Ready for Proposal

Yes. Scope and phase boundaries are already approved by the user. Each open design question above has a concrete recommendation: plate normalization, order numbering, stock-consumption timing and movement linking, the offline boundary, WhatsApp/print/export mechanics, and demo seeding.

`sdd-propose` should carry these recommendations forward. `sdd-design` should pin down the work-order status state machine and formally record the work-orders → inventory cross-feature call as an accepted architecture decision.
