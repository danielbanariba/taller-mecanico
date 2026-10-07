# Tasks: Workshop core (customers and vehicles, work orders with WhatsApp sharing, payments and export)

Change: `workshop-core` · Inputs: `proposal.md`, the ten capability specs under `specs/`, `design.md` (including "Resolved Questions" and "Sequencing inside each phase"). Each slice below is one of design's "Sequencing inside each phase" entries; task IDs are `P{phase}.S{slice}.T{task}`.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~3,000–3,600 (P1) + ~4,500–5,500 (P2) + ~3,000–3,800 (P3) ≈ **10,500–12,900 total**, authored lines (additions + deletions), per `proposal.md`'s Size Forecast |
| 400-line budget risk | **High** for every phase (each phase alone is 7–14× the 400-line budget) |
| Chained PRs recommended | Yes |
| Suggested split | 3 deliveries total (one PR-track per phase, as the user already agreed), each internally chained into the slices below (~400–900 authored lines per slice) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending — the orchestrator asks the user, per phase, after this forecast: `stacked-to-main` or `feature-branch-chain` (or an explicit `size:exception` to ship a phase as one PR) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Per-slice line estimate (planning estimate, not an exact diff count)

| Phase | Slice | Goal | Est. lines | Risk |
|---|---|---|---|---|
| P1 | S1 | API: migration (both tables), customers domain/use cases/router + tests | ~800 | High |
| P1 | S2 | API: vehicles (plate, uniqueness race, cascade archive) + tests | ~650 | High |
| P1 | S3 | Web: `AppShell`, `BottomNav`, router restructure, logout move, Órdenes placeholder + tests | ~450 | High |
| P1 | S4 | Web: customers list/search/create/edit/archive + tests | ~700 | High |
| P1 | S5 | Web: vehicle create/edit/archive/detail + tests | ~550 | High |
| P1 | S6 | Closing: seed, docs, `CLAUDE.md`, migration round-trip, real-browser check | ~150 | Low |
| **P1 total** | | | **~3,300** | **High** |
| P2 | S1 | API: ledger (migration incl. movement columns, work-order ORM models, `record_movement` link params/replay, history projection) + tests | ~900 | High |
| P2 | S2 | API: work-order domain, numbering, non-consuming lines, list + tests | ~850 | High |
| P2 | S3 | API: `change_status` + consuming-state reconciliation + tests | ~900 | High |
| P2 | S4 | Web: history order link, `workorders` api/hooks, list, read-only detail | ~750 | High |
| P2 | S5 | Web: new order flow, line editor, item picker | ~650 | High |
| P2 | S6 | Web: status actions, WhatsApp builders, lazy share sheet | ~550 | High |
| P2 | S7 | Closing: orders on customer/vehicle detail, seed, docs, migration round-trip, real-browser + Android check | ~400 | Medium |
| **P2 total** | | | **~5,000** | **High** |
| P3 | S1 | API: payments migration, `record_payment`, balance, void, cancellation guard + tests | ~750 | High |
| P3 | S2 | API: cash summary + timezone tests | ~450 | High |
| P3 | S3 | API: export (pure builder + endpoint tenancy tests) | ~600 | High |
| P3 | S4 | Web: payments on order detail | ~450 | High |
| P3 | S5 | Web: receipts (lazy routes, print CSS, measured 58 mm page) | ~600 | High |
| P3 | S6 | Closing: cash summary page, export action, shell "Más" menu, persistence filter, seed, docs, real-browser + print-preview check | ~550 | High |
| **P3 total** | | | **~3,400** | **High** |

### Suggested Work Units

Each slice below is one chainable work unit. If the user picks `stacked-to-main` or `feature-branch-chain` for a phase, each row becomes its own PR in that phase's chain (PR #1 base = `feat/workshop-core-customers`/the phase's tracker branch; PR #2 base = PR #1's branch; and so on, per slice order). If the user instead picks `size:exception` for a phase, all of that phase's rows land as sequential commits inside the one phase PR.

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| P1.S1 | Customers data layer + API | P1 chain #1 | `uv run pytest tests/customers/test_customers_api.py` | N/A — API-only, exercised through pytest | Drop `taller/customers/` package + migration `downgrade()` |
| P1.S2 | Vehicles API | P1 chain #2 | `uv run pytest tests/customers/test_vehicles_api.py` | N/A | Revert vehicles use cases/router/tests; migration already reversible from S1 |
| P1.S3 | App shell | P1 chain #3 | `npm test -- --run src/app/AppShell.test.tsx` | Manual: load any `/inventario/...` route, confirm nav renders | Revert `router.tsx`/`AppShell.tsx`; `InventoryPage` header restorable from git history |
| P1.S4 | Customers web | P1 chain #4 | `npm test -- --run src/features/customers` | Manual: create/search/archive a customer at 390×844 | Remove `web/src/features/customers/`; router entries revert |
| P1.S5 | Vehicles web | P1 chain #5 | `npm test -- --run src/features/customers` (vehicle specs) | Manual: create/edit a vehicle, duplicate-plate message | Remove vehicle containers/routes |
| P1.S6 | Phase 1 close | P1 chain #6 | full phase verification (below) | Real-browser check at 390×844 on demo | Revert seed/docs changes only; no schema change |
| P2.S1 | Ledger + link fields | P2 chain #1 | `uv run pytest tests/inventory/test_movement_order_link.py` | N/A | Migration `downgrade()` drops link columns; movements stay in ledger |
| P2.S2 | Work-order core + numbering | P2 chain #2 | `uv run pytest tests/workorders/test_work_orders_api.py tests/workorders/test_work_order_concurrency.py` | N/A | Revert `workorders/` application+router; models stay (used by S1) |
| P2.S3 | Status machine + reconciliation | P2 chain #3 | `uv run pytest tests/workorders/test_stock_consumption.py` | N/A | Revert `change_status`/reconciliation wiring; S2's non-consuming paths unaffected |
| P2.S4 | Web: history link, list, read-only detail | P2 chain #4 | `npm test -- --run src/features/workorders` | Manual: open Órdenes tab, see seeded orders | Remove workorders web list/detail |
| P2.S5 | Web: new order + line editor | P2 chain #5 | `npm test -- --run src/features/workorders` | Manual: create an order with 3 line kinds | Remove new-order/line-editor components |
| P2.S6 | Web: status actions + WhatsApp | P2 chain #6 | `npm test -- --run src/features/workorders` | Manual Android Chrome: share with photos | Remove `whatsapp.ts`/`ShareSheet`/`StatusActions` |
| P2.S7 | Phase 2 close | P2 chain #7 | full phase verification (below) | Real-browser + Android share check on demo | Revert seed/docs; later rollback drops P2 schema per `design.md` Migration/Rollout |
| P3.S1 | Payments API | P3 chain #1 | `uv run pytest tests/workorders/test_payments_api.py` | N/A | Migration `downgrade()` drops `payments` |
| P3.S2 | Cash summary API | P3 chain #2 | `uv run pytest tests/workorders/test_cash_summary.py` | N/A | Revert `daily_cash_summary` use case + route |
| P3.S3 | Export API | P3 chain #3 | `uv run pytest tests/export/` | N/A | Revert `taller/export/` package + mount |
| P3.S4 | Web: payments | P3 chain #4 | `npm test -- --run src/features/workorders` (payments) | Manual: record a partial payment | Remove payment components |
| P3.S5 | Web: receipts | P3 chain #5 | `npm test -- --run src/features/workorders` (receipt) | Manual: print preview both layouts at 390×844 | Remove receipt routes/components |
| P3.S6 | Phase 3 close | P3 chain #6 | full phase verification (below) | Real-browser + print-preview check on demo | Revert seed/docs; schema rollback per `design.md` |

---

## Phase 1: Customers, vehicles and the app shell

### Slice P1.S1 — API: customers data layer, domain, use cases, router (+tests)

- [x] **P1.S1.T1** Verify unconfirmed identifiers before writing any phase-1 code (no production change; this task's output gates every later task in this document). Confirmed this session via CodeGraph — re-confirm with one `Read` only if `git log` shows these files changed since:
  - `get_clock` is defined in `api/src/taller/identity/adapters/dependencies.py` and imported from there (e.g. `from taller.identity.adapters.dependencies import get_clock` in `api/src/taller/identity/adapters/router.py`).
  - **Identity has no reusable `invalid_phone` string code.** `RegisterRequest`/`LoginRequest` in `api/src/taller/identity/adapters/schemas.py` validate phone through a Pydantic `field_validator` (`_validate_phone`) that raises a plain `ValueError`; FastAPI turns that into a generic 422 whose `detail` is a list of validation issues, not the string `"invalid_phone"`. **Consequence:** `taller/customers` MUST mint its own `detail: "invalid_phone"` mapping in its own use case/router (catch `InvalidPhoneNumber` from `api/src/taller/identity/domain/errors.py` directly) — there is nothing to "reuse" at the HTTP layer, only the `PhoneNumber` value object itself (AD-8 still holds for the value object; its "reuse the code" hope does not).
  - `api/migrations/env.py` registers ORM metadata through side-effecting module imports: `import taller.identity.adapters.models` and `import taller.inventory.adapters.models` (both `# noqa: F401,E402`), and declares `MIGRATION_ONLY_INDEXES = frozenset({"ix_inventory_items_active_name"})`, checked in `include_object`. This slice adds `import taller.customers.adapters.models` to that same block; `MIGRATION_ONLY_INDEXES` is unchanged unless the fallback in `design.md` ("Migration-check fallback") is triggered.
  - The workshops table is named `workshops` (`WorkshopModel.__tablename__`, `api/src/taller/identity/adapters/models.py`).
  - `format.ts` (money/quantity/date formatting) lives at `web/src/features/inventory/format.ts` (`formatCents`, `parseLempirasToCents`, `centsToPlainAmount`, `formatDateTime`, `parseStockQuantity`, `MAX_STOCK`).
  - No item mutation in `web/src/features/inventory/hooks.ts` (`useCreateItem`, `useUpdateItem`) sets an explicit `networkMode` — they rely on TanStack Query's default `"online"` mode, paired with a UI-level `useOnlineStatus()` check disabling submit in `NewItemPage.tsx`/`EditItemPage.tsx`. New customers/vehicles mutations follow the same convention (no explicit `networkMode` override).
  - **Still open, confirm directly from `api/src/taller/inventory/adapters/router.py`'s `record_movement_route` with one bounded `Read` before Phase 2 Slice 1 (the first place these are reused):** the exact HTTP status codes `record_movement_route` maps `MovementIdConflict` and `StockOutOfRange` to. `design.md`'s API-surface tables already state 409 and 422 respectively (consistent with `ItemIdConflict`→409 and other bound violations→422 elsewhere in the same router); a CodeGraph caching quirk blocked re-reading the literal handler lines this session, so this is "very likely confirmed, re-check once" rather than unknown.

- [x] **P1.S1.T2** Create the package skeleton: `api/src/taller/customers/__init__.py`, `domain/__init__.py`, `application/__init__.py`, `adapters/__init__.py`.

- [x] **P1.S1.T3** Create `api/src/taller/customers/domain/entities.py`: `Customer` (with the `phone_is_mobile` property — `None` with no phone, else `phone[0] != "2"`, per AD-8), `Vehicle`, `VehicleType` (`car`, `motorcycle`, `other`). Both entities are declared now because the phase-1 migration (T6) creates both tables together; `Vehicle`'s own use cases land in Slice 2.

- [x] **P1.S1.T4** Create `api/src/taller/customers/domain/errors.py`: `CustomerNotFound`, `CustomerIdConflict`, `VehicleNotFound`, `VehicleIdConflict`, `PlateTaken`, `InvalidPlate` (all six declared now; the vehicle-specific ones are raised starting Slice 2).

- [x] **P1.S1.T5** Create `api/src/taller/customers/application/ports.py`: `CustomerRepository` and `VehicleRepository` (Protocols; `VehicleRepository` includes `get_many` for phase 2's `describe_vehicles`, per AD-12, even though it has no implementation yet).

- [x] **P1.S1.T6** Create the phase-1 migration `api/migrations/versions/<rev>_customers_and_vehicles.py`: `customers` and `vehicles` tables exactly as specified in `design.md`'s "Data model per phase → Phase 1" (columns, `ix_customers_workshop_id`, `ix_vehicles_workshop_id`, `ix_vehicles_customer_id`, `ck_vehicles_vehicle_type`, and the partial unique index `uq_vehicles_workshop_plate_active ON vehicles (workshop_id, plate) WHERE archived_at IS NULL AND plate IS NOT NULL`), with a working `downgrade()` (drop `vehicles` then `customers`). Add `import taller.customers.adapters.models` to `api/migrations/env.py` per T1.

- [x] **P1.S1.T7** Create `api/src/taller/customers/adapters/models.py`: `CustomerModel` and `VehicleModel` (both ORM models, matching T6's schema exactly, including the partial index declared with `postgresql_where` so `alembic check` sees it).

- [x] **P1.S1.T8 (RED)** Write `api/tests/customers/test_customers_domain.py`:
  - `phone_is_mobile` is `False` for `22345678`, `True` for `98765432`, `None` with no phone. **Defect it catches:** WhatsApp is offered to a landline, or the app crashes on a phoneless customer (phase 2 depends on this being right).
  Confirm these fail (no `Customer`/`phone_is_mobile` implementation satisfies them yet beyond T3's property — if T3 is already correct this test should pass immediately; if so, write it before T3 lands in version control history, i.e. run it once against a stash of T3 reverted, or accept GREEN-on-first-run only if T3 was written test-first in the same commit).

- [x] **P1.S1.T9 (GREEN)** Confirm T8 passes against T3's `Customer.phone_is_mobile` implementation; add any missing edge case T8 revealed.

- [x] **P1.S1.T10 (RED)** Write `api/tests/customers/test_customers_api.py` covering, before any use case/router exists:
  - Create with phone `+504 2234-5678` → stored `22345678`, `phone_is_mobile` `false`; a 7-digit phone or one starting with `1` → HTTP 422 `invalid_phone`. **Defect it catches:** the customer path skips `PhoneNumber` normalization, or invalid phones are persisted.
  - Create with no phone → saved, `phone_is_mobile` `null`. **Defect it catches:** an empty phone is rejected or crashes normalization.
  - Replaying an identical create (same id, same payload) → HTTP 200, one row; the same id with a different `full_name` → HTTP 409 `customer_id_conflict`, original unchanged. **Defect it catches:** a retry duplicates customers, or a conflicting replay silently overwrites data.
  - Editing only the name leaves phone/`phone_is_mobile` unchanged; editing a nonexistent or foreign id → HTTP 404 `customer_not_found`. **Defect it catches:** a partial-update bug clobbers omitted fields, or tenancy is unchecked on edit.
  - Archiving an active customer sets `archived_at` and removes it from the default listing; archiving again is a no-op that keeps the first `archived_at`. **Defect it catches:** a hard delete, or `archived_at` is re-stamped on a repeat archive.
  - `q=maria` finds `María`; `q=9876` finds `98765432`; `q=50%` matches the literal string `50%` (not a wildcard). **Defect it catches:** accent/case-sensitive search, the phone fragment not searched, or unescaped `LIKE` wildcards.
  - Workshop B's GET/PATCH/archive of workshop A's customer id → HTTP 404 `customer_not_found`, A's data unchanged. **Defect it catches:** a missing `workshop_id` filter leaks or mutates another tenant's data.

- [x] **P1.S1.T11 (GREEN)** Create `api/src/taller/customers/application/use_cases.py`: `create_customer` (idempotent by client id, replay-before-conflict per the codebase's existing item-create idiom; catches `InvalidPhoneNumber` and raises the customers-domain-owned `invalid_phone` mapping per T1), `update_customer`, `archive_customer` (sets `archived_at`; idempotent — Slice 2 extends this to cascade to vehicles), `get_customer`, `list_customers` (accent-insensitive search via `taller_unaccent_lower`, matching name OR phone fragment; the plate-fragment match is added in Slice 2 once vehicles exist).

- [x] **P1.S1.T12 (GREEN)** Create `api/src/taller/customers/adapters/repositories.py`: `SqlAlchemyCustomerRepository` implementing `CustomerRepository` against `CustomerModel`.

- [x] **P1.S1.T13 (GREEN)** Create `api/src/taller/customers/adapters/schemas.py`: `CustomerCreateRequest`, `CustomerUpdateRequest`, `CustomerOut` (`{id, full_name, phone, phone_is_mobile, notes, archived_at, created_at, updated_at}`), replay comparison on `{full_name, phone, notes}`.

- [x] **P1.S1.T14 (GREEN)** Create `api/src/taller/customers/adapters/router.py`: `customers_router` with `POST /customers`, `GET /customers?q=&include_archived=`, `GET /customers/{id}`, `PATCH /customers/{id}`, `POST /customers/{id}/archive`, each scoped by `get_current_workshop_id`, mapping `InvalidPhoneNumber` → 422 `invalid_phone`, `CustomerIdConflict` → 409, `CustomerNotFound` → 404. Run T10 and confirm it is green.

- [x] **P1.S1.T15 (GREEN)** Modify `api/src/taller/main.py`: mount `customers_router` under `/api`.

- [x] **P1.S1.T16** Run this slice's verification: `docker compose up -d db`; `cd api && uv run ruff check . && uv run ruff format --check . && uv run pytest`. Fix any failure before proceeding.

- [x] **P1.S1.T17** Work-unit commit on `feat/workshop-core-customers`: `:sparkles: feat(customers): add customer records with search and archive` (body: what/why, referencing `customers` capability spec).

### Slice P1.S2 — API: vehicles (plate normalization, uniqueness race, cascade archive) + tests

- [x] **P1.S2.T1** Create `api/src/taller/customers/domain/plate.py`: `normalize_plate(raw) -> str | None` — strip, uppercase, remove whitespace/`-`/`.`/`/`; empty result → `None`; result must match `^[A-Z0-9]{1,12}$` or raise `InvalidPlate` (AD-9).

- [x] **P1.S2.T2 (RED)** Write `api/tests/customers/test_customers_domain.py` additions (plate unit tests):
  - `normalize_plate("hab-1234") == "HAB1234"`. **Defect it catches:** a separator or lowercase variant bypasses the uniqueness index.
  - `normalize_plate("  ")` is `None`. **Defect it catches:** a whitespace-only plate is stored as `""`, which would collide with a second unplated vehicle against the partial index.
  - `normalize_plate("HAB#1")` raises `InvalidPlate`. **Defect it catches:** an invalid character is silently accepted and stored.

- [x] **P1.S2.T3 (GREEN)** Confirm T2 passes against T1's `normalize_plate`.

- [x] **P1.S2.T4 (RED)** Write `api/tests/customers/test_vehicles_api.py` covering, before vehicle use cases/router exist:
  - Create referencing an active customer of the workshop → saved with that owner. **Defect it catches:** the owner reference is dropped or unchecked.
  - Create referencing a nonexistent, foreign, or **archived** customer id → HTTP 404 `customer_not_found`, no vehicle created. **Defect it catches:** an archived customer's id is still accepted for new links (AD-14).
  - An edit payload including a different `customer_id` does not reassign the owner; the edit endpoint does not accept `customer_id`. **Defect it catches:** a vehicle can be reassigned to a different customer after creation.
  - Replaying an identical vehicle create → HTTP 200, one row; same id with a different plate → HTTP 409 `vehicle_id_conflict`. **Defect it catches:** a retry duplicates vehicles, or a conflicting replay overwrites data.
  - Plate `hab-1234` stored as `HAB1234`. **Defect it catches:** normalization is skipped at the API boundary.
  - A second active vehicle in the same workshop with plate `HAB 1234` against an existing `HAB1234` → HTTP 409 `plate_taken`; several unplated vehicles are always allowed; archiving a plated vehicle frees the plate for reuse; the same plate in a **different** workshop succeeds. **Defect it catches:** the index is not partial, not workshop-scoped, or compares unnormalized plates.
  - **Replaying a plated vehicle create → HTTP 200, not `plate_taken`.** **Defect it catches:** the uniqueness pre-check runs before replay detection (AD-14's ordering rule).
  - With the uniqueness pre-check monkeypatched away, a plate race → HTTP 409 `plate_taken` via the `IntegrityError` mapped by index name; an unrelated `IntegrityError` re-raises (not swallowed as `plate_taken`). **Defect it catches:** every integrity error gets mapped to `plate_taken`, hiding real bugs, or the race surfaces as an unhandled 500.
  - Archiving twice keeps the first `archived_at` (vehicle-only, no cascade). **Defect it catches:** `archived_at` is re-stamped on a repeat archive.
  - **Archiving a customer with two active vehicles archives both with the customer's own `archived_at` timestamp, and frees their plates; a vehicle already archived at an earlier `T0` keeps `T0`.** **Defect it catches:** orphaned plate reservations after a customer is archived, or the cascade overwrites an already-archived vehicle's timestamp.
  - **Customer search also matches a normalized plate** (`q=hab1234` and the partial `q=hab12` both find the owner of an active vehicle plated `HAB1234`; a plate on an **archived** vehicle is not matched). **Defect it catches:** the plate search ignores partial matches, or searches archived vehicles' plates.
  - Workshop B's GET/PATCH/archive of workshop A's vehicle id → HTTP 404 `vehicle_not_found`; workshop B creating a vehicle under workshop A's customer id → HTTP 404 `customer_not_found`. **Defect it catches:** a missing `workshop_id` filter leaks or mutates another tenant's data.
  - Listing a customer's vehicles without `include_archived` returns only active ones.

- [x] **P1.S2.T5 (GREEN)** Modify `api/src/taller/customers/application/use_cases.py`: `create_vehicle` (idempotent, rejects archived/foreign/nonexistent customer, replay-before-uniqueness-check per AD-14), `update_vehicle` (no `customer_id` in the editable payload), `archive_vehicle`, `get_vehicle`, `list_vehicles_for_customer`. Modify `archive_customer` to cascade: stamp `archived_at` on the customer and every one of its active vehicles in one transaction, same timestamp. Modify `list_customers`'s search to also match a normalized plate fragment of the customer's active vehicles.

- [x] **P1.S2.T6 (GREEN)** Modify `api/src/taller/customers/adapters/repositories.py`: `SqlAlchemyVehicleRepository` implementing `VehicleRepository` (including `get_many`), and extend the customer search query with the vehicle-plate join.

- [x] **P1.S2.T7 (GREEN)** Modify `api/src/taller/customers/adapters/schemas.py`: `VehicleCreateRequest`, `VehicleUpdateRequest`, `VehicleOut`, `VehicleDetailOut` (`VehicleOut` plus `owner: CustomerOut`); replay comparison on `{customer_id, vehicle_type, make, model, year, color, plate, notes}`.

- [x] **P1.S2.T8 (GREEN)** Modify `api/src/taller/customers/adapters/router.py`: add `vehicles_router` with `POST /vehicles`, `GET /customers/{id}/vehicles`, `GET /vehicles/{id}`, `PATCH /vehicles/{id}`, `POST /vehicles/{id}/archive`; map `PlateTaken` → 409, `InvalidPlate` → 422, `VehicleNotFound`/`CustomerNotFound` → 404, `VehicleIdConflict` → 409. Run T4 and confirm it is green.

- [x] **P1.S2.T9 (GREEN)** Modify `api/src/taller/main.py`: mount `vehicles_router`.

- [x] **P1.S2.T10** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest` (api).

- [x] **P1.S2.T11** Work-unit commit: `:sparkles: feat(customers): add vehicles with plate normalization and cascade archive`.

### Slice P1.S3 — Web: app shell, bottom nav, router restructure, Órdenes placeholder

- [x] **P1.S3.T1 (RED)** Write `web/src/app/AppShell.test.tsx`:
  - The nav renders on `/inventario/:id` and (once customer routes exist in S4) `/clientes/:id/vehiculos/:vid`, with the active tab following the first path segment (`aria-current="page"`). **Defect it catches:** the layout wraps only index routes, or the Clientes tab is not marked active on a nested vehicle screen.
  - Logout from the shell navigates to `/login` and clears the workshop cache; `InventoryPage` renders no logout control of its own. **Defect it catches:** logout is lost or duplicated during the move out of `InventoryPage`.
  - The Órdenes tab renders "Próximamente" and fires no request (MSW's `onUnhandledFrame: "error"` fails the test if it does). **Defect it catches:** the placeholder issues a work-orders request that would 404 before phase 2 ships.
  - Switching tabs while offline still renders the shell and each destination's own offline-read rules; switching makes no network request itself.

- [x] **P1.S3.T2 (GREEN)** Create `web/src/app/BottomNav.tsx` (presentational: three `NavLink`s, ≥48 px tall, `fixed` bottom with `env(safe-area-inset-bottom)`).

- [x] **P1.S3.T3 (GREEN)** Create `web/src/app/AppShell.tsx` (container: reads the session for the workshop name; owns the logout mutation moved out of `InventoryPage`; renders `<BottomNav/>` plus `<Outlet/>`, content padded so it is never hidden behind the nav).

- [x] **P1.S3.T4 (GREEN)** Create `web/src/app/copy.ts` for shell strings (Spanish).

- [x] **P1.S3.T5 (GREEN)** Create `web/src/features/workorders/WorkOrdersComingSoon.tsx` and `web/src/features/workorders/copy.ts`: renders "Próximamente", fetches nothing.

- [x] **P1.S3.T6 (GREEN)** Modify `web/src/app/router.tsx`: wrap `RequireSession`'s outlet in a pathless layout route; nest the `AppShell` layout route under it with the existing inventory routes, the phase-1 `Órdenes` placeholder route, and (left empty until S4/S5) the `/clientes` route slots.

- [x] **P1.S3.T7 (GREEN)** Modify `web/src/features/inventory/InventoryPage.tsx` (and its test): remove the page-level header and logout button (now in the shell). Re-run the **existing** inventory test suite and confirm it is still green (per spec: "Existing Inventory Flows Are Unaffected By The Shell").

- [x] **P1.S3.T8 (GREEN)** Modify `web/src/features/auth/hooks.ts`: export `useWorkshopId` (currently module-private). Modify `web/src/features/inventory/hooks.ts` to import it from `auth/hooks.ts` instead of its own copy.

- [x] **P1.S3.T9** Run T1 and confirm every scenario is green.

- [x] **P1.S3.T10** Run this slice's verification: `cd web && npm run lint && npm run typecheck && npm test -- --run`.

- [x] **P1.S3.T11** Work-unit commit: `:sparkles: feat(app): add a bottom-nav shell and move logout out of InventoryPage`.

### Slice P1.S4 — Web: customers list, search, create, edit, archive

- [x] **P1.S4.T1 (RED)** Write tests under `web/src/features/customers/` (one `*.test.tsx` per container, `server.use(...)` per test per the existing MSW pattern):
  - Submitting the new-customer form while offline is disabled with the Spanish message; the cached list still renders offline. **Defect it catches:** a write pauses offline and is silently lost, or offline reads break.
  - Double-clicking "Guardar" sends one client id, and a retry reuses the same id. **Defect it catches:** a new id generated per click/retry creates duplicate customers.
  - A 409 `plate_taken`-shaped and a 422 `invalid_phone` response each render their Spanish message from `copy.ts`, not a generic fallback. **Defect it catches:** a new error code falls through to the generic message.
  - A workshop switch (login as a different workshop) removes cached customer list/detail queries (extends the existing `workshopSwitch` test). **Defect it catches:** an unscoped query key serves workshop A's customers to workshop B.
  - Search `maria` renders `María` from the list.

- [x] **P1.S4.T2 (GREEN)** Create `web/src/features/customers/api.ts` (typed client for every phase-1 customer endpoint) and `copy.ts` (every Spanish string, including the offline-write message and the `invalid_phone`/`plate_taken` mappings).

- [x] **P1.S4.T3 (GREEN)** Create `web/src/features/customers/hooks.ts`: `useCustomers(params)`, `useCustomer(id)`, `useCreateCustomer`, `useUpdateCustomer`, `useArchiveCustomer`, every query key prefixed with `workshopQueryKey(w)` (per the "Query keys" table in `design.md`); no explicit `networkMode` on the mutations (per P1.S1.T1's confirmed convention).

- [x] **P1.S4.T4 (GREEN)** Create presentational `CustomerList.tsx`, `CustomerForm.tsx`.

- [x] **P1.S4.T5 (GREEN)** Create containers `CustomersPage.tsx` (search + list), `NewCustomerPage.tsx`, `EditCustomerPage.tsx`; each reads `useOnlineStatus()` to disable submit, and generates the client id once per form mount (`useState(() => crypto.randomUUID())`).

- [x] **P1.S4.T6 (GREEN)** Create `web/src/features/customers/routes.tsx` and wire it into `web/src/app/router.tsx`'s `/clientes` slot from S3.

- [x] **P1.S4.T7** Run T1 and confirm every scenario is green.

- [x] **P1.S4.T8** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.

- [x] **P1.S4.T9** Work-unit commit: `:sparkles: feat(customers): add the customers list, search, create, edit and archive screens`.

### Slice P1.S5 — Web: vehicle create, edit, archive and detail

- [x] **P1.S5.T1 (RED)** Write tests under `web/src/features/customers/` for the vehicle containers:
  - Submitting the new-vehicle form while offline is disabled with the Spanish message.
  - A previously visited vehicle detail renders offline from the persisted cache.
  - A duplicate-plate 409 and an invalid-plate 422 each render their Spanish message.
  - Double submit of a new vehicle reuses one client id.
  - `CustomerDetailPage` lists that customer's vehicles (not yet their orders — phase 2).

- [x] **P1.S5.T2 (GREEN)** Modify `web/src/features/customers/api.ts`/`copy.ts`/`hooks.ts`: vehicle endpoints and messages (`useVehiclesForCustomer`, `useVehicle`, `useCreateVehicle`, `useUpdateVehicle`, `useArchiveVehicle`), query keys per the "Query keys" table.

- [x] **P1.S5.T3 (GREEN)** Create presentational `VehicleList.tsx`, `VehicleForm.tsx`.

- [x] **P1.S5.T4 (GREEN)** Create containers `CustomerDetailPage.tsx` (lists vehicles), `NewVehiclePage.tsx`, `EditVehiclePage.tsx`, `VehicleDetailPage.tsx`.

- [x] **P1.S5.T5 (GREEN)** Modify `web/src/features/customers/routes.tsx`/`router.tsx`: nest vehicle routes under `/clientes/:customerId/vehiculos/...` per AD-16.

- [x] **P1.S5.T6** Run T1 and confirm every scenario is green.

- [x] **P1.S5.T7** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run && npm run build` (record the chunk sizes per `design.md`'s "Lazy boundaries" note, even though phase 1 adds no lazy route yet).

- [x] **P1.S5.T8** Work-unit commit: `:sparkles: feat(customers): add vehicle create, edit, archive and detail screens`.

### Slice P1.S6 — Phase 1 closing: seed, docs, migration round-trip, real-browser check

- [x] **P1.S6.T1** Extend `deploy/demo/seed-demo-account.sh`: add the five seeded customers and their vehicles from `design.md`'s "Demo seed growth" table (`maria-hernandez`, `jose-nunez`, `carlos-mejia`, `ana-castillo`, `luis-zelaya`, each with the vehicles listed, exercising raw/lowercase/spaced plate normalization and at least two unplated vehicles). Use the existing idiom: `uuidgen --sha1 --namespace @url --name "$id_namespace/customer/<key>"` (and `/vehicle/<key>`); treat 201/200/409 as normal outcomes; print a one-line summary per entity. **Idempotency/rerun check:** add an explicit step that runs the seed script twice in a row against the same database and asserts the second run creates zero new rows (count customers/vehicles before and after, or rely on the script's own 200/409 accounting) before this task is checked off. **Verification note:** the orchestrator deferred a live rerun of this script to the deployment step (T6, not run in this apply pass — no demo deployment yet); verified here with `bash -n` plus a manual read-through, which caught and fixed a variable-shadowing bug (the customer loop's `phone` was clobbering the demo account's own `phone` used in the final summary line).

- [x] **P1.S6.T2** Update `deploy/demo/README.md`: document the seeded customers/vehicles, and that seeded mobile numbers are fictional and must not be messaged (this phase adds no WhatsApp action yet, but the data is already in place for phase 2).

- [x] **P1.S6.T3** Update `CLAUDE.md`:
  - **Architecture** section: add a subsection for the new `customers` feature (mirroring the existing "API: hexagonal per feature" and "Web: container/presentational" descriptions) and the new app shell (`AppShell`/`BottomNav`, logout relocated from `InventoryPage`).
  - **Planning and history** section: add a bullet for `openspec/changes/` (active SDD changes: proposal/specs/design/tasks per change) and `openspec/specs/` (archived baseline specs), alongside the existing `odd/tasks/` and `docs/research/` bullets.

- [x] **P1.S6.T4** Exercise the phase-1 migration round-trip locally: `uv run alembic upgrade head`, `uv run alembic downgrade -1`, `uv run alembic upgrade head` against the dev database; confirm no error and that `uv run pytest tests/test_migrations.py` (`alembic check`) is green. **Result:** upgrade → downgrade -1 (1b224b5a2186 → 1e94ffe69058) → upgrade head, no errors; `test_migrations.py` passed.

- [x] **P1.S6.T5** Run the full phase-1 verification suite and record each result:
  - API: `docker compose up -d db`; `cd api && uv run ruff check . && uv run ruff format --check . && uv run pytest`. **Result:** ruff check clean; ruff format clean (72 files); pytest 136 passed.
  - Web: `cd web && npm run lint && npm run typecheck && npm test -- --run && npm run build`. **Result:** eslint clean; tsc clean; vitest 117 passed (25 files); build succeeded (main chunk 416.00 kB / gzip 125.16 kB).
  - Migrations: upgrade → downgrade → upgrade (T4). **Result:** see T4.

- [x] **P1.S6.T6** Deploy phase 1 to the demo (`deploy/demo/README.md` procedure) and re-run the seed script against it. **Evidence:** the demo worktree runs the branch head; `alembic upgrade` applied `1b224b5a2186` cleanly; `/api/health` answered ok. The first seed run created 5 customers and 6 vehicles; the second run created 0 of each.

- [x] **P1.S6.T7** Real-browser check at **390×844** against the deployed demo, covering phase 1's success criteria from `proposal.md`:
  - Every protected screen shows `Inventario · Clientes · Órdenes`; logout works from the shell; existing inventory flows (list, detail, movement, count, offline tap) still work.
  - Clientes lists the seeded customers; `maria` finds `María`.
  - A customer saved with `+504 2234-5678` is stored as `22345678` and recognized as a landline; `9876-5432` is a mobile; an empty phone is accepted; a 7-digit number or one starting with `1` is rejected with a Spanish message.
  - A vehicle saved with plate `hab-1234` shows `HAB1234`; a second active vehicle with `HAB 1234` in the same workshop is rejected with a Spanish duplicate message; several unplated vehicles are allowed.
  - With the device offline, a previously visited customer list/detail still renders; create/edit is disabled with a message.
  - Rerunning the seed script creates no duplicates (confirmed via T1, re-verified against the demo database).
  **Evidence:** checked in a real browser at 390×844 on the public demo. Bottom nav with `aria-current` and logout from the shell work. Accent, plate and phone-fragment searches work. A customer was created with a landline. `prb-123` showed as `PRB123`, and `DEM 0001` was rejected with the Spanish duplicate message. Offline, the cached list still rendered and create was disabled with its message. The Órdenes placeholder shows. Console was clean apart from the expected 401/409. The check exposed one layout defect: detail and form screens rendered as a narrow centered strip inside the shell. It was fixed in `1232af0` and re-checked on the demo. The 7-digit phone rejection, several unplated vehicles, and inventory movement/count/offline-tap flows were not repeated in the browser; the API and web suites cover them.

- [x] **P1.S6.T8** Work-unit commit: `:hammer: chore(deploy): seed phase 1 customers and vehicles, document the shell` (covers T1–T3; T4–T7 are verification evidence, not code changes, recorded in this change's history/PR description).

---

## Phase 2: Work orders, quote lines and WhatsApp sharing

### Slice P2.S1 — API: ledger changes (migration, work-order ORM models, `record_movement` link params/replay, history projection)

- [x] **P2.S1.T1** Re-confirm (one bounded `Read` of `api/src/taller/inventory/adapters/router.py`'s exception handling in `record_movement_route`) the exact HTTP status codes for `MovementIdConflict` and `StockOutOfRange` flagged as still-open in P1.S1.T1. Adjust T6/T8 below if they differ from the expected 409/422. **Result:** confirmed unchanged — `MovementIdConflict` → 409 `movement_id_conflict`, `StockOutOfRange` → 422 `stock_out_of_range` (`record_movement_route`, `router.py:269-276`). No adjustment needed.

- [x] **P2.S1.T2** Create the package skeleton: `api/src/taller/workorders/__init__.py`, `domain/__init__.py`, `application/__init__.py`, `adapters/__init__.py`.

- [x] **P2.S1.T3** Create `api/src/taller/workorders/adapters/models.py` with **only** the ORM models the migration and the FK-by-table-name trick need at this point: `WorkshopCounterModel` (`workshop_counters`, composite PK `(workshop_id, name)`), `WorkOrderModel` (`work_orders`), `WorkOrderLineModel` (`work_order_lines`) — columns, checks and indexes exactly per `design.md`'s "Data model per phase → Phase 2" table. Work-order domain/application code (which needs these mapped to domain entities) is not written until Slice 2.

- [x] **P2.S1.T4** Create the phase-2 migration `api/migrations/versions/<rev>_work_orders.py`: `workshop_counters`, `work_orders`, `work_order_lines` (upgrade order: counters, orders, lines), then on `inventory_movements`: nullable `order_id`/`order_line_id` columns, their FKs (by table-name string, `work_orders.id`/`work_order_lines.id`), `ck_inventory_movements_order_link_pair`, and the two indexes. Working `downgrade()` in the reverse order from `design.md` (drop the two movement indexes; drop the check and both FKs on movements; drop the two columns — linked movement rows remain; then drop `work_order_lines`, `work_orders`, `workshop_counters`). Add `import taller.workorders.adapters.models` to `api/migrations/env.py`. **Result:** generated via `alembic revision --autogenerate`, then hand-fixed: autogenerate omits `CheckConstraint`s on `ALTER`-added columns and leaves ALTER-added FKs unnamed, so `ck_inventory_movements_order_link_pair` and both FK names (`inventory_movements_order_id_fkey`/`..._order_line_id_fkey`, Postgres' own default naming) were added explicitly, and upgrade/downgrade reordered to match `design.md` exactly (revision `8db9fb7d17ef`).

- [x] **P2.S1.T5 (RED)** Write `api/tests/inventory/test_movement_order_link.py`, before `record_movement` accepts link parameters:
  - `record_movement` called twice with identical `{item_id, kind, quantity, note, order_id, order_line_id}` and the same movement id → the second call's `is_new` is `False` and no second row exists. **Defect it catches:** the link fields are excluded from replay matching, so a legitimately-replayed order-caused movement double-applies.
  - The same movement id with the same `{item_id, kind, quantity, note}` but a **different** `order_line_id` → raises `MovementIdConflict`. **Defect it catches:** AD-3's planted-id attack — a client pre-records an unlinked movement at a derived `uuid5` id, then an order's real consumption at that same id is silently taken as a harmless replay instead of a conflict.
  - A movement recorded with no order link, replayed with the same `{item_id, kind, quantity, note}` and still no link → unaffected, no false conflict (existing outbox behavior). **Defect it catches:** adding the nullable link fields changes replay matching for movements that never carried one, breaking offline-outbox replay.
  - An item's movement history exposes `order_id`/`order_line_id`/`order_number` for an order-linked movement, and `null`/`null`/`null` for a manual/offline movement. **Defect it catches:** `inventory_movements` carries the link but the history read path never surfaces it, so a mechanic can't see which order consumed a part.
  **Result (RED):** confirmed by stashing T6-T11's application/adapter changes (keeping T3/T4's models/migration) and running this file: `test_replaying_an_order_linked_movement_is_a_no_op`, `test_same_movement_id_with_a_different_order_line_is_a_conflict`, and `test_item_history_exposes_the_order_that_caused_a_movement` failed with `TypeError: record_movement() got an unexpected keyword argument 'order_id'`; `test_unlinked_movement_replay_is_unaffected_by_the_link_fields` passed immediately (existing behavior, unaffected by the stash) — 3 failed, 1 passed, exactly as expected before GREEN.

- [x] **P2.S1.T6 (GREEN)** Modify `api/src/taller/inventory/domain/entities.py`: add `order_id: uuid.UUID | None = None` and `order_line_id: uuid.UUID | None = None` to `StockMovement`; add `MovementHistoryEntry` (`movement: StockMovement`, `order_number: int | None`).

- [x] **P2.S1.T7 (GREEN)** Modify `api/src/taller/inventory/application/ports.py`: `MovementRepository.list_for_item` returns `list[MovementHistoryEntry]`.

- [x] **P2.S1.T8 (GREEN)** Modify `api/src/taller/inventory/application/use_cases.py`: `record_movement` gains trailing keyword-only `order_id`/`order_line_id` (default `None`); `_movement_matches` compares `{item_id, kind, quantity, note, order_id, order_line_id}`; `list_item_movements` returns `MovementHistoryEntry` items.

- [x] **P2.S1.T9 (GREEN)** Modify `api/src/taller/inventory/adapters/models.py`: add the two nullable columns, their FKs (string references to `work_orders.id`/`work_order_lines.id`), the check constraint, and the two indexes, matching T4 exactly.

- [x] **P2.S1.T10 (GREEN)** Modify `api/src/taller/inventory/adapters/repositories.py`: persist/map the link fields on `StockMovementModel`↔`StockMovement`; `list_for_item` issues a `LEFT JOIN` to a lightweight `sqlalchemy.table("work_orders", column("id"), column("number"))` construct (no ORM import of `WorkOrderModel`) and returns `MovementHistoryEntry` objects.

- [x] **P2.S1.T11 (GREEN)** Modify `api/src/taller/inventory/adapters/schemas.py`: `MovementOut` gains `order_id`, `order_line_id`, `order_number` fields, mapped from `MovementHistoryEntry`. Run T5 and confirm it is green. **Result (GREEN):** `MovementOut.from_domain` takes a plain `StockMovement` plus an explicit `order_number: int | None = None` keyword (not a `MovementHistoryEntry` directly) — `record_movement_route`'s response reuses the same classmethod for the just-written/replayed movement, which never has a resolvable `order_number` to join against, so the list route passes `entry.order_number` explicitly while the record route leaves it at its default. All 4 new tests passed; full `api/tests/inventory/` suite (60 tests) green, including the existing movement/outbox/tenant-isolation tests.

- [x] **P2.S1.T12** Exercise the migration round-trip locally (`alembic upgrade head` → `downgrade -1` → `upgrade head`) and confirm `uv run pytest tests/test_migrations.py` is green. **Result:** upgrade `1b224b5a2186` → `8db9fb7d17ef`, downgrade back to `1b224b5a2186`, upgrade to `8db9fb7d17ef` again — no errors; `test_migrations.py` (`alembic check`) passed, no `MIGRATION_ONLY_INDEXES` fallback needed (every index/check is expressible on the models).

- [x] **P2.S1.T13** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest` (api). This must also re-run every **existing** inventory test (movement replay, outbox) and confirm it is still green, per the "Existing Movement Idempotency Behavior Is Preserved" requirement. **Result:** ruff check clean; ruff format clean (79 files); pytest 145 passed (141 existing + 4 new in `test_movement_order_link.py`), including every pre-existing inventory/outbox/tenant-isolation test.

- [x] **P2.S1.T14** Work-unit commit: `:sparkles: feat(inventory): link stock movements to the work order that caused them`.

### Slice P2.S2 — API: work-order domain, numbering, non-consuming lines, list

- [x] **P2.S2.T1 (RED)** Write `api/tests/workorders/test_reconciliation_plan.py` (pure, no DB) against `plan_reconciliation`, before it exists:
  - In `in_progress`, an inventory-part line not yet posted plans `out qty` at revision 1. **Defect it catches:** the initial consumption is skipped or posts the wrong quantity.
  - Posted 2 → target 5 plans `out 3`; posted 5 → target 2 plans `in 3`. **Defect it catches:** an edit re-posts the full new quantity instead of only the delta, double-counting consumption.
  - A removed line (posted `qty`, target `0`) plans `in qty`. **Defect it catches:** removing a consuming line leaves its stock taken.
  - In `cancelled`, every previously-posted line plans `in posted`. **Defect it catches:** cancellation reverses only some lines, or reverses a line that never consumed.
  - Labor and external-part lines never appear in the plan, in any status. **Defect it catches:** a non-part line accidentally touches stock.
  - The plan is sorted by `(item_id, line_id)`. **Defect it catches:** an unsorted plan, which is the deadlock AD-5 exists to prevent.
  **Result (RED):** stashed `status.py`/`stock.py`/`money.py`/`entities.py`/`errors.py` (keeping the test file), ran the suite: `ModuleNotFoundError: No module named 'taller.workorders.domain.entities'` on collection. Restored the stash (GREEN): 7 passed.

- [x] **P2.S2.T2 (GREEN)** Create `api/src/taller/workorders/domain/status.py`: `WorkOrderStatus` (`StrEnum`), `TRANSITIONS`, `CONSUMING`, `EDITABLE`, exactly as in `design.md`'s "Interfaces / Contracts" snippet (`PAYABLE` is added in phase 3).

- [x] **P2.S2.T3 (GREEN)** Create `api/src/taller/workorders/domain/stock.py`: `WORK_ORDER_STOCK_NAMESPACE` (a fixed literal `uuid.UUID`, generated once and never changed), `movement_id_for(order_id, line_id, revision)`, `PlannedMovement`, `plan_reconciliation(order_id, status, lines)` (pure). Run T1 and confirm it is green. **Deviation:** `WORK_ORDER_STOCK_NAMESPACE` is `uuid.uuid5(uuid.NAMESPACE_URL, "https://taller-mecanico.invalid/workorders/stock-consumption")` rather than a hand-picked random literal — a pure function of a constant input is exactly as fixed/never-changing as a literal, and it mirrors the codebase's own existing idiom (`_INITIAL_STOCK_NAMESPACE` in `inventory/application/use_cases.py`) instead of introducing a second, unexplained convention.

- [x] **P2.S2.T4 (GREEN)** Create `api/src/taller/workorders/domain/money.py`: line subtotal (`quantity * unit_price_cents`) and order total (sum over non-removed lines) helpers, cents-only, no floats.

- [x] **P2.S2.T5 (GREEN)** Create `api/src/taller/workorders/domain/entities.py`: `WorkOrder`, `WorkOrderLine` aggregates (fields per the "Data model per phase → Phase 2" tables, including `stock_posted_quantity`/`stock_revision` on the line). Also adds `LineKind` (`StrEnum`), mirroring `VehicleType`'s existing convention for a line's `kind`.

- [x] **P2.S2.T6 (GREEN)** Create `api/src/taller/workorders/domain/errors.py`: `WorkOrderNotFound`, `WorkOrderIdConflict`, `InvalidStatusTransition`, `WorkOrderLocked`, `WorkOrderLineNotFound`, `WorkOrderLineIdConflict`, `ItemNotFoundForLine`. `InvalidStatusTransition` is declared now and used starting Slice 3.

- [x] **P2.S2.T7 (GREEN)** Modify `api/src/taller/customers/application/use_cases.py`: add `get_active_vehicle(workshop_id, vehicle_id)` (404-equivalent domain error for a missing/foreign/archived vehicle) and `describe_vehicles(workshop_id, vehicle_ids)` (batched, one query per table) per AD-12. **Deviation (minimal, necessary):** AD-12 says "batches one query per table" (plural) — resolving owners too needs a second batched lookup beyond the already-declared `VehicleRepository.get_many`, so `CustomerRepository` gained the same `get_many(workshop_id, customer_ids)` method (ports.py + `SqlAlchemyCustomerRepository`), mirroring `VehicleRepository.get_many`'s existing shape exactly. **Gotcha:** `get_many` had to be placed *before* `CustomerRepository.list(...)` in both the Protocol and its SQLAlchemy implementation — a method named `list` inside a class body shadows the builtin `list` for every annotation evaluated afterward in that same class, breaking `customer_ids: list[uuid.UUID]` on any method defined below it (`TypeError: 'function' object is not subscriptable`); caught immediately via `import taller.main`.

- [x] **P2.S2.T8 (RED)** Write `api/tests/workorders/test_work_orders_api.py` and `api/tests/workorders/test_work_order_lines_api.py`, before the use cases/router exist:
  - Create referencing an existing active vehicle → saved with that vehicle; a nonexistent/foreign vehicle id → HTTP 404 `vehicle_not_found`, no order created. **Defect it catches:** the vehicle reference is dropped, or tenancy on the referenced vehicle is unchecked.
  - A workshop's last number `42` → the next create gets `43`. **Defect it catches:** numbering starts over or reads a stale counter.
  - Replaying an identical create (same id, same payload) → HTTP 200, still numbered `43`, counter not incremented again; the same id with a different `vehicle_id` → HTTP 409 `work_order_id_conflict`. **Defect it catches:** a retry burns a number, or a conflicting replay overwrites the order.
  - A labor line, an inventory-part line (referencing an active item), and an external-part line can all be added in a non-consuming status; the order's total is the sum of their quantity×price subtotals; no inventory movement is posted by adding any of them. **Defect it catches:** a line add posts stock prematurely, or the total omits a line kind.
  - An inventory-part line referencing a nonexistent/foreign item id → HTTP 404 `item_not_found`, no line added. **Defect it catches:** a part line accepts a cross-tenant or made-up item id.
  - Replaying an identical line add → HTTP 200, one line; the same line id with a different payload → HTTP 409 `work_order_line_id_conflict`; editing/removing a line id that doesn't exist on the order (or belongs to another order) → HTTP 404 `work_order_line_not_found`. **Defect it catches:** line replay/conflict/not-found semantics are missing.
  - `GET /work-orders?status_group=open|closed|all` filters correctly; `limit` is capped at 100.
  **Also added (same Test Value Gate):** archived-vehicle/archived-item rejection, a second workshop numbering independently from 1, idempotent double-removal of a line, and tenant isolation on `GET`/`PATCH /work-orders/{id}` (the `work-orders` spec's own "Work Order Data Is Isolated Per Workshop" requirement, exercised in the same slice that introduces the resource, matching how customers/vehicles tenant isolation landed in their own introducing slice in Phase 1). **Result (GREEN against T11–T14):** 26 passed.

- [x] **P2.S2.T9 (RED)** Write `api/tests/workorders/test_work_order_concurrency.py`:
  - Two threads creating orders for one workshop concurrently → two distinct, sequential numbers, no gap. **Defect it catches:** a read-then-write numbering scheme races under concurrent creates.
  - Two threads submitting the **same** client id concurrently → exactly one order persists, one request sees 201 and the other 200, and the counter is not bumped twice. **Defect it catches:** a rolled-back duplicate insert leaves a gap in the sequence (AD-6's retry-on-`IntegrityError` path).
  **Implementation note:** calls `create_work_order` directly against two real `Session(test_engine)` connections (not through HTTP/`TestClient`), the same way `test_login_throttle_repository.py`'s two-session pattern works below the router — the per-test SAVEPOINT fixture (`db_session`/`client`) is invisible across connections, so a genuine row-lock race needs data committed outside it. A `committed_workshop` fixture commits a workshop/user/customer/vehicle on a separate connection (flushed one dependency level at a time — the same cross-model flush-ordering gotcha from P2.S1) and deletes them afterward. **Result:** 2 passed, re-run 5× with no flake.

- [x] **P2.S2.T10 (GREEN)** Create `api/src/taller/workorders/application/ports.py`: `WorkshopCounterRepository.next_value`, `WorkOrderRepository` (`get_by_id`, `get_for_update`, `add`, `save`, `list`, `totals`), per `design.md`'s "Interfaces / Contracts" snippet.

- [x] **P2.S2.T11 (GREEN)** Create `api/src/taller/workorders/application/use_cases.py`: `create_work_order` (AD-6's exact sequencing — replay check first, resolve the vehicle, bump the counter via the upsert, insert, retry once on a `work_orders_pkey` `IntegrityError`), `add_line`, `update_line`, `remove_line` (all idempotent by client id, and in this slice only handling non-consuming statuses — consuming-state reconciliation is Slice 3), `update_work_order` (PATCH), `get_work_order`, `list_work_orders`.

- [x] **P2.S2.T12 (GREEN)** Create `api/src/taller/workorders/adapters/repositories.py`: `SqlAlchemyWorkshopCounterRepository.next_value` (the `INSERT … ON CONFLICT DO UPDATE … RETURNING value` upsert from AD-6), `SqlAlchemyWorkOrderRepository`. `WorkOrderRepository.save`/`add`/`get_by_id`/`get_for_update` load and reconcile the `work_order_lines` collection through explicit queries (no ORM `relationship()`, matching every other model in this codebase).

- [x] **P2.S2.T13 (GREEN)** Create `api/src/taller/workorders/adapters/schemas.py`: `WorkOrderCreateRequest`, `WorkOrderOut`, `WorkOrderSummaryOut`, `WorkOrderLineOut`, line create/update requests, per `design.md`'s "API surface per phase → Phase 2" shapes (payment fields added phase 3). Line/order update requests reject an explicit `null` on their non-nullable fields (`description`/`quantity`/`unit_price_cents`), mirroring `CustomerUpdateRequest`'s guard from Phase 1.

- [x] **P2.S2.T14 (GREEN)** Create `api/src/taller/workorders/adapters/router.py`: `work_orders_router` with `POST /work-orders`, `GET /work-orders`, `GET /work-orders/{id}`, `PATCH /work-orders/{id}`, `POST /work-orders/{id}/lines`, `PATCH /work-orders/{id}/lines/{line_id}`, `DELETE /work-orders/{id}/lines/{line_id}` (the `PUT .../status` endpoint is added in Slice 3). Run T8 and T9, confirm both are green. As composition root, it calls `describe_vehicles` (customers' application layer) to embed `vehicle`/`customer` on every single-order and list response.

- [x] **P2.S2.T15 (GREEN)** Modify `api/src/taller/main.py`: mount `work_orders_router`.

- [x] **P2.S2.T16** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest`. **Result:** ruff check clean; ruff format clean (93 files); pytest 180 passed (152 existing + 28 new: 7 reconciliation-plan + 14 order-level + 12 line-level + 2 concurrency, minus overlap already counted — see commit for the exact new-file list).

- [x] **P2.S2.T17** Work-unit commit: `:sparkles: feat(workorders): add work orders with atomic numbering and quote lines`.

### Slice P2.S3 — API: `change_status` and consuming-state reconciliation

- [x] **P2.S3.T1 (RED)** Write `api/tests/workorders/test_stock_consumption.py`, before `change_status` exists:
  - `approved → in_progress` posts an `out` movement per inventory-part line only (no movement for labor/external lines); negative stock is allowed and the item is flagged, the transition is never blocked by it. **Defect it catches:** a non-part line touches stock, or the transition is incorrectly rejected on negative stock.
  - Forbidden transitions (`quote → in_progress`, `delivered → cancelled`, `completed → cancelled`) → HTTP 409 `invalid_status_transition`, stock unchanged. **Defect it catches:** approval is bypassed, or stock already installed in a delivered/completed order is reversed.
  - A repeated `PUT in_progress`, repeated `PATCH` quantity, and repeated `DELETE` line each post nothing the second time. **Defect it catches:** a retry double-consumes stock.
  - Editing quantity 2→5 while consuming posts `out 3`; 5→2 posts `in 3`; adding a part line while already consuming posts at once; removing a consuming line returns its stock. **Defect it catches:** a full re-post on edit, or a line added mid-job never consumes.
  - Cancelling after consumption restores stock exactly to its pre-consumption value; cancelling from `quote` posts nothing. **Defect it catches:** a missing or doubled reversal.
  - After a mixed scenario (consume, edit, partial cancel-equivalent), each line's `stock_posted_quantity == -SUM(delta)` of its linked movements, and `item.stock` equals the ledger sum. **Defect it catches:** the persisted posting state drifts from the ledger (AD-4's invariant).
  - `record_movement` monkeypatched to fail on the second of several lines → the order's status is unchanged and no movement from the first line is left committed. **Defect it catches:** a partial commit, violating the one-transaction requirement.
  - Line edits in `delivered` or `cancelled` → HTTP 409 `work_order_locked`; editing lines in `completed` is allowed. **Defect it catches:** a locked order stays mutable, or `completed` is wrongly locked.
  - Workshop B on workshop A's order (status PUT, line add/edit/remove) → HTTP 404 everywhere. **Defect it catches:** a missing tenancy check on the status/line endpoints.
  **Result (RED):** confirmed by running the file before `change_status` and the reconciliation wiring existed — collection/call failures (`ImportError`/`TypeError`) on every scenario above, since `change_status` and the extended `add_line`/`update_line`/`remove_line` signatures did not exist yet.

- [x] **P2.S3.T2 (RED)** Extend `api/tests/workorders/test_work_order_concurrency.py`:
  - Order X with items `[A, B]` and order Y with `[B, A]`, both transitioned into `in_progress` concurrently → both succeed, final stocks reflect both. **Defect it catches:** locking items in line order (instead of the deterministic `(item_id, line_id)` order from AD-5) deadlocks.
  **Result (RED):** same import-time failure as T1, before `change_status` existed.

- [x] **P2.S3.T3 (GREEN)** Modify `api/src/taller/workorders/application/use_cases.py`: add `change_status(...)` — lock the order row `FOR UPDATE` first (serializing against line edits per AD-5); no-op if `current == target`; 409 if `target` is not in `TRANSITIONS[current]`; otherwise run `plan_reconciliation` and, for each planned movement in `(item_id, line_id)` order, call `taller.inventory.application.use_cases.record_movement` (imported directly per AD-2, sharing the caller's session/transaction) with `order_id`/`order_line_id` set, update the line's `stock_posted_quantity`/`stock_revision`, then update the order's status and the matching timestamp (`approved_at`/`started_at`/`completed_at`/`delivered_at`/`cancelled_at`). Extend `add_line`/`update_line`/`remove_line` from Slice 2 to also run reconciliation when the order's current status is in `CONSUMING`. **Deviation:** no `clock` parameter — `change_status` computes one `now = datetime.now(UTC)` internally and shares it across every posted movement's `occurred_at` and the order's own status timestamp, mirroring the convention every other use case in this file already uses (`create_work_order`/`add_line`/`update_line`/`remove_line` all call `datetime.now(UTC)` inline; nothing in this feature injects a clock). No scenario above needs time manipulation, so an unused injectable parameter would be an untested, inconsistent indirection. **Gotcha found and fixed:** `add_line`'s brand-new line must be persisted (`order_repo.save(order)`) *before* reconciliation runs when the order is already consuming — `inventory_movements.order_line_id`'s FK requires the line's row to exist first, and posting against the still-unflushed in-memory line hit a `ForeignKeyViolation` in T1's "adding a part line while already consuming" scenario. Fixed with an extra `save` right after appending the line, before reconciling; the existing final `save` still persists the posted-quantity/revision update afterward.

- [x] **P2.S3.T4 (GREEN)** Modify `api/src/taller/workorders/adapters/router.py`: add `PUT /work-orders/{id}/status`, building `SqlAlchemyItemRepository`/`SqlAlchemyMovementRepository` on the same request session and passing them into `change_status`; map `InvalidStatusTransition` → 409, and re-raise inventory's `MovementIdConflict`/`StockOutOfRange` unchanged (confirmed status codes from P2.S1.T1). Also wired `current_user`/`item_repo`/`movement_repo` into `add_line_route`/`update_line_route`/`remove_line_route` (Slice 2 did not need them) and mapped `MovementIdConflict`/`StockOutOfRange` there too, since Slice 3 extended those same use cases to call `record_movement` while consuming. Ran T1 and T2, confirmed both green.

- [x] **P2.S3.T5** Ran this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest` (api). **Result:** ruff check clean; ruff format clean (94 files); pytest 190 passed (180 existing + 10 new: 9 in `test_stock_consumption.py` + 1 deadlock test in `test_work_order_concurrency.py`), including every pre-existing workorders/inventory/customers test. The deadlock test was re-run 5× with no flake.

- [x] **P2.S3.T6** Work-unit commit: `:sparkles: feat(workorders): consume and reverse stock through the status lifecycle`.

### Slice P2.S4 — Web: inventory history order link, work-orders list, read-only detail

- [x] **P2.S4.T1 (RED)** Write/extend inventory web tests: item history renders "Orden #N" linking to `/ordenes/:id` when `order_number` is present, and nothing extra when it is `null`. **Defect it catches:** the order link from the API is fetched but never rendered. **Result (RED):** added `"links a movement to the order that caused it, and renders no such link for a manual one"` to `ItemDetailPage.test.tsx`; ran it before touching `MovementHistory.tsx` — failed on `findAllByRole("link", ...)` finding zero elements, confirming no link was rendered yet.

- [x] **P2.S4.T2 (GREEN)** Modify `web/src/features/inventory/hooks.ts`: export `inventoryQueryKey` (currently module-private). Modify `web/src/features/inventory/api.ts`: `MovementOut` gains `order_id`, `order_line_id`, `order_number`. Modify `web/src/features/inventory/MovementHistory.tsx` (or the item-detail component rendering it) to link to `/ordenes/:id` when `order_number` is present. Run T1 and confirm it is green. **Result (GREEN):** T1 passed. **Deviation (minimal, necessary):** adding the three required fields to `MovementOut` also required updating the one other literal `MovementOut` object in the web test suite (`hooks.test.ts`'s queued-outbox-flush mock) with the same three `null` fields, or `npm run typecheck` would fail on a missing-properties error; every other `recorded_at`-shaped test literal found by a repo-wide search is passed through `HttpResponse.json(...)` (not type-checked against `MovementOut`), so none of them needed a change.

- [x] **P2.S4.T3 (GREEN)** Create `web/src/features/workorders/api.ts` (types and client functions per `design.md`'s TS interface snippet: `WorkOrderStatus`, `LineKind`, `WorkOrderOut`, `WorkOrderSummaryOut`, `WorkOrderLineOut`) and `copy.ts` (Spanish labels for every status and line kind). `api.ts` ships only `listWorkOrders`/`getWorkOrder` in this read-only slice; create/line/status client functions arrive with the mutations that need them (S5/S6). **Deviation (minimal, necessary, applying the phase-1 lesson on this change):** also promoted `formatCents`/`centsToPlainAmount`/`parseLempirasToCents` from `web/src/features/inventory/format.ts` to new `web/src/shared/format/money.ts`, since this slice's `WorkOrderList`/`WorkOrderLines`/`WorkOrderDetailPage` are the second consumer of the lempira formatter (`design.md`'s "Web architecture per phase" note, and this change's own phase-1 lesson: "do that instead of duplicating them"). `inventory/format.ts` re-exports all three, so its existing imports (and `format.test.ts`) are unchanged.

- [x] **P2.S4.T4 (GREEN)** Create `web/src/features/workorders/hooks.ts`: `useWorkOrders(params)` (`useInfiniteQuery` for Historial per the "Query keys" table), `useWorkOrder(id)`, query keys prefixed by `workshopQueryKey(w)`. Implemented as `useWorkOrders(statusGroup, limit?)` (both tabs share the one hook/key shape; only Historial realistically pages via `fetchNextPage`).

- [x] **P2.S4.T5 (RED)** Write tests for the list and read-only detail: Abiertas/Historial tabs render the right status groups; a previously visited order detail renders offline from the persisted cache; status actions are not yet interactive in this slice (deferred to S6) so no test asserts them here. **Result (RED):** confirmed by running `WorkOrdersPage.test.tsx`/`WorkOrderDetailPage.test.tsx` before `hooks.ts`/the containers existed — import/collection failures on both files.

- [x] **P2.S4.T6 (GREEN)** Create `WorkOrderList.tsx` (presentational), `WorkOrdersPage.tsx` (container: Abiertas | Historial), `WorkOrderLines.tsx` (presentational, read-only in this slice), `WorkOrderDetailPage.tsx` (container: lines, totals; status/share/payments wired in later slices).

- [x] **P2.S4.T7 (GREEN)** Modify `web/src/app/router.tsx`: replace the phase-1 `Órdenes` placeholder route with the real `WorkOrdersPage`/`WorkOrderDetailPage` routes. Delete `web/src/features/workorders/WorkOrdersComingSoon.tsx` and its now-unused copy entries. Also updated `web/src/app/AppShell.test.tsx`: its two tests that stood in a `<WorkOrdersComingSoon/>`/"Próximamente" stub for the Órdenes route now use a plain stub `<div>` (the same stand-in style it already uses for the not-yet-tested inventory/vehicle nested routes), since the real screen is no longer a no-fetch placeholder.

- [x] **P2.S4.T8** Run T1 and T5, confirm both are green. **Result:** both green (see T1/T5 notes).

- [x] **P2.S4.T9** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`. **Result:** eslint clean; `tsc -b --noEmit` clean; vitest 123 passed (28 files), including every pre-existing inventory/customers/app test. `api/` was untouched by this slice; re-ran its suite anyway as a baseline check: `ruff check`/`ruff format --check` clean (94 files), `pytest` 190 passed, unaffected.

- [x] **P2.S4.T10** Work-unit commit: `:sparkles: feat(workorders): add the orders list, read-only detail, and the item-history order link`.

### Slice P2.S5 — Web: new order flow, line editor, item picker

- [x] **P2.S5.T1 (RED)** Write tests:
  - A double submit of the new-order form reuses one client id. **Defect it catches:** duplicate orders and a skipped number.
  - The line editor rejects a part line with no item selected, and an inventory-part line correctly excludes stock effects from its own preview (no optimistic stock mutation before the server responds).
  - Creating an order while offline is disabled with the Spanish message.
  **Result (RED):** `NewWorkOrderPage.test.tsx`'s "reuses the same client-generated id" test confirmed RED against a one-line regression (generating the create payload's `id` with a fresh `crypto.randomUUID()` per submit instead of the one generated at mount) — the test failed on the two captured ids differing, then passed again once reverted. `LineEditorDialog.test.tsx`'s "rejects a part line with no item selected" confirmed RED the same way against removing `itemMissing` from `handleSubmit`'s guard (first draft of the test left `description` blank too, which masked the defect by blocking the submit for an unrelated reason — fixed by filling every other field validly before asserting). Its "previews a part line's subtotal ... never posting a stock movement" test confirmed RED against an injected fake `PUT /api/inventory/movements/...` call from `handleSelectItem`. The offline scenario mirrors the already-established `NewCustomerPage.test.tsx`/`NewVehiclePage.test.tsx` pattern (disables submission, no API call), not separately RED-verified beyond that precedent.

- [x] **P2.S5.T2 (GREEN)** Create `NewWorkOrderPage.tsx` (customer search → vehicle pick → create, client id generated once per mount), `ItemPicker.tsx` (reuses inventory's `useItems`), `LineEditorDialog.tsx`, and wire `WorkOrderLines.tsx` to add/edit/remove lines through `hooks.ts` mutations added this slice (`useAddLine`, `useUpdateLine`, `useRemoveLine`) — each `setQueryData`s the order detail from the mutation's full-order response per `design.md`. **Deviations (minimal, necessary):**
  - `web/src/shared/api/http.ts` gained a `delete` method — the only HTTP verb the shared client was missing, needed for `DELETE /work-orders/{id}/lines/{line_id}`.
  - `routes.tsx` gained a literal `nueva` segment ahead of `:orderId` (matching `design.md`'s `/ordenes/nueva?vehiculo=` route), and `WorkOrdersPage.tsx` gained a "Nueva orden" button so the route is reachable from the UI, not just by URL (the `?vehiculo=` pre-selection itself is P2.S7's job, once a vehicle detail screen can link to it).
  - **Pre-existing bug fixed in the same file this slice already touches:** `WorkOrderDetailPage.tsx` read `useParams<{ id: string }>()`, but `routes.tsx` (written in S4) defines the segment as `:orderId` — through the real app router (`app/router.tsx`'s nested `/ordenes` route), this param was always `undefined`, so every order detail page would have fetched `/api/work-orders/` with an empty id. S4's own test never caught it because it mounted an isolated `<Route path="/ordenes/:id">` matching the component's (wrong) param name instead of the real route tree. Fixed the component to read `orderId`, and updated `WorkOrderDetailPage.test.tsx`'s two route mounts to `:orderId` to match.
  - `LineEditorDialog`'s fields initialize once from `initialLine`/`mode` and never reset via an effect (this repo's lint config forbids `setState` in an effect body); the caller remounts it with a fresh `key` per dialog open instead (documented in both files).

- [x] **P2.S5.T3** Run T1, confirm green. **Result:** all three new test files green (`NewWorkOrderPage.test.tsx` 2, `LineEditorDialog.test.tsx` 3), each independently RED-confirmed per T1's note above.

- [x] **P2.S5.T4** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`. **Result:** eslint clean; `tsc -b --noEmit` clean; vitest 128 passed (30 files, 5 new). `api/` was untouched by this slice; re-ran its suite anyway as a baseline check: `ruff check`/`ruff format --check` clean (94 files), `pytest` 190 passed, unaffected.

- [x] **P2.S5.T5** Work-unit commit: `:sparkles: feat(workorders): add the new-order flow and the line editor`.

### Slice P2.S6 — Web: status actions, WhatsApp builders, lazy share sheet

- [x] **P2.S6.T1 (RED)** Write `web/src/features/workorders/whatsapp.test.ts`:
  - `buildWhatsAppUrl("98765432", "a & b #2")` → `https://wa.me/50498765432?text=a%20%26%20b%20%232`. **Defect it catches:** a missing `504` country code, or an unencoded `&`/`#` truncating the message in WhatsApp.
  - `buildOrderSummary` includes the order number, vehicle, every line, and the formatted (not raw-cents) total. **Defect it catches:** the summary omits a line kind or leaks raw integer cents to the customer.
  - The share button renders only when `customer.phone_is_mobile === true` (hidden for `false` or `null`). **Defect it catches:** WhatsApp is offered to a landline or a phoneless customer.
  - With `navigator.canShare({ files })` returning `true`, triggering share with photos selected calls `navigator.share` with those files and the text; with it unsupported/`false`, the button is a plain anchor to the `wa.me` link and no picker is offered. **Defect it catches:** the file-share branch is offered where it cannot work, or the fallback never engages.
  **Result (RED→GREEN):** the pure-function scenarios landed in `whatsapp.test.ts` (confirmed RED by moving `whatsapp.ts` aside: `Failed to resolve import`); the button/share-sheet scenarios landed in a separate `ShareWhatsAppButton.test.tsx` (confirmed RED the same way, by moving `ShareWhatsAppButton.tsx`/`share/ShareSheet.tsx` aside), since the first file has no JSX/React dependency and the other two test a component plus its lazy child — splitting them follows this change's own "one `*.test.tsx` per container" convention instead of forcing component tests into a `.test.ts` file. Both green after restoring the implementation files (T3/T4): 5 + 4 tests passing. **Deviation (minimal, necessary):** `buildOrderSummary`'s own test asserts against `formatCents(50000)` rather than a hand-typed `"L 500.00"` literal -- `Intl.NumberFormat("es-HN", ...)` renders a non-breaking space (` `) between the symbol and the amount, which a plain string literal with a regular space silently fails `toContain` on (caught while running this very test).

- [x] **P2.S6.T2 (RED)** Write status-action tests: the rendered buttons come exactly from the order's `allowed_transitions` (not a hard-coded client-side table); they are disabled offline with the Spanish message; after a successful "Iniciar trabajo", the inventory queries (`inventoryQueryKey`) are invalidated so stock refetches. **Defect it catches:** a hard-coded transition table drifts from the server, an offline status change is attempted, or the inventory list shows stale stock after work starts. **Result (RED):** `StatusActions.test.tsx` confirmed RED by moving `StatusActions.tsx` aside (`Failed to resolve import`) before T5 existed.

- [x] **P2.S6.T3 (GREEN)** Create `web/src/features/workorders/whatsapp.ts`: `buildWhatsAppUrl`, `buildOrderSummary` (templates from `copy.ts` only), `supportsFileShare`. Run T1, confirm green. **Result:** green (5 tests in `whatsapp.test.ts`).

- [x] **P2.S6.T4 (GREEN)** Create `ShareWhatsAppButton.tsx` and the lazy `share/ShareSheet.tsx` (`React.lazy` + `Suspense`, `<input type="file" accept="image/*" capture="environment" multiple>`; clipboard-copy-then-`navigator.share` path per AD-18; `File` objects live only in component state, dropped on close). **Result:** green (4 tests in `ShareWhatsAppButton.test.tsx`). Also wired both components into `WorkOrderDetailPage.tsx` (needed for either to be reachable at all), reading the workshop name from the already-cached session via `useSession()`.

- [x] **P2.S6.T5 (GREEN)** Create `StatusActions.tsx`: buttons from `order.allowed_transitions`, disabled via `useOnlineStatus()`; on success, invalidate `inventoryQueryKey(workshopId)` in addition to the order/list keys. Run T2, confirm green. **Result:** green (3 tests in `StatusActions.test.tsx`). Added `useChangeStatus` to `hooks.ts` and `changeStatus`/`ChangeStatusPayload` to `api.ts` (the client for the already-existing `PUT /work-orders/{id}/status`, from Slice 3); reused the existing `useLineMutationCacheUpdate` helper for the order/list cache update, adding only the extra `inventoryQueryKey` invalidation on top. Also wired `StatusActions` into `WorkOrderDetailPage.tsx` (same reasoning as T4) and updated that page's own existing test (`WorkOrderDetailPage.test.tsx`), which had explicitly deferred asserting on status actions to this slice.

- [x] **P2.S6.T6** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`. **Result:** eslint clean; `tsc -b --noEmit` clean; vitest 140 passed (33 files, 3 new: `whatsapp.test.ts`, `ShareWhatsAppButton.test.tsx`, `StatusActions.test.tsx`). `api/` was untouched by this slice; re-ran its suite anyway as a baseline check: `ruff check`/`ruff format --check` clean (94 files), `pytest` 190 passed, unaffected.

- [x] **P2.S6.T7** Work-unit commit: `:sparkles: feat(workorders): add status actions and WhatsApp sharing with photos`.

### Slice P2.S7 — Phase 2 closing: customer/vehicle order history, seed, docs, migration round-trip, real-browser + Android check

- [x] **P2.S7.T1 (GREEN)** Modify `web/src/features/customers/CustomerDetailPage.tsx` and `VehicleDetailPage.tsx`: list that customer's/vehicle's work orders (most recent first), and a "Nueva orden" action from the vehicle detail. **Result:** `CustomerDetailPage.tsx` gained a new "Órdenes" section using `useWorkOrdersForCustomer`; `VehicleDetailPage.tsx` gained the same plus a "Nueva orden" button navigating to `/ordenes/nueva?vehiculo=<id>`. Added `useWorkOrdersForVehicle`/`useWorkOrdersForCustomer` to `workorders/hooks.ts` (plain `useQuery`, `statusGroup: "all"`, reusing the existing list query-key prefix so existing invalidation covers them). `NewWorkOrderPage.tsx` reads the `?vehiculo=` param, preselects that vehicle and its owner (falling back to the normal customer/vehicle picker if the preselected vehicle fails to load), and hides "Cambiar vehículo" when preselected.

- [x] **P2.S7.T2 (RED→GREEN)** Write/confirm a test: a vehicle with two work orders shows both, most recent first, on its detail screen. **Defect it catches:** the vehicle's service history is missing, filtered to the wrong vehicle, or unordered, leaving a mechanic unable to tell what was last done to this vehicle. **Result (RED→GREEN):** `VehicleDetailPage.test.tsx`'s new "shows that vehicle's work orders, most recent first" confirmed RED by stashing `VehicleDetailPage.tsx`/`workorders/hooks.ts` (failed with `TestingLibraryElementError`), confirmed GREEN after restoring. Also added a companion test in `NewWorkOrderPage.test.tsx` ("skips the customer and vehicle pickers when opened with a `?vehiculo=` preselection"), RED→GREEN-confirmed the same way.

- [x] **P2.S7.T3** Extend `deploy/demo/seed-demo-account.sh`: add the orders and lines from `design.md`'s seed table (Corolla brakes `in_progress`, CG 150 service `quote`, Frontier oil `completed`, Accent diagnosis `approved`, Corolla alignment `delivered`, Pulsar `cancelled`), driving each through the real create/line/status endpoints step by step, treating a `409 invalid_status_transition` as "tester-moved, kept." **Idempotency/rerun check:** run the extended script twice against the same database and confirm the second run creates no new orders/lines (relies on create/line replay idempotency) before checking this off. **Result:** added deterministic `order_ids`/`order_lines`/`status_sequence` data and three new loops (create orders, create lines, drive status transitions one edge at a time via `TRANSITIONS`). Verified with `bash -n` (syntax OK) and a full manual read-through of the idempotency chain (replay-matched creates return 200 on rerun, status PUTs either no-op at 200 or 409-and-kept); **not** exercised against a live database this pass — no demo deployment was authorized, so the rerun check itself is a deviation (see risks), not a live-verified result.

- [x] **P2.S7.T4** Update `deploy/demo/README.md`: document the seeded orders/states and that the demo now exercises stock consumption. **Result:** added a 6-row orders table (order/vehicle/status/lines) and a paragraph on the status-lifecycle driving and stock-consumption visibility; updated the "Demo account" intro.

- [x] **P2.S7.T5** Update `CLAUDE.md`: document the `work-orders`/`work-order-stock-consumption` features, the accepted cross-feature dependency (AD-2: `workorders.application` calling `inventory.application.record_movement`/`get_item` directly, never inventory's adapters/models), and the per-line reconciliation idiom (AD-4). **Result:** added a `workorders` feature paragraph (numbering via `workshop_counters` upsert, `describe_vehicles` batching) and a "Stock consumption" paragraph (`plan_reconciliation`, deterministic ids, delta-only posting, one-transaction atomicity, `(item_id, line_id)` lock ordering); updated the feature lists and the stale "Órdenes tab is a placeholder" sentence; updated the stock-ledger replay-matching sentence to mention `order_id`/`order_line_id` in the comparison tuple.

- [x] **P2.S7.T6** Exercise the phase-2 migration round-trip locally (`upgrade head` → `downgrade -1` → `upgrade head`); confirm `test_migrations.py` is green. **Result:** `alembic upgrade head` (already at head) → `alembic downgrade -1` (`8db9fb7d17ef` → `1b224b5a2186`) → `alembic upgrade head` (`1b224b5a2186` → `8db9fb7d17ef`), all clean; `pytest tests/test_migrations.py` passed (`alembic check` reports no drift).

- [x] **P2.S7.T7** Run the full phase-2 verification suite: API (`ruff check`, `ruff format --check`, `pytest`); Web (`lint`, `typecheck`, `test -- --run`, `build`); migration round-trip (T6). **Result:** API — `ruff check` clean, `ruff format --check` clean (94 files), `pytest` 190 passed. Web — `eslint .` clean, `tsc -b --noEmit` clean, `vitest --run` 142 passed (33 files), `vite build` succeeded. Migration round-trip: see T6.

- [x] **P2.S7.T8** Deploy phase 2 to the demo and re-run the seed script. **Evidence:** `alembic upgrade` applied `8db9fb7d17ef` to the demo database cleanly. The first seed run created 6 orders, 10 lines and 11 status changes. Two more runs created nothing, and the ledger stayed identical before and after the third run: 13 movements, one order per status, total stock 47.

- [x] **P2.S7.T9** Real-browser check at **390×844** against the deployed demo, covering phase 2's success criteria: sequential numbering with no skip on a double-submit; a 3-line-kind order's total; `in_progress` lowering linked stock with the history link, edited quantity posting only the delta, cancellation restoring stock, retries not double-applying; WhatsApp share opening with a prefilled summary for a mobile customer and being absent for a landline/phoneless one; vehicle detail listing its orders; the seeded demo showing orders in several states with the in-progress stock effect visible. Plus a manual **Android Chrome** check of photo sharing (per `design.md`'s testing-strategy note). **Evidence (390×844, public demo):**
  - The six seeded orders list with number, customer/vehicle and a lempira total.
  - New order #7 has labor L 200 + Bujía NGK ×2 (L 240) + external part L 360, for a total of L 800.
  - Approve → start dropped Bujía NGK from 16 to 14, with "Salida −2" linked to "Orden #7" in the item history. Cancel restored it to 16, with "Entrada +2" linked to the order.
  - The WhatsApp link is `https://wa.me/504` + 8 digits with a URL-encoded summary for a mobile customer, and absent for a landline customer.
  - Customer and vehicle details list their orders.
  - Each screen has one `<main>` and one `<h1>`, at full width.
  - Offline, the cached list renders and every write is disabled with its Spanish message.
  - The console was clean apart from the expected pre-login 401.
  - The check exposed a one-tap irreversible "Cancelar orden", which rendered first because the API sorts `allowed_transitions` alphabetically. Fixed in `b94f6d8` (forward actions first, a confirmation dialog) and re-checked on the demo: dismissing sends no status request.
  - Numbering under double-submit, delta posting on edits and retry idempotency were not repeated in the browser; the API concurrency and stock tests cover them.

- [ ] **P2.S7.T9b** Manual **Android Chrome** check of photo sharing via the Web Share API with files. **Pending:** needs a real Android phone; it cannot be emulated in desktop Chromium.

- [x] **P2.S7.T10** Work-unit commit: `:sparkles: feat(workorders): show order history on customer and vehicle detail` (covers T1–T2) followed by `:hammer: chore(deploy): seed phase 2 work orders, document stock consumption` (covers T3–T5). **Result:** `7757b39` and `b2ef6fb` on `feat/workshop-core-work-orders`.

### Slice P2.S8 — Review fixes (phase 2 findings)

- [x] **P2.S8.T1 (RED→GREEN)** Fix the critical finding: `update_work_order` (PATCH `/work-orders/{id}`) read the order via `order_repo.get_by_id` (no row lock) and then did a blind full-row `save()`, so a concurrent `change_status`/line edit committed in that window could be silently reverted by the PATCH's own stale snapshot (`design.md`'s AD-5 requires every mutating work-order use case to lock the order row first). **Result:** changed `update_work_order` to call `order_repo.get_for_update` instead of `get_by_id` (`api/src/taller/workorders/application/use_cases.py`), and updated its docstring. Added `test_update_work_order_does_not_revert_a_concurrently_committed_status_change` to `api/tests/workorders/test_work_order_concurrency.py`, using a `_ReadPausingWorkOrderRepository` test wrapper that deterministically lands a concurrent `change_status` commit between the PATCH's own read and its `save()` (no sleep-based timing beyond a 1s upper bound on the buggy path's instant signal). Confirmed RED against the unfixed code (`assert 'quote' == 'approved'` — the committed `approved` status was reverted to `quote`); confirmed GREEN after the fix, re-run 5× with no flake.

- [x] **P2.S8.T2** Investigated, not applicable: the finding that `CustomerDetailPage`'s new unconditional `useWorkOrdersForCustomer` call breaks the pre-existing `CustomerDetailPage.test.tsx` under this repo's MSW policy. **Result:** empirically false at the time — ran `npm test -- --run src/features/customers/CustomerDetailPage.test.tsx` and the full `npm test -- --run` (143 passed, 33 files), both clean. `web/src/test/setup.ts`'s `server.listen({ onUnhandledFrame: "error" })` configures both HTTP and WebSocket unhandled-request handling (MSW 3 replaced 2.x's `onUnhandledRequest` with this one option; this slice's original note that it was WebSocket-only was wrong), but its `"error"` strategy only logs a console error and answers with a network error — it does not fail the test by itself. The unmocked `GET /api/work-orders` request therefore logged an MSW console error but did not fail the test, since nothing in the test asserted on the orders query. No code change made at the time. **Correction (verify-gap-closure pass, see P2.S9):** `setup.ts` now also subscribes to MSW's `request:unhandled` life-cycle event and fails the test in `afterEach` on any unmocked request, so this exact case — a query that silently falls back on an unmocked endpoint — is now caught instead of passing quietly.

- [x] **P2.S8.T3 (RED→GREEN)** Fix the minor finding: the API's `work_order_create_failed` error code (the unexpected-`IntegrityError` branch in `create_work_order_route`) had no entry in `web/src/features/workorders/copy.ts`'s `ERROR_MESSAGES`, falling through to the generic message. **Result:** added the mapping (`"No se pudo crear la orden. Intente de nuevo."`). Added a test to `NewWorkOrderPage.test.tsx` asserting the specific message renders (and the generic one does not) for a `work_order_create_failed` 500 response; confirmed RED with the mapping stashed, GREEN restored.

- [x] **P2.S8.T4** Run the full verification suite: API — `uv run ruff check .` (clean), `uv run ruff format --check .` (94 files), `uv run pytest` (191 passed). Web — `npm run lint` (clean), `npm run typecheck` (clean), `npm test -- --run` (143 passed, 33 files), `npm run build` (succeeded).

- [x] **P2.S8.T5** Work-unit commits: one for the API lock fix, one for the web copy fix.

### Slice P2.S9 — Verify gap closure (post-verify follow-up)

Closes four coverage/test-infrastructure gaps raised in a post-verify pass over phase 2: the order-header lock, the `vehicle_id`/`customer_id` list filters, the line editor's offline behavior through its real container, and MSW's unhandled-request strictness. Test-first throughout; every new test ran once against the existing code before any related production or doc change.

- [x] **P2.S9.T1 (coverage, GREEN on first run)** Added `test_patching_a_delivered_order_is_locked` and `test_patching_a_cancelled_order_is_locked` to `api/tests/workorders/test_work_orders_api.py` (plus a `_set_status` helper): `PATCH /work-orders/{id}` on a `delivered`/`cancelled` order must answer 409 `work_order_locked` and leave the order unchanged. **Result:** both green immediately against the unmodified `update_work_order`/`EDITABLE` code — a coverage gap, not a bug: the header lock was already correct, just untested at the order level (lines were already covered in `test_stock_consumption.py`).

- [x] **P2.S9.T2 (coverage, GREEN on first run)** Added `test_list_filters_by_vehicle_id_and_customer_id` and `test_list_filtering_by_another_workshops_vehicle_or_customer_id_returns_nothing` to the same file: `GET /work-orders?vehicle_id=`/`?customer_id=` must return only that vehicle's/customer's orders, and another workshop's id must return `[]`, never that workshop's own unfiltered list. **Result:** both green immediately against the unmodified `SqlAlchemyWorkOrderRepository.list` — again a coverage gap: the `workshop_id` filter was already applied unconditionally alongside the optional ones.

- [x] **P2.S9.T3 (coverage, GREEN on first run)** Added a test to `web/src/features/workorders/WorkOrderDetailPage.test.tsx` (plus a `goOffline()` helper mirrored from `ItemDetailPage.test.tsx`): open the line editor dialog online, then drop the connection — `LineEditorDialog`'s "Guardar línea" must disable with `workOrdersCopy.offline.lineEditDisabled` and the add-line request must never fire. **Result:** green immediately — `WorkOrderDetailPage` already threads `useOnlineStatus()` into `offline={isOffline}` correctly; this was an untested wiring path (the dialog's own unit test only ever passed `offline={false}`/`offline={true}` as static props, never through the real container's live state).

- [x] **P2.S9.T4 (RED→fix, test infrastructure)** `web/src/test/setup.ts`'s `server.listen({ onUnhandledFrame: "error" })` only logs and network-errors an unmocked request; per MSW 3.0.2's own type declarations (`node_modules/msw/lib/_chunks/interceptor-source.d.ts`, confirmed against source, not guessed) it does not fail the test. Added a `request:unhandled` life-cycle listener (`server.events.on(...)`) collecting every unmocked request per test, and a final `afterEach` that throws if any occurred (registered last, so the existing `resetHandlers`/`onlineManager`/IndexedDB cleanup hooks still run first). **Result (RED → fixed):** the full web suite went from 144 passed to 5 files / 14 tests failing on real missing handlers:
  - `NewItemPage.test.tsx`, `NewCustomerPage.test.tsx`, `NewVehiclePage.test.tsx` (4 tests each): none of these ever mocked `GET /api/auth/me`, which `useWorkshopId()` fetches for real when unmocked. Fixed by adding a `SESSION` constant and a file-level `beforeEach` registering `http.get("/api/auth/me", ...)` in each file (the same shape `EditItemPage.test.tsx` already used per-test).
  - `ItemDetailPage.test.tsx`'s 404 test: `useMovements` fires unconditionally alongside the item fetch, so the 404 case also needed `GET /api/inventory/items/item-1/movements` mocked. Fixed by adding that handler to the test's existing `server.use(...)`.
  - `CustomerDetailPage.test.tsx`'s vehicle-listing test: `useWorkOrdersForCustomer` (added in P2.S7) fires unconditionally alongside the vehicle fetch and was never mocked here — exactly the P2.S8.T2 finding, previously tolerated by the non-strict config. Fixed by adding a mocked `GET /api/work-orders` response and a new assertion that the rendered order (`"Orden #7"`) appears; scoped the pre-existing vehicle assertions to the vehicles `<section>` (via `within`) since the mocked order's own vehicle text otherwise collided with the plate assertion.
  After these five fixes, the full suite is back to green with the stricter check active; no production code changed for this task, and no false-positive (failing-but-harmless) case was found.

- [x] **P2.S9.T5 (docs)** Corrected `CLAUDE.md`'s MSW paragraph: `onUnhandledFrame: "error"` alone does not fail a test (only logs and network-errors the request); `setup.ts`'s own `request:unhandled` listener is what fails it now. Corrected `tasks.md` P2.S8.T2 (above): its claim that `onUnhandledFrame` "only configures MSW's WebSocket frame handling, not HTTP" was wrong — MSW 3 uses this one option for both HTTP and WebSocket, replacing 2.x's `onUnhandledRequest`; kept its conclusion that the finding did not break the test at the time, and noted that strict mode (T4 above) now catches that exact case.

- [x] **P2.S9.T6** Full verification. API: `uv run ruff check .` (clean), `uv run ruff format --check .` (94 files), `uv run pytest` (195 passed = 191 baseline + 4 new work-order tests). Web: `npm run lint` (clean), `npm run typecheck` (clean), `npm test -- --run` run twice after the MSW change (144 passed both times, no flake), `npm run build` (succeeded, main chunk 440.43 kB / gzip 130.71 kB).

- [x] **P2.S9.T7** Work-unit commits: one for the API tests (T1–T2), one for the web line-editor test (T3), one for MSW strictness plus its test fixes and docs (T4–T5).

---

## Phase 3: Payments, non-fiscal receipt, daily cash summary, export

### Slice P3.S1 — API: payments, balance, void, cancellation guard

- [x] **P3.S1.T1 (RED)** Write `api/tests/workorders/test_payments_api.py`, before the payments code exists:
  - Recording a payment against an existing order of the authenticated workshop → saved against that order; a nonexistent/foreign order id → HTTP 404 `work_order_not_found`. **Defect it catches:** the order reference is dropped, or tenancy is unchecked.
  - A supported method (`transfer`) is accepted; an unsupported value (`transferencia`, `check`) → HTTP 422, no payment created. **Defect it catches:** the Spanish label or an arbitrary string is accepted as a wire value.
  - Replaying an identical payment create → HTTP 200, paid total unchanged; the same id with a different amount → HTTP 409 `payment_id_conflict`. **Defect it catches:** a retry double-counts a payment.
  - A payment against `quote` or `cancelled` → HTTP 409 `work_order_not_payable`; a deposit against `approved` is accepted. **Defect it catches:** payments are accepted before approval or after cancellation, or wrongly rejected on a legitimate deposit.
  - A payment exceeding the balance (including against an already-settled, zero-balance order) → HTTP 409 `payment_exceeds_balance`, no payment created. **Defect it catches:** overpayment is recorded instead of rejected.
  - **Replaying the exact payment that settled the order → HTTP 200, not `payment_exceeds_balance`.** **Defect it catches:** the balance check runs before replay detection (the ordering AD-14 requires).
  - A single full payment zeroes the balance; two partial payments (200 + 300 against 500) accumulate to a zero balance. **Defect it catches:** wrong paid/balance arithmetic.
  - Voiding a payment with no reason → HTTP 422, payment remains non-voided. **Defect it catches:** a reason-less void silently succeeds, losing the audit trail.
  - Voiding a payment excludes it from the order's paid total and balance due (balance increases back). **Defect it catches:** a voided payment still counts toward the totals.
  - Voiding twice is idempotent: the second void (any reason) → HTTP 200, payment unchanged, voided timestamp unchanged from the first void. **Defect it catches:** a second void re-stamps the timestamp or requires/overwrites the reason.
  - **Voiding a payment id that does not belong to the target order (either nonexistent, or recorded against a different order) → HTTP 404 `payment_not_found`.** *(Spec delta — not present in `specs/payments/spec.md`, which only covers the cross-workshop case via `work_order_not_found`. `design.md` has no code path for this either. Add this as the explicit 404 for an in-workshop, wrong-order/nonexistent payment id, distinct from the existing cross-workshop `work_order_not_found`.)* **Defect it catches:** voiding with a guessed or mistyped payment id silently 500s, or worse, voids an unrelated payment if the lookup is not scoped to `(order_id, payment_id)` together.
  - Workshop B voiding using workshop A's order id and payment id → HTTP 404 `work_order_not_found`, A's payment remains non-voided. **Defect it catches:** a missing tenancy check on the void endpoint.
  - Cancelling an order with one non-voided payment → HTTP 409 `work_order_has_payments`; cancelling an order whose only payment has been voided → succeeds. **Defect it catches:** a voided-only order can never be cancelled, or a paid order is wrongly cancellable.
  **Result (RED):** confirmed by stashing every P3.S1 production file (`domain/{entities,status,errors,money}.py`, `application/{ports,use_cases}.py`, `adapters/{models,repositories,schemas,router}.py`) before running this file: collection failed with `ImportError: cannot import name 'PaymentModel' from 'taller.workorders.adapters.models'`. Restored (GREEN against T3–T9): 24 of this file's 25 tests passed on the first run (the 25th is T2's concurrency test, below).

- [x] **P3.S1.T2 (RED)** Write a concurrency test: two concurrent payments that together would exceed the balance → exactly one succeeds. **Defect it catches:** the balance check runs without the order row lock, letting both payments through. **Deviation (minimal, necessary):** lands in `test_payments_api.py` itself (not a separate file), matching this unit's own "Focused test command" (`uv run pytest tests/workorders/test_payments_api.py`) in the Suggested Work Units table; it needs the same two-real-connections-and-threads pattern as `test_work_order_concurrency.py` (a `committed_payable_order` fixture committed on a connection outside the per-test SAVEPOINT), so that file's existing fixtures were mirrored rather than imported across test modules. **Result (RED):** confirmed by the same stash as T1 — `ImportError: cannot import name 'SqlAlchemyPaymentRepository'`. Restored (GREEN): passed, re-run 5× with no flake.

- [x] **P3.S1.T3** Create the phase-3 migration `api/migrations/versions/<rev>_payments.py`: `payments` table per `design.md`'s "Data model per phase → Phase 3" (including `ix_payments_workshop_paid_at (workshop_id, paid_at)`, `ix_payments_order_id`, `ck_payments_amount_positive`, `ck_payments_method`), plus a `voided_at`/`void_reason` column pair (nullable) to support the Resolved-Questions voiding feature — not shown in `design.md`'s original payments table, which predates that resolved question; add them here. Working `downgrade()` (drop `payments`). Add `import taller.workorders.adapters.models` to `api/migrations/env.py` if not already present from phase 2 (it is — confirmed, no change needed). **Result:** generated via `alembic revision --autogenerate` (revision `ffb1eb564de6`, parent `8db9fb7d17ef`) — unlike phase 2's ALTER-added columns, a brand-new `create_table` captures every `CheckConstraint` inline, so no hand-fix was needed beyond reformatting to the project's style (double quotes, `str | Sequence[str] | None`, `collections.abc.Sequence`). Upgrade → downgrade -1 → upgrade head: no errors; `uv run pytest tests/test_migrations.py` (`alembic check`) passed, no `MIGRATION_ONLY_INDEXES` fallback needed.

- [x] **P3.S1.T4 (GREEN)** Modify `api/src/taller/workorders/domain/entities.py`: add `Payment` (with `voided_at`/`void_reason`) and `PaymentMethod` (a `StrEnum`, mirroring `LineKind`'s existing convention for a closed wire-value field). Modify `domain/status.py`: add `PAYABLE`. Modify `domain/errors.py`: add `WorkOrderNotPayable`, `PaymentExceedsBalance`, `WorkOrderHasPayments`, `PaymentIdConflict`, `PaymentNotFound` (the spec-delta error from T1). Also added `domain/money.py`'s `paid_cents`/`balance_cents` helpers (alongside the existing `order_total_cents`), since computing the balance is a domain rule several call sites (the use case, the response schema) need identically.

- [x] **P3.S1.T5 (GREEN)** Modify `api/src/taller/workorders/application/ports.py`: `PaymentRepository` (`get_by_id` scoped by `(workshop_id, order_id, payment_id)` so a wrong-order id is a clean miss, `add`, `list_for_order`, `list_for_workshop_day` for S2). **Deviation (minimal, necessary):** also added `save(payment)` (persists `voided_at`/`void_reason`, the only mutable fields) — T5's own list omits it, but `void_payment` (T6) has no other way to persist a void, and every other mutating repository in this feature already exposes a `save`.

- [x] **P3.S1.T6 (GREEN)** Modify `api/src/taller/workorders/application/use_cases.py`: `record_payment` (lock the order row, replay check first, then status-in-`PAYABLE` check, then `amount_cents ≤ balance` check, then insert — AD-11's exact order), `void_payment` (looks up by `(workshop_id, order_id, payment_id)`, raises `PaymentNotFound` on a miss, requires a reason, idempotent), and extend `change_status`'s cancellation path to raise `WorkOrderHasPayments` when any non-voided payment exists. **Deviation (minimal, necessary, same reasoning as P2.S3.T3's `change_status`):** `paid_at`/the void timestamp use an inline `datetime.now(UTC)` rather than an injected `clock()` — every other use case in this file already follows that convention (no scenario in T1/T2 needs time manipulation), and `change_status` gained a new required `payment_repo` keyword-only parameter for the cancellation guard, so every existing caller (the router's `change_status_route`, and `test_work_order_concurrency.py`'s three call sites) was updated to build and pass a `SqlAlchemyPaymentRepository`.

- [x] **P3.S1.T7 (GREEN)** Modify `api/src/taller/workorders/adapters/repositories.py`: `SqlAlchemyPaymentRepository` (backed by the new `PaymentModel`) implementing `PaymentRepository`.

- [x] **P3.S1.T8 (GREEN)** Modify `api/src/taller/workorders/adapters/schemas.py`: `PaymentCreateRequest` (`method` a closed `Literal`, so an unsupported wire value is a standard 422 with nothing further to validate), `PaymentOut` (also carries `voided_at`/`void_reason`, beyond `design.md`'s original shape, for the same struck-through-in-the-web reason as T3's migration delta), `VoidPaymentRequest` (`{reason}`, required and non-nullable so a missing or explicit-`null` reason is a standard 422 with no extra validator needed); extend `WorkOrderOut`/`from_domain` with `payments`, `paid_cents`, `balance_cents`, `accepts_payments`.

- [x] **P3.S1.T9 (GREEN)** Modify `api/src/taller/workorders/adapters/router.py`: `POST /work-orders/{id}/payments`, `POST /work-orders/{id}/payments/{pid}/void`; map `PaymentNotFound` → 404 `payment_not_found` (the spec delta), `WorkOrderNotPayable` → 409, `PaymentExceedsBalance` → 409, `PaymentIdConflict` → 409; extend the `PUT .../status` handler's cancellation path to map `WorkOrderHasPayments` → 409. Every route building a `WorkOrderOut` response now also builds a `SqlAlchemyPaymentRepository` and passes it to `_to_out` (extended to embed `payments`). Run T1 and T2, confirm both are green.

- [x] **P3.S1.T10** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest`. **Result:** ruff check clean; ruff format clean (97 files); pytest 220 passed (195 existing + 25 new in `test_payments_api.py`, including its concurrency test), re-run 3× with no flake on `test_payments_api.py`'s and `test_work_order_concurrency.py`'s concurrency tests.

- [x] **P3.S1.T11** Work-unit commit: `:sparkles: feat(workorders): record and void payments against a work order`.

### Slice P3.S2 — API: cash summary and timezone tests

- [x] **P3.S2.T1 (RED)** Write `api/tests/workorders/test_cash_summary.py`:
  - A payment at `2026-10-07T05:59:00Z` (23:59 Oct 6 Honduras) falls into Oct 6's totals when Oct 6 is requested; one at `06:01:00Z` (00:01 Oct 7) falls into Oct 7's. **Defect it catches:** a UTC or server-local day boundary instead of `America/Tegucigalpa`.
  - Mixed-method totals (300 cash, 150 transfer, 50 card) → cash 300, transfer 150, card 50, other 0, grand total 500; **all four method keys are always present**, even with zero payments. **Defect it catches:** a missing method key when it has no payments that day.
  - Only the requesting workshop's payments contribute. **Defect it catches:** a tenant leak into another workshop's summary.
  - A voided payment contributes to neither its method's total nor the grand total, and does not appear in the day's listed payments. **Defect it catches:** a voided payment still shows up in the drawer reconciliation.
  - **Deviation (minimal, necessary):** also added `test_a_malformed_date_query_parameter_is_rejected`, covering T3's own "a malformed date → 422" contract line (not listed among T1's four scenarios, but it is this slice's only coverage of that behavior). Since `record_payment` always stamps `datetime.now(UTC)` (no injectable clock there), the near-midnight and mixed-method scenarios create each payment through the real API, then directly rewrite its `PaymentModel.paid_at` via the shared `db_session` (the same session the `TestClient`'s routes use) — there is no other way to place a payment at an exact instant. **Result (RED):** confirmed before any production change existed: all 6 tests failed with `404 Not Found` (`GET /api/cash-summary` not yet mounted) rather than passing trivially.

- [x] **P3.S2.T2 (GREEN)** Modify `api/src/taller/workorders/application/use_cases.py`: `daily_cash_summary(workshop_id, day, clock, payment_repo, order_repo)` per AD-20 (`ZoneInfo("America/Tegucigalpa")` as module-level `HONDURAS_TZ`, `day` defaulting to `clock.now().astimezone(HONDURAS_TZ).date()` using identity's injectable `Clock` protocol, the sargable `paid_at >= start AND paid_at < end` range via the existing `PaymentRepository.list_for_workshop_day`, totals grouped by method in Python with all four `PaymentMethod` keys always present via `dict.fromkeys(PaymentMethod, 0)`, excluding voided payments from both the totals and the returned entries). **Deviation (minimal, necessary):** the response needs each listed payment's order number (`design.md`'s "Cash summary" note: "The response also lists the day's payments with their order numbers"), so also added `CashSummaryEntry` (`api/src/taller/workorders/domain/entities.py`, mirroring inventory's `MovementHistoryEntry` convention) and a batched `WorkOrderRepository.numbers()` port method (`api/src/taller/workorders/application/ports.py` + `SqlAlchemyWorkOrderRepository.numbers()` in `adapters/repositories.py`, mirroring the existing `totals()` method) — neither exists in `design.md`'s table, which only lists the already-existing `PaymentRepository`/`record_payment`/cancellation-guard changes from slice 1.

- [x] **P3.S2.T3 (GREEN)** Modify `api/src/taller/workorders/adapters/schemas.py`: `CashSummaryOut` (plus `CashSummaryTotalsOut`, `CashSummaryPaymentOut`). Modify `api/src/taller/workorders/adapters/router.py`: `GET /cash-summary?date=YYYY-MM-DD` (default today, Honduras local, via the `get_clock` dependency already used by identity's login throttling; a malformed date → 422 for free, from FastAPI's own `date` query-parameter parsing). Ran T1: green.

- [x] **P3.S2.T4** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest`. **Result:** ruff check clean; ruff format clean (one new test file auto-reformatted, then clean); pytest 226 passed (220 existing + 6 new in `test_cash_summary.py`). The dev machine's system has the `America/Tegucigalpa` zone in its tz database (confirmed via `python -c "from zoneinfo import ZoneInfo; ZoneInfo('America/Tegucigalpa')"`) — no `tzdata` package needed here; `design.md`'s Risks note about a slim deployment image lacking it still stands, unverified against the demo host in this apply pass.

- [x] **P3.S2.T5** Work-unit commit: `:sparkles: feat(workorders): add the daily cash summary by payment method`.

### Slice P3.S3 — API: export (pure builder, then endpoint tenancy)

- [x] **P3.S3.T1 (RED)** Write `api/tests/export/test_csv_zip.py` (pure, no DB):
  - Every produced CSV starts with the UTF-8 BOM (`EF BB BF`). **Defect it catches:** Excel on Windows mojibakes accented names without it.
  - `José Núñez` round-trips byte-for-byte through the writer. **Defect it catches:** an encoding step silently strips or mangles accents.
  - A text cell starting with `=1+1` is written as `'=1+1`; a negative number is **not** prefixed. **Defect it catches:** formula injection in Excel, or the guard over-escapes legitimate negative numbers.
  - An empty table still produces a header-only CSV. **Defect it catches:** a workshop with no payments gets a missing file instead of an empty one.
  **Result (RED):** confirmed before `taller.export` existed at all: collection failed with `ModuleNotFoundError: No module named 'taller.export.application.csv_zip'`.

- [x] **P3.S3.T2 (GREEN)** Create `api/src/taller/export/__init__.py` and `application/csv_zip.py`: the pure CSV/ZIP builder (`csv.writer`, `utf-8-sig` encoding, the formula-injection guard, the money/`_hnl`-suffix and local-timestamp formatting rules from `design.md`'s "Export" section, no `sep=,` line). Run T1, confirm green. **Result (GREEN):** 5 passed. **Implementation note:** `format_money` returns a `Decimal`, never a `str` — the injection guard (`build_csv`'s `_render_cell`) only ever inspects `str` cells, so a negative balance ("saldo a favor") is written as `-50.00` and is never escaped, which is what "numeric columns are never prefixed" requires for a value that textually starts with `-`.

- [x] **P3.S3.T3 (RED)** Write `api/tests/export/test_export_api.py`:
  - The ZIP contains exactly one CSV per entity (customers, vehicles, items, inventory movements, work orders, work order lines, payments). **Defect it catches:** an entity is missing from the archive.
  - Only workshop A's rows appear when A requests the export; a client-supplied workshop id parameter is ignored. **Defect it catches:** a tenant leak, or a client-controlled scope parameter.
  - Two consecutive exports with no writes in between yield the same rows, and neither request creates/modifies/deletes any record. **Defect it catches:** the export has a side effect, or is non-deterministic absent writes.
  **Result (RED):** confirmed before `/api/export` existed: all 4 tests failed with `404 Not Found`.

- [x] **P3.S3.T4 (GREEN)** Create `api/src/taller/export/adapters/sources.py` (explicit column-list reads over each feature's ORM models, always `WHERE workshop_id = :current`) and `adapters/router.py` (`GET /export`, assembling the `BytesIO`/`zipfile` response with `Content-Disposition`/`Cache-Control: no-store`, per AD-13 — not a `StreamingResponse`, so the request's DB session stays open for the whole build). Run T3, confirm green. **Result (GREEN):** 4 passed. **Deviation (minimal, necessary):** `work_orders.csv`'s `total_hnl`/`paid_hnl`/`balance_hnl` are computed with two `GROUP BY order_id` aggregate queries over `WorkOrderLineModel`/`PaymentModel` (non-removed lines; non-voided payments) directly in `sources.py`, instead of importing `taller.workorders.domain.money`'s helpers — those take domain entities (`WorkOrderLine`, `Payment`), not model rows, and AD-1's dependency diagram draws `export.adapters` depending only on `customers/inventory/workorders models`, not their domain/application layers.

- [x] **P3.S3.T5 (GREEN)** Modify `api/src/taller/main.py`: mount the export router.

- [x] **P3.S3.T6** Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest`. **Result:** ruff check clean; ruff format clean (105 files, 2 auto-reformatted then clean); pytest 235 passed (226 existing + 9 new in `api/tests/export/`). Web was untouched by this slice; re-ran its suite anyway as a baseline check: `eslint .` clean, `tsc -b --noEmit` clean, `vitest --run` 146 passed (33 files), unaffected.

- [x] **P3.S3.T7** Work-unit commit: `:sparkles: feat(export): add the workshop-scoped CSV/ZIP export`.

### Slice P3.S4 — Web: payments on the order detail

- [x] **P3.S4.T1 (RED)** Write tests:
  - Recording a payment while offline is disabled with the Spanish message.
  - The payment-amount field parses `1,500.50` to `150050` cents (reusing `centsToPlainAmount`/`parseLempirasToCents`-equivalent logic, moved to `web/src/shared/` this slice if not already, per `design.md`'s note). **Defect it catches:** a thousands separator is mis-parsed into the wrong cent amount.
  - The 409 codes (`payment_exceeds_balance`, `work_order_not_payable`, `payment_id_conflict`) and the new `payment_not_found` each map to a distinct Spanish message, not a generic fallback.
  **Result:** `payments/PaymentForm.test.tsx` (money parsing + a zero-amount rejection) and five new `WorkOrderDetailPage.test.tsx` cases (offline disable; the three 409 codes; `payment_not_found` on void).

- [x] **P3.S4.T2 (GREEN)** If not already done in phase 2, move the lempira formatting/parsing helpers from `web/src/features/inventory/format.ts` to `web/src/shared/` (work orders is now a second consumer, per `design.md`'s File Changes note); re-export from `inventory/format.ts` if other inventory code still imports the old path, to avoid a wide mechanical rename in this slice. **Result:** already done in phase 2 (`web/src/shared/format/money.ts` exists and is already `LineEditorDialog.tsx`'s and now `PaymentForm.tsx`/`PaymentList.tsx`'s source of these helpers) — no action needed.

- [x] **P3.S4.T3 (GREEN)** Modify `web/src/features/workorders/copy.ts`: add the four payment-method labels and the new error-code messages (including `payment_not_found`). Modify `hooks.ts`: `useRecordPayment`, `useVoidPayment`. Create `payments/PaymentForm.tsx`, `payments/PaymentList.tsx`; wire into `WorkOrderDetailPage.tsx`. **Result:** `api.ts` gained `PaymentMethod`, `PaymentOut`, `CreatePaymentPayload`, `VoidPaymentPayload` and `WorkOrderOut.{payments,paid_cents,balance_cents,accepts_payments}` (always present, matching the already-shipped API contract) plus `recordPayment`/`voidPayment` client calls. `WorkOrderDetailPage.tsx` gained a "Pagos" section (paid/balance, `PaymentList`, and `PaymentForm` gated by `accepts_payments`, else an "Esta orden no acepta pagos en su estado actual." notice) and a client-generated payment id reused across a failed retry, regenerated only on success (the same double-submit idiom every other create in this app uses). `PaymentList` owns its own void confirm dialog (the shared `Dialog.tsx` pattern `StatusActions` already uses for cancellation), with a required reason.

- [x] **P3.S4.T4** Run T1, confirm green. **Result:** `npm test -- --run src/features/workorders` — 8 files, 32 tests passed.

- [x] **P3.S4.T5** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`. **Result:** eslint clean; tsc clean; vitest 153 passed (34 files, up from 146).

- [x] **P3.S4.T6** Work-unit commit: `:sparkles: feat(workorders): record payments on the order detail`.
  - **Risk flagged, not fixed (out of this slice's explicit scope):** `work_order_has_payments` (the cancel guard's 409, added by P3.S1) is still unmapped in `copy.ts`'s `ERROR_MESSAGES`, so cancelling a paid order still shows the generic fallback instead of an actionable message. T1/T3 only scoped the four payment-specific codes; flagging for the user/reviewer, as P3.S3 did for `payments.csv`'s missing void columns.

### Slice P3.S5 — Web: receipts (lazy routes, print CSS, measured 58 mm page)

- [x] **P3.S5.T1 (RED)** Write tests:
  - A receipt route for an order in `completed` or `delivered` renders that order's content; one for any other status renders no order data and shows the "only available once completed/delivered" message. **Defect it catches:** a quote or in-progress order's data is exposed through a receipt route.
  - Both layouts render "DOCUMENTO NO FISCAL — No válido como factura" visibly. **Defect it catches:** the receipt could be mistaken for a tax invoice.
  - A fully-paid order (total 500, paid 500) shows total 500.00, paid 500.00, balance 0.00; a partially-paid order (total 500, paid 200) shows balance 300.00. **Defect it catches:** a wrong balance printed on the customer's copy.
  - A receipt request for another workshop's order id → HTTP 404 `work_order_not_found`, no data rendered. **Defect it catches:** a tenant leak through the receipt route.
  **Result (RED):** confirmed by running `receipt/ReceiptBody.test.tsx`, `receipt/Receipt58Page.test.tsx` and `receipt/ReceiptLetterPage.test.tsx` before `ReceiptBody.tsx`/`Receipt58Page.tsx`/`ReceiptLetterPage.tsx`/`useReceiptOrder.ts` existed — import/collection failures on every scenario above.

- [x] **P3.S5.T2 (GREEN)** Create `receipt/ReceiptBody.tsx` (shared content: number, vehicle, customer name, lines with subtotal, total, paid, balance), `receipt/Receipt58Page.tsx`, `receipt/ReceiptLetterPage.tsx`, each its own react-router `lazy` route rendered **without** the shell (per AD-16 — guarded, but outside the `AppShell` layout route). Implement AD-19 exactly: a component-scoped inline `<style>` per layout (no `href`/`precedence`), the 58 mm layout's `useLayoutEffect`-measured `@page { size: 58mm <height>mm; margin: 0 }` with a `58mm 297mm` fallback before measurement, the full-page layout's `@page { margin: 12mm }` with no `size`, `print:hidden` on each action bar (the "Imprimir" button; `OfflineStatusBanner`'s own `print:hidden` is P3.S6.T5's job, not this slice's). Run T1, confirm green. **Deviations (minimal, necessary):**
  - **`receipt/useReceiptOrder.ts` (not in `design.md`'s file list):** both layouts need identical loading/not-found/eligibility gating (`WorkOrderDetailPage`'s same loading/404 handling, plus the receipt-only `completed`/`delivered` check). Extracted once into a small hook instead of duplicating that branching logic — and its tests — verbatim in both page components, so the eligibility rule can only drift from the spec in one place.
  - **`whatsapp.ts`'s `vehicleLabel` exported** (was module-private): `ReceiptBody` is its second consumer, reusing the exact same "make model · plate" join instead of a second copy, mirroring this change's own precedent for `formatCents` in phase 2 (P2.S4.T3).
  - Money labels reuse existing copy instead of new strings: the receipt's total/paid/balance labels reuse `workOrdersCopy.detail.totalLabel`/`payments.paidLabel`/`payments.balanceLabel`/`payments.creditLabel`, and the order title reuses `detail.orderTitle(number)`. Only `receipt.nonFiscalLabel`, `receipt.notEligible` and `receipt.print` are new copy keys.

- [x] **P3.S5.T3 (RED→GREEN)** Write/confirm a manual-equivalent automated check: at mount (before the `useLayoutEffect` measurement resolves), the 58 mm layout still renders a valid page with the fallback height. **Defect it catches:** printing immediately after mount (before measurement) produces an invalid or zero-height page. **Result:** jsdom has no layout engine, so `getBoundingClientRect()` always reports a zero height — every render of `Receipt58Page` in this suite exercises exactly the "before/without a real measurement" path a real browser only hits for an instant at mount. `Receipt58Page.test.tsx` asserts the `<style>` tag still carries the `58mm 297mm` fallback in that case (RED against removing the `heightPx > 0` guard, which would otherwise emit an invalid `58mm 0mm` page), and a second test mocks `getBoundingClientRect` to a valid height and confirms the measured value (`101.6mm` for a `384px` mock) replaces the fallback (RED against the measurement effect never actually applying).

- [x] **P3.S5.T4** Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`. **Result:** eslint clean; `tsc -b --noEmit` clean; vitest 165 passed (37 files, 12 new: 4 `ReceiptBody` + 5 `Receipt58Page` + 3 `ReceiptLetterPage`). `npm run build` also run as an extra check (not in this slice's required command, but cheap and confirms the lazy routes actually resolve): succeeded, with `Receipt58Page`, `ReceiptLetterPage` and `useReceiptOrder` each split into their own chunk, main chunk 448.44 kB gzip 132.59 kB. `api/` was untouched by this slice (`git status` confirmed no `api/` changes); not re-run.

- [x] **P3.S5.T5** Work-unit commit: `:sparkles: feat(workorders): add the 58mm and full-page non-fiscal receipts`.

### Slice P3.S6 — Phase 3 closing: cash summary page, export action, "Más" menu, seed, docs, real-browser + print-preview check

- [x] **P3.S6.T1 (RED)** Write tests:
  - The cash summary offline shows the Spanish "requires a connection" message, never stale cached numbers; its query key carries `meta: { persist: false }` and is absent from the persisted IndexedDB snapshot. **Defect it catches:** stale cash totals shown as current, or the summary accidentally persists.
  - Export offline is disabled; online it fetches `/api/export`, clicks a generated `<a download>`, and revokes the object URL afterward. **Defect it catches:** export attempted offline, or an object-URL leak.
  - **Result:** `cash/CashSummaryPage.test.tsx` (totals/payments render, offline message replaces a previously-fetched total), `export/exportData.test.ts` (download+revoke, 401→`not_authenticated`, network failure→`network_error`), `app/shouldPersistQuery.test.ts` (drops a `meta.persist === false` query, keeps a plain one), and `AppShell.test.tsx` additions (menu offers the three actions, export disabled offline with the Spanish message, export click downloads+revokes).

- [x] **P3.S6.T2 (GREEN)** Create `cash/CashSummaryPage.tsx` (lazy route; query with `meta: { persist: false }`) and `export/exportData.ts` (dynamic `import()` on click; `fetch("/api/export", { credentials: "same-origin" })`; 401 → existing session-expired handling; blob → object URL → temporary `<a download>` click → revoke).

- [x] **P3.S6.T3 (GREEN)** Modify `web/src/app/AppShell.tsx`/`router.tsx`: replace the P1 logout-only header action with a "Más" menu (Caja del día, Exportar todo, Cerrar sesión); add the lazy cash-summary and receipt routes. **Note:** the receipt routes were already added in P3.S5's own deviation; only the `caja` lazy route needed adding here, in `workorders/routes.tsx` (not `app/router.tsx`, which mounts `workOrderRoutes` wholesale).

- [x] **P3.S6.T4 (GREEN)** Modify `web/src/app/providers.tsx`: `shouldDehydrateQuery` skips any query whose `meta.persist === false`. Run T1, confirm green. **Deviation:** the predicate itself lives in a new `app/shouldPersistQuery.ts`, not inline in `providers.tsx` — `eslint-plugin-react-refresh`'s `only-export-components` rule rejects a non-component function export sharing a file with `AppProviders`.

- [x] **P3.S6.T5 (GREEN)** Modify `web/src/features/inventory/OfflineStatusBanner.tsx`: add `print:hidden` (it renders inside `RequireSession`, above every receipt route).

- [x] **P3.S6.T6** Extend `deploy/demo/seed-demo-account.sh`: add the two seeded payments from `design.md`'s table (Frontier L 500.00 `cash` partial; Corolla alignment L 400.00 `transfer` settled), treating a `409 payment_exceeds_balance` as "testers edited the order, kept." **Idempotency/rerun check:** run the script twice against the same database and confirm the second run creates no new payments before checking this off. **Result:** `bash -n` syntax-checked clean; not executed live this slice (no demo deploy — see T11), so the idempotency rerun itself is deferred to T11.

- [x] **P3.S6.T7** Update `deploy/demo/README.md`: document the seeded payments, the receipt routes, the cash summary, and "Exportar todo." Noted explicitly that the order-detail screen has no UI link to either receipt route yet (only the direct URL), so the docs don't overstate what's reachable from the UI.

- [x] **P3.S6.T8** Update `CLAUDE.md`: document payments (including voiding and the `payment_not_found` spec delta), the non-fiscal receipt, the cash summary's timezone handling, and the export module.

- [x] **P3.S6.T9** Exercise the phase-3 migration round-trip locally; confirm `test_migrations.py` is green. **Result:** `alembic downgrade 1b224b5a2186` (before phase 3's only migration) then `alembic upgrade head` round-tripped cleanly back to `ffb1eb564de6`; `test_migrations.py` passed as part of the full `pytest` run (T10).

- [x] **P3.S6.T10** Run the full phase-3 verification suite: API (`ruff check`, `ruff format --check`, `pytest`); Web (`lint`, `typecheck`, `test -- --run`, `build`); migration round-trip (T9). **Result:** `ruff check` all checks passed; `ruff format --check` 105 files already formatted; `pytest` 235 passed; `npm run lint` clean; `npm run typecheck` clean; `npm test -- --run` 175 passed (40 files; fixed 3 `AppShell.test.tsx` failures found on first run — two tests forgot to mock `GET /api/inventory/items`, one set `onlineManager.setOnline(false)` before the session query's first fetch instead of after, which paused it forever under TanStack Query's default `networkMode: "online"`); `npm run build` succeeded, with `exportData` and `CashSummaryPage` each in their own lazy chunk.

- [ ] **P3.S6.T11** Deploy phase 3 to the demo and re-run the seed script. **Deferred:** explicitly out of scope for this pass — no demo deploy or live seed run performed; `seed-demo-account.sh`'s new payments logic is syntax-checked only (T6).

- [ ] **P3.S6.T12** Real-browser check at **390×844** against the deployed demo, covering phase 3's success criteria: recording a payment updates paid total/balance; both receipt layouts render in print preview with the non-fiscal label visible; the daily cash summary shows seeded and newly recorded payments bucketed by Honduran local day; "Exportar todo" downloads a ZIP that opens in Excel with accents intact and only the current workshop's data; each phase's `downgrade()` already exercised locally. **Deferred:** explicitly out of scope for this pass — no real-browser or print-preview check performed; depends on T11's demo deploy.

- [x] **P3.S6.T13** Work-unit commit: `:sparkles: feat(workorders): add the cash summary, export and Más menu` (covers T2–T5) followed by `:hammer: chore(deploy): seed phase 3 payments and document exports` (covers T6–T8). Both titles trimmed from the plan's exact wording to fit the 72-character limit.

### Slice P3.S7 — Review fixes (phase 3 findings)

Re-checked three review findings against the code before fixing any of them; all three were real. Test-first throughout: each new test confirmed RED against the unfixed code before its production fix landed.

- [x] **P3.S7.T1 (RED→GREEN)** Fix the major finding: `payments.csv` (`api/src/taller/export/adapters/sources.py`) included voided payments with no indicator, so it was internally inconsistent with `work_orders.csv`'s own `paid_hnl` (already non-voided-only) in the same ZIP — summing `payments.csv` in Excel overstated recorded cash revenue by every voided amount. **Result:** added `voided_at`/`void_reason` to `PAYMENTS_HEADERS` and `payments_rows` (full ledger kept, per the `payments` spec's "never deleted" rule — no row excluded, matching `inventory_movements.csv`'s own full-history convention). Added `test_a_voided_payment_is_exported_with_its_void_columns` to `api/tests/export/test_export_api.py`, driving a real order through create → line → approve → payment → void and asserting the export's `payments.csv` carries the void columns while `work_orders.csv`'s `paid_hnl` stays `0.00`. Confirmed RED (`KeyError: 'voided_at'` from `csv.DictReader`) against the unfixed `sources.py`; confirmed GREEN after the fix. **Deviation (doc note, not a code change):** `design.md` line 748's `payments.csv` column list predates the voiding feature (per `design.md`'s own Resolved Questions and this change's P3.S1.T3 note) and was not updated — `design.md` is outside this slice's allowed edit surfaces; flagging here since this is the second place (after `PaymentModel`'s docstring) that documents the same column-list delta.

- [x] **P3.S7.T2 (RED→GREEN)** Fix the major finding: `PaymentList.tsx`'s "Anular" (void) trigger disabled itself offline, but the Spanish offline explanation only rendered inside the confirm dialog that disabled trigger is the only way to open — so an offline mechanic saw a greyed-out button with no explanation anywhere on screen, failing the `payments` spec's "Voiding Requires A Live Connection" scenario. **Result:** added the same always-visible `<Alert>` outside the dialog that `StatusActions.tsx`'s own cancel trigger already pairs with its disabled button (this PR's own established pattern), alongside the existing in-dialog alert (kept, for the case where the connection drops while the dialog is already open). Added `"shows the void-payment offline message without requiring the disabled Anular trigger to open the dialog"` to `web/src/features/workorders/WorkOrderDetailPage.test.tsx`. Confirmed RED (`screen.getByText(...)` threw — element not found) against the unfixed `PaymentList.tsx`; confirmed GREEN after the fix.

- [x] **P3.S7.T3 (RED→GREEN)** Fix the major finding: the 409 `work_order_has_payments` (cancelling an order with a non-voided payment) had no entry in `web/src/features/workorders/copy.ts`'s `ERROR_MESSAGES`, so the cancel flow fell through to the generic "Ocurrió un error. Intente de nuevo." instead of an actionable message — this is the exact risk `P3.S4.T6` had already flagged as out of that slice's scope. **Result:** added `work_order_has_payments: "No se puede cancelar una orden con pagos registrados. Anule los pagos primero."`. Added `"maps a 409 work_order_has_payments to its own Spanish message, not the generic fallback"` to `web/src/features/workorders/StatusActions.test.tsx`. Confirmed RED (generic fallback text, not the specific message) against the unfixed `copy.ts`; confirmed GREEN after the fix.

- [x] **P3.S7.T4** Run the full verification suite. API: `uv run ruff check .` (clean), `uv run ruff format --check .` (clean), `uv run pytest` (236 passed = 235 baseline + 1 new). Web: `npm run lint` (clean), `npm run typecheck` (clean), `npm test -- --run` (177 passed = 175 baseline + 2 new, 40 files), `npm run build` (succeeded).

- [x] **P3.S7.T5** Work-unit commits: one for the API export fix (T1), one for the two web copy/offline-message fixes (T2–T3).

### Slice P3.S8 — Browser-check fixes (defects found running the deferred P3.S6.T12 real-browser check)

Fixes three defects a real-browser check of this phase found (the check itself was deferred at P3.S6.T12/T11; the orchestrator ran an equivalent check against the deployed demo outside this task sequence and reported the findings back for this slice). Web-only; no API change.

- [x] **P3.S8.T1 (critical, fix)** Fix: a stale persisted TanStack Query cache crashed the app after a deploy. `web/vite.config.ts`'s `__APP_VERSION__` was `packageJson.version` alone, which stayed `0.1.0` across all three phases, so the persisted-cache `buster` (`web/src/app/providers.tsx`) never changed between deploys. Reproduced: a browser that had opened work order #1 under the phase 2 build (no `payments` field) reopened it under the phase 3 build and crashed with `TypeError: Cannot read properties of undefined (reading 'length')`, caught only by react-router's default English error screen; a fresh browser context opened the same order fine. **Result:** added `resolveBuildId()` to `vite.config.ts` (the git short SHA via `git rev-parse --short HEAD`, falling back to a build timestamp when git is unavailable) and set `__APP_VERSION__` to `` `${packageJson.version}+${resolveBuildId()}` ``, so every build -- not only a version bump -- busts the cache. Updated the explaining comments in `vite.config.ts`, `providers.tsx`, `vite-env.d.ts`, and `CLAUDE.md`'s offline paragraph. **New test (in-source, inside `vite.config.ts`, via Vitest's `includeSource` option, so it is not a separate file and `import.meta.vitest` is always `undefined` -- a no-op -- outside the test runner):** `resolveBuildId` returns the trimmed git SHA when git succeeds, and falls back to an injected timestamp both when git throws and when it prints only whitespace. **Confirmed RED:** temporarily short-circuited the success branch (`if (false)` in place of `if (sha)`), which failed the "returns the trimmed git short SHA" assertion with the timestamp fallback value instead of the SHA; restored and confirmed GREEN. **Verification:** after `npm run build`, `rg -o "0\.1\.0\+[0-9a-f]+" dist/assets/index-*.js` found `0.1.0+8f97273`, matching this worktree's `git rev-parse --short HEAD`.

- [x] **P3.S8.T2 (major, fix)** Fix: the receipt routes (`/ordenes/:orderId/recibo/58mm` and `/ordenes/:orderId/recibo/carta`) existed in `router.tsx` but nothing linked to them, so a user had no way to print a receipt. **Result:** `WorkOrderDetailPage.tsx` now renders two `LinkButton`s ("Recibo 58 mm", "Recibo carta") beside the status/share actions, gated by the receipt hook's own eligibility rule (`completed`/`delivered`) exported as `isReceiptEligible(status)` from `receipt/useReceiptOrder.ts` instead of a second, driftable status list. Copy added to `workorders/copy.ts`'s `receipt` object (`link58mm`, `linkLetter`). **New tests in `WorkOrderDetailPage.test.tsx`:** a `completed` order shows both links pointing at their exact routes (**confirmed RED** before the links existed: `getByRole("link", { name: "Recibo 58 mm" })` found nothing); a `quote` order shows neither (the negative half of the same scenario -- the defect this whole pair catches is either no way to reach the receipt, or a receipt offered for an unfinished order).

- [x] **P3.S8.T3 (minor, fix)** Fix: an unexpected render error anywhere in the protected route tree fell through to react-router's default "Unexpected Application Error!" screen, in English, with a raw stack trace. **Result:** added `app/AppErrorBoundary.tsx` (a plain Spanish message plus a "Recargar" button calling `window.location.reload()`) and wired it as `errorElement` on `router.tsx`'s pathless `RequireSession` layout route -- the root of the protected tree, so it also catches a crash inside `AppShell` itself. Copy added to `app/copy.ts`'s new `error` object. **New tests in `AppErrorBoundary.test.tsx` (a `createMemoryRouter`/`RouterProvider` slice, since `errorElement` is a data-router feature the declarative `<Routes>` used elsewhere in this suite does not support):** a route that throws renders "Algo salió mal", not react-router's own text. **Confirmed RED:** removed the `errorElement` wiring from the test's own router, which rendered react-router's built-in developer prompt (mentioning the `errorElement` prop) instead; restored and confirmed GREEN. A second test confirms the reload button calls `window.location.reload()` (stubbed via `Object.defineProperty(window, "location", ...)`, restored in `afterEach`).

- [x] **P3.S8.T4** Run the full web verification suite. **Result:** `npm run lint` clean; `npm run typecheck` (`tsc -b --noEmit`) clean; `npm test -- --run` 184 passed (177 baseline + 7 new: 3 for `resolveBuildId`, 2 for the receipt links, 2 for the error boundary; 42 files, up from 40 -- the 2 new files are the in-source `vite.config.ts` test and `AppErrorBoundary.test.tsx`); `npm run build` succeeded, and the built bundle (`dist/assets/index-*.js`) embeds `0.1.0+8f97273`, the exact current `git rev-parse --short HEAD` (T1's own verification, repeated here as part of the full suite). API was untouched by this slice (every change is under `web/`, `CLAUDE.md`, or this file); not re-run.

- [x] **P3.S8.T5** Work-unit commits: `:bug: fix(app): bust the persisted cache on every build` (T1), `:sparkles: feat(workorders): link the receipts from the order detail` (T2), `:goal_net: fix(app): show a spanish error screen instead of a crash` (T3; also records this slice in `tasks.md`).
