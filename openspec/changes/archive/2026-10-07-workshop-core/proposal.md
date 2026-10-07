# Proposal: Workshop core (customers and vehicles, work orders with WhatsApp sharing, payments and export)

Projects touched: **api** and **web** in every phase, plus `deploy/demo/` (seed script) in every phase.

## Intent

The inventory MVP is shipped and running on the public demo. The next roadmap step (`odd/tasks/inventory-mvp-rebuild.md`) is customers, vehicles, quotes and work orders that consume stock. The practitioner research (`docs/research/Software que aman los mecánicos.md`) supports that order and changes one thing about its contents:

- **The core is not optional.** Inventory, work orders, customer and vehicle history, and quotes form the "must-have" combo in every product analyzed, at every price point and in every market, from Tekmetric at US$400/month to TTN Garage at US$51/year to the free RAMP (section "¿Inventario primero sigue siendo la apuesta correcta?").
- **WhatsApp sharing moves forward.** Showing the customer a photo and a simple message with the work and its price, over the channel they already have open, is the most-cited trust mechanism in every market studied. In the US it is digital inspection with SMS approval. In India, Senegal and Ghana it is literally WhatsApp. It needs no new infrastructure. The research's first prioritized implication is to ship quote sharing over WhatsApp *with* quotes and work orders, not later next to user roles and password reset. Spanish-language apps with real traction already build it in from the start ("Gestión Taller Mecánico" on Google Play).
- **Fiscal invoicing stays decoupled and last** (implication 2). A Spanish-speaking reviewer treats certified invoicing as a desirable upgrade ("si lo agregan será un programa 10/10"), not as a precondition, and none of the nine documented abandonment stories was caused by invoicing. That is why the receipt in this change is explicitly non-fiscal.
- **Easy data export is a retention guarantee** (implication 4). Forced migrations and data held hostage were the most consistent abandonment triggers across nine paid products, for example "5 years' worth of data essentially stuck" after Shopmonkey 2.0, or Protractor charging a cancelled customer to see their own archived data. A one-tap CSV export is cheap now and expensive to retrofit.
- **No feature parity with US suites** (implication 3). Full digital inspection, card payment links and licensed labor guides serve a buyer who already bills over US$1M/year, not this product's customer.

**Why now:** the inventory ledger, tenancy, persisted offline reads and the public demo with a seeded account already exist, so this change builds on proven plumbing. The research also states that no Honduran or Central American mechanic's voice exists in any indexed source. Real validation has to come from 4–5 Honduran mechanics using the live demo, so each phase ships to the demo with seed data and becomes the vehicle for that validation.

**Success looks like:** a shop owner on a phone can register a customer and their vehicle, open a work order with labor and parts, send the quote over WhatsApp, start the work and see stock drop, take payment, hand over a clearly non-fiscal receipt, check the day's cash, and export everything to Excel at any time.

## Scope

Delivered as three phases, **one PR per phase**, a split agreed with the user before it was made. Each phase deploys to the public demo and extends `deploy/demo/seed-demo-account.sh` idempotently. Phase N+1 builds on phase N.

### In Scope

**Phase 1: customers, vehicles and the app shell** (branch `feat/workshop-core-customers`)

- Customers. Create, edit, archive (soft, like items), list, and search accent-insensitively by name or phone.
- **The customer's phone is optional.** When present, it is validated and normalized by the existing `PhoneNumber` value object, unchanged: separators and an optional `+504` are stripped, 8 digits are stored, and the first digit must be 2–9. A number starting with 2 is a landline; any other is treated as a mobile, so phase 2 can offer WhatsApp only for mobiles. Login phone rules for users (`api/src/taller/identity/domain/phone_number.py`) are **not** changed.
- Vehicles, which belong to one customer. Create, edit, archive and list per customer, plus a vehicle detail screen.
- **Plates are optional** and normalized: uppercase, separators removed, only the normalized form is stored. A plate is unique per workshop among active vehicles. An unplated vehicle is always allowed.
- A mobile bottom-nav app shell (`Inventario · Clientes · Órdenes`) that wraps every protected route. Logout moves from `InventoryPage` into the shell.
- Every read is workshop-scoped through `get_current_workshop_id`, uses `workshopQueryKey`-prefixed query keys, and stays readable offline from the persisted cache. Every write is online-only: disabled with a Spanish message when offline, the same treatment item create/edit gets today.
- Create endpoints accept client-generated ids and are idempotent like item creation, which the seed script relies on.
- The demo seed adds sample customers, a mix of mobile, landline and no phone, with cars and motorcycles, some unplated.

**Phase 2: work orders, quote lines and WhatsApp sharing**

- Work orders for a customer's vehicle, each with a human-readable number from a per-workshop counter table. The number comes from an atomic `UPDATE … RETURNING`, and a replayed idempotent create never consumes a second number.
- Three kinds of quote line, with quantities, unit prices and order totals in Lempiras:
  - **Labor.**
  - **Inventory part**, linked to an `Item`. These lines consume stock.
  - **External part**, bought outside the shop. Free text, no stock effect.
- A status lifecycle. **The state machine is left to `sdd-design`** (see Approach). The exploration's working assumption is quote → approved → in_progress → completed → delivered, plus cancelled.
- **Stock consumption.** Inventory part lines post `out` movements through the existing `record_movement` when the order enters the in-progress state.
  - Edits after that point post delta movements.
  - Cancellation posts reversal movements.
  - Every movement id is deterministic (`uuid5`, the same idiom as `_initial_movement_id`), so retries never double-apply.
  - Negative stock is still flagged, never blocked.
- `inventory_movements` gains nullable `order_id` and `order_line_id` columns. An item's history shows which order consumed it.
- **WhatsApp sharing**, offered only when the customer's phone is a mobile:
  - The action opens a `https://wa.me/504<number>?text=…` link with a prefilled Spanish summary of the order.
  - Where `navigator.canShare({ files })` is supported, the Web Share API shares photos the user picks or takes on the device at share time, together with the summary.
  - Elsewhere it falls back to the text-only `wa.me` link.
  - Photos are never uploaded to or stored by the app.
- Vehicle and customer detail screens list their orders, which makes the vehicle history visible.
- The demo seed adds orders in several states for the seeded vehicles and items. At least one is in progress, so its stock effect shows.

**Phase 3: payments, the non-fiscal receipt, the daily cash summary and the export**

- Recording payments against a work order, with the order's paid total and balance due.
- Two printable receipt layouts, each its own lazy-loaded route: 58 mm thermal (`@page { size: 58mm auto }`) and full page. Both carry the visible label **"DOCUMENTO NO FISCAL — No válido como factura"**.
- A daily cash summary: the day's payments and totals for the current workshop.
- **"Exportar todo"**: a ZIP of per-entity CSVs (customers, vehicles, items, movements, orders, order lines, payments), each UTF-8 with a BOM so Excel on Windows renders accents correctly. It is scoped only by `get_current_workshop_id`, never by a client-supplied id.
- The demo seed adds at least one sample payment.

### Out of Scope

- SAR/CAI fiscal invoicing, RTN/CAI fields, or anything that could be mistaken for a tax document.
- Multi-user workshops, roles and permissions.
- Password reset.
- WhatsApp Business API, or any server-side messaging integration.
- Offline writes for customers, vehicles, orders and payments. The outbox stays movement-only and unchanged.
- Storing photos on orders or items (photo attachments), and full digital vehicle inspection (DVI) checklists.
- Card payment links or any payment-processor integration.
- Changes to login phone validation or to the identity feature's rules.
- Service reminders, appointment scheduling, labor-time guides, and CSV import.

## Capabilities

`openspec/specs/` holds no baseline specs yet (only `.gitkeep`), so every capability below is new. Each spec must state its tenancy (`workshop_id` scoping), idempotency and offline-boundary behavior, per `openspec/config.yaml` `rules.specs`.

### New Capabilities

- `app-shell-navigation` (phase 1): the bottom-nav shell over protected routes, its three destinations, the logout relocated into it, and the active-tab state.
- `customers` (phase 1): customer records, the optional landline-or-mobile phone with its normalization and validation, the mobile flag, archiving, accent-insensitive search, and the online-only write boundary.
- `vehicles` (phase 1): vehicles owned by a customer, the optional normalized plate unique per workshop among active vehicles, archiving, and the vehicle detail.
- `work-orders` (phase 2): orders for a vehicle, per-workshop numbering, quote lines of three kinds, totals, and the status lifecycle defined by design.
- `work-order-stock-consumption` (phase 2): when and how inventory part lines post movements, deltas, reversals, deterministic movement ids, and the order linkage on `inventory_movements` shown in an item's history. This capability carries the inventory ledger's behavior change, because no inventory baseline spec exists to delta against.
- `whatsapp-sharing` (phase 2): the `wa.me` link and its prefilled Spanish summary, the mobile-only availability, and Web Share with photos plus its fallback.
- `payments` (phase 3): recording payments on an order, paid total, and balance due.
- `non-fiscal-receipt` (phase 3): the 58 mm and full-page layouts and the mandatory non-fiscal label.
- `daily-cash-summary` (phase 3): per-day payment totals for the current workshop and their day boundary.
- `data-export` (phase 3): the workshop-scoped ZIP of per-entity UTF-8-BOM CSVs.

### Modified Capabilities

None. No baseline specs exist in `openspec/specs/`. Behavior changes to existing inventory surfaces are specified inside the new capabilities: the movement linkage and item history in `work-order-stock-consumption`, and the logout relocation in `app-shell-navigation`.

## Approach

The approach carries the exploration's recommendations (`openspec/changes/workshop-core/exploration.md`), all accepted by the user.

**API: new hexagonal features, the same shape as `inventory`.**

- `taller/customers/` holds customers and vehicles, and `taller/workorders/` holds orders, lines and the counter.
- Payments and the cash summary go in a phase 3 feature. Export is a read-only module that composes per-feature read ports. `sdd-design` fixes the exact package boundaries.
- Routers are mounted only in `taller/main.py`.
- Every query and mutation is scoped by `get_current_workshop_id`.
- Creates are idempotent through client-generated ids: a replay with the same payload is a no-op, and a different payload is a 409.

**Customer phone.**

- The customer phone reuses identity's `PhoneNumber` unchanged. It already accepts landlines, because its first-digit set is 2–9 (`_FIRST_DIGITS = "23456789"`, `api/src/taller/identity/domain/phone_number.py:16`).
- The customers domain derives `is_mobile` (first digit is not 2), which gates the WhatsApp action.
- `PhoneNumber` and the login rules stay untouched.
- Correction: an earlier draft planned a customer-specific value object because the exploration said `PhoneNumber` accepted only 3/7/8/9. The code shows otherwise.

**Plates.**

- Normalized in Python at write time, and only the normalized form is stored.
- The uniqueness index `(workshop_id, plate) WHERE archived_at IS NULL AND plate IS NOT NULL` is declared on the model with `postgresql_where`, so `alembic check` sees it and no `MIGRATION_ONLY_INDEXES` entry is needed.

**Order numbers.** A `workshop_counters` table bumped with one atomic `UPDATE … SET value = value + 1 … RETURNING value`. The row lock is implicit. Per-workshop `SEQUENCE` objects are rejected.

**Stock consumption.**

- Work orders call `taller.inventory.application.use_cases.record_movement` directly. This is the first cross-feature application-to-application dependency. It never reaches into inventory's adapters or models. `sdd-design` must record it as an accepted architecture decision.
- Movement ids are `uuid5` derived from order, line and revision or reversal.
- The order's status change and its movements commit in one transaction.
- Item rows are locked in a deterministic order.

**State machine: deferred to `sdd-design`.** The design must define the states, the allowed transitions, and which states allow line edits and (in phase 3) payments. It must also satisfy these constraints:

1. Exactly one transition triggers stock consumption.
2. Cancellation after consumption reverses it.
3. Repeating a transition is idempotent.

**Web: one new feature folder per area, in the existing shape.**

- `web/src/features/customers/` and `web/src/features/workorders/` follow the inventory shape: `api.ts`, `copy.ts`, `hooks.ts`, containers and presentational components.
- The shared kit in `web/src/shared/ui/` is reused.
- Every Spanish string, including the WhatsApp summary template and the receipt label, lives in `copy.ts`.
- The API returns only English error codes.
- A new `web/src/app/AppShell.tsx` wraps `RequireSession`'s outlet in `router.tsx`.
- Rarely used, heavier screens are code-split with `React.lazy`: print layouts, share, export and the cash summary. This keeps the PWA precache lean on Honduran mobile networks (bundle-dynamic-imports and bundle-conditional from `vercel-react-best-practices`).

**Offline boundary.** Reads use the persisted query cache with `workshopQueryKey`-prefixed keys. New writes are online-only. The outbox, its Web Locks mutex and the movement replay path are not modified.

**Postgres hygiene** (from `postgresql-best-practices`):

- Explicit indexes on every new FK and `workshop_id` column, because Postgres does not index FKs automatically.
- `ON DELETE RESTRICT` with soft-archive instead of hard deletes.
- `numeric(12,2)` for money.
- New columns on `inventory_movements` are nullable, so adding them is a metadata-only change with no table rewrite.

**Delivery.** Each phase is one PR. Each will exceed the 400-line review budget (see the forecast), so under `ask-on-risk` the orchestrator asks the user for the chain strategy before apply, inside each phase.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `api/src/taller/customers/{domain,application,adapters}/` | New (P1) | Customer and Vehicle entities, the phone value object, plate normalization, ports, repositories, schemas, router |
| `api/src/taller/workorders/{domain,application,adapters}/` | New (P2) | WorkOrder, its lines, the status machine, the counter, stock-consumption use cases, router |
| Phase 3 payments/cash module and export module under `api/src/taller/` | New (P3) | Payments, the daily summary query, the ZIP/CSV streaming endpoint (package names fixed by design) |
| `api/src/taller/inventory/{domain/entities.py,application/ports.py,application/use_cases.py,adapters/models.py,adapters/repositories.py,adapters/schemas.py}` | Modified (P2) | Nullable `order_id`/`order_line_id` on movements; item history exposes the order link |
| `api/src/taller/main.py` | Modified (P1–P3) | Mount the new routers |
| `api/migrations/versions/*.py`, `api/migrations/env.py` | New/Modified (P1–P3) | One migration per phase, each with a working `downgrade()`; `MIGRATION_ONLY_INDEXES` only if an index cannot be declared on a model |
| `api/tests/{customers,workorders,…}/` | New (P1–P3) | Domain unit tests, API integration tests on real Postgres, concurrency tests (counter, stock locks) |
| `web/src/app/router.tsx`, `web/src/app/AppShell.tsx` | Modified/New (P1) | Shell with bottom nav; new routes per phase |
| `web/src/features/inventory/InventoryPage*` | Modified (P1) | Header/logout move into the shell |
| `web/src/features/inventory/` (item detail/history) | Modified (P2) | Show the order a movement belongs to |
| `web/src/features/customers/` | New (P1) | List, detail, forms for customers and vehicles |
| `web/src/features/workorders/` | New (P2, P3) | Order list/detail/editor, line editor with item picker, status actions, WhatsApp share; payments, receipts, cash summary, export in P3 |
| `web/src/test/handlers.ts` | Modified (P1–P3) | MSW handlers for every new endpoint |
| `deploy/demo/seed-demo-account.sh`, `deploy/demo/README.md` | Modified (P1–P3) | Idempotent seeding of the new entities; document what the demo account contains |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Migration drift: autogenerate drops an index the models cannot express (as in T9b) | Med | Declare partial indexes on models with `postgresql_where`; `api/tests/test_migrations.py` (`alembic check`) must pass in every phase; any unexpressible index goes into `MIGRATION_ONLY_INDEXES` |
| Order-counter hot row under concurrent order creation in one workshop | Low | Single atomic `UPDATE … RETURNING`; a concurrency test like the login-throttle and stock-lock tests; replayed creates do not bump the counter |
| Deadlock when two orders lock the same items in different order at work start | Med | Lock items in a deterministic order (sorted item id) inside one transaction; concurrency test |
| Stock double-applied or lost on retries, edits or cancellation | Med | Deterministic `uuid5` movement ids per order/line/revision/reversal; the existing idempotent `record_movement`; tests for replay, edit-delta and cancel-reversal |
| Adding `order_id`/`order_line_id` changes `record_movement`'s replay comparison (`{item_id, kind, quantity, note}`) | Med | `sdd-design` decides whether the link fields join the idempotency payload; the existing outbox movement path stays byte-compatible (fields optional) |
| First cross-feature use-case dependency erodes hexagonal boundaries | Low | Application-to-application call only; recorded as an explicit design decision; no imports into inventory adapters/models |
| Phase 2 is the largest and riskiest slice (touches the inventory ledger) | High | Internal chained slices per `ask-on-risk`; ledger changes land first, with tests, before UI |
| Web Share with files: some share targets drop the text when files are attached; support varies by browser | Med | Feature-detect with `navigator.canShare({ files })`; the `wa.me` text link is always available; verified on Android Chrome against the demo |
| Printing 58 mm from a phone depends on the printer's Android print service (many Bluetooth thermal printers need a vendor print app) | Med | Both layouts are plain browser print CSS verified in print preview/PDF; full-page layout is the guaranteed path; no printer SDK in scope |
| Daily cash summary off by the UTC offset (Honduras is UTC-6) | Med | Day boundaries computed in `America/Tegucigalpa`; test with payments near midnight local time |
| Data leaves the app (CSV export, WhatsApp) | Low | Export scoped only by `get_current_workshop_id`; tenancy tests on the export endpoint; WhatsApp is user-initiated per order |
| Receipt mistaken for a fiscal invoice | Low | The non-fiscal label is mandatory on both layouts and asserted in tests |
| Bundle growth hurts the PWA on mobile networks | Low | `React.lazy` for print, share, export and summary screens; check `npm run build` chunk sizes per phase |
| Test surface grows across three areas (MSW `onUnhandledFrame: "error"` fails on any missing handler) | Med | One handler per new endpoint in `web/src/test/handlers.ts`; every repository test uses the SAVEPOINT `db_session` fixture |
| Demo testers share one account and see each other's customers and orders | Low | Already true for inventory and documented in `deploy/demo/README.md`; seed data uses obviously fictional names and phones |

## Rollback Plan

The demo database (`taller-demo-db`, port 5441) is separate from the dev database (`docker compose` `db`, 5440). The demo runs from the detached worktree `/home/banar/Desktop/taller-mecanico-worktrees/demo` (`deploy/demo/README.md`). Each phase follows the same procedure:

1. **Before deploying the phase:** dump the demo database (`docker exec taller-demo-db pg_dump -U taller taller_demo > taller_demo-<phase>.sql`) and record the current `alembic current` revision and deployed commit.
2. **To roll back:** with the phase's code still checked out, because the downgrade lives in its revision, run `uv run --frozen --env-file ~/.config/taller-mecanico/demo.env alembic downgrade <previous revision>`. Then `git checkout --detach <previous commit>` in the demo worktree, rebuild the web with `demo.env` loaded, and restart both units. On `main`, revert the phase's merge commit.
3. **Order:** later phases roll back first. Phase 3 depends on phase 2's orders, and phase 2 depends on phase 1's vehicles. Rolling back phase 1 while phase 2 is deployed is not possible.
4. **Client side:** older builds never read the new query keys, so persisted cache entries for new entities are inert, and logout clears them. The service worker auto-updates to the rolled-back build. The outbox is untouched by all three phases.

Phase-specific effects:

- **Phase 1:** `downgrade()` drops the vehicles and customers tables and their indexes. No existing table changes, so inventory is unaffected. Tester-entered customers and vehicles are lost unless restored from the dump. The web returns to per-page header and logout.
- **Phase 2:** `downgrade()` drops the FKs, then `order_id`/`order_line_id` on `inventory_movements`, then the work order lines, work orders and `workshop_counters` tables. **Movements already posted by orders stay in the ledger**, so every item's cached stock remains equal to its ledger sum. They only lose their order link. Order data is lost unless restored from the dump.
- **Phase 3:** `downgrade()` drops the payments table. Receipts, the cash summary and the export are read-only and have no schema of their own. Payment data is lost unless restored from the dump.

Each phase's `downgrade()` is exercised locally (upgrade → downgrade → upgrade on the dev database) before the PR is opened.

## Dependencies

- Phase 2 requires phase 1, and phase 3 requires phase 2. Each phase is merged and deployed before the next one is applied.
- The existing inventory ledger (`record_movement`, `get_for_update`, deterministic-id idiom) and tenancy dependency (`get_current_workshop_id`).
- The existing demo deployment and seed idiom (`deploy/demo/`).
- No new external services. The Python stdlib (`csv`, `zipfile`) covers the export, and the browser's Web Share API and `wa.me` cover sharing. No new runtime dependency is expected. If design proposes one, it must be justified there.

## Size Forecast (rough, authored lines = additions + deletions, tests included)

| Phase | API | Web | Seed/docs | Total | ≈400-line slices |
|------|-----|-----|-----------|-------|------------------|
| 1: customers, vehicles, shell | ~1,300 (incl. ~600 tests) | ~1,700 (incl. ~600 tests) | ~100 | **~3,000–3,600** | ~8–9 |
| 2: work orders, stock, WhatsApp | ~2,200 (incl. ~1,000 tests) | ~2,600 (incl. ~900 tests) | ~150 | **~4,500–5,500** | ~11–14 |
| 3: payments, receipt, summary, export | ~1,500 (incl. ~700 tests) | ~1,700 (incl. ~600 tests) | ~80 | **~3,000–3,800** | ~8–10 |

Every phase exceeds the 400-line review budget. Under `ask-on-risk` the orchestrator must ask the user for the chain strategy (`stacked-to-main` or `feature-branch-chain`) before applying each phase. `sdd-tasks` produces the exact forecast and guard lines.

## Product Decisions (resolved by the user)

1. **Payments:** the methods are cash (efectivo), transfer (transferencia), card (tarjeta) and other (otro). An order accepts several partial payments (a deposit plus the balance). The daily cash summary breaks totals down by method, so the owner can reconcile the cash drawer.
2. **Taxes:** line prices are final amounts. There is no ISV computation or breakdown, consistent with the non-fiscal scope.
3. **Órdenes tab in phase 1:** the tab is visible and shows a "Próximamente" empty state until phase 2 ships.
4. **Cash-summary day boundary:** a fixed `America/Tegucigalpa` calendar day. There is no per-workshop timezone setting.
5. **Orders without a vehicle:** every work order belongs to a vehicle of one of the workshop's customers. Counter sales without a vehicle are out of scope.

## Success Criteria

Each criterion is observable on the public demo with the seeded demo account (`9999-9999`) after the phase is deployed and seeded, and also covered by automated tests.

**Phase 1**

- [ ] Every protected screen shows the bottom nav `Inventario · Clientes · Órdenes`. Logout works from the shell, and every existing inventory flow (list, detail, movements, count, offline taps) still works.
- [ ] Clientes lists the seeded customers. Searching `maria` finds `María`.
- [ ] A customer saved with phone `+504 2234-5678` is stored as `22345678` and recognized as a landline. `9876-5432` is recognized as a mobile. An empty phone is accepted. A 7-digit number or one starting with `1` is rejected with a Spanish message.
- [ ] A vehicle saved with plate `hab-1234` shows `HAB1234`. A second active vehicle with `HAB 1234` in the same workshop is rejected with a Spanish duplicate message. Several unplated vehicles are allowed.
- [ ] With the device offline, a previously visited customer list and detail still render, and create/edit actions are disabled with a message.
- [ ] Rerunning the seed script creates no duplicates.
- [ ] `alembic check`, ruff, pytest, eslint, typecheck, vitest and build all pass.

**Phase 2**

- [ ] Creating an order for a seeded vehicle assigns the workshop's next number. Double-submitting the same create does not skip or duplicate a number.
- [ ] An order with one labor line, one inventory part line and one external part line shows the correct total in Lempiras.
- [ ] Moving an order to the in-progress state lowers the linked item's stock by the line quantity, and the item's history shows that movement linked to the order number. Editing the quantity afterward posts only the difference. Cancelling restores the stock. Retrying any of these never double-applies.
- [ ] For a customer with a mobile phone, "Compartir por WhatsApp" opens WhatsApp with a prefilled Spanish summary. On Android Chrome, attached photos are shared with it. A landline-only or phoneless customer is not offered the action.
- [ ] The vehicle detail lists that vehicle's orders.
- [ ] The seeded demo shows orders in several states, at least one in progress with its stock effect.

**Phase 3**

- [ ] Recording a payment on an order updates its paid total and balance due.
- [ ] Both receipt layouts (58 mm and full page) render in print preview with "DOCUMENTO NO FISCAL — No válido como factura" visible.
- [ ] The daily cash summary for today shows the seeded and newly recorded payments, bucketed by the Honduran local day.
- [ ] "Exportar todo" downloads a ZIP of per-entity CSVs that opens in Excel with accents intact and contains only the current workshop's data.
- [ ] Each phase's `downgrade()` succeeds locally (upgrade → downgrade → upgrade) before its PR is opened.
