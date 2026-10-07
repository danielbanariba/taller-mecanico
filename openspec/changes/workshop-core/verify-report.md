# Verify report — workshop-core, Phase 1 (P1.S1–P1.S6)

Change: `workshop-core`. Scope: phase 1 only — capabilities `app-shell-navigation`, `customers`, `vehicles`. Branch `feat/workshop-core-customers`. Verified 2026-10-07.

## 1. Executed checks (real commands, this session)

| Command | Result |
|---|---|
| `docker compose up -d db` | Container already healthy (`taller-mecanico-db-1`) |
| `cd api && uv run ruff check .` | PASS — "All checks passed!" |
| `cd api && uv run ruff format --check .` | PASS — 72 files already formatted |
| `cd api && uv run pytest` | PASS — 139 passed, 1 warning (pre-existing httpx deprecation, unrelated) |
| `cd web && npm run lint` | PASS — eslint clean |
| `cd web && npm run typecheck` | PASS — `tsc -b --noEmit` clean |
| `cd web && npm test -- --run` | PASS — 25 files, 117 tests passed |
| `cd web && npm run build` | PASS — main chunk 416.00 kB / gzip 125.16 kB (matches figure already recorded in `tasks.md` P1.S6.T5) |

Migration round-trip was not re-executed this session; `tasks.md` P1.S6.T4 already records `upgrade → downgrade -1 → upgrade head` with no error, and `test_migrations.py` (`alembic check`) is part of the 139 passing pytest tests above — no drift currently exists.

Pytest count (139) is 3 higher than the 136 recorded at P1.S6.T5 time, consistent with the later commit `6acbdd7` ("reject explicit null on required patch fields") adding three new null-rejection tests. Vitest count (117) matches exactly.

## 2. Task completion (observed from `openspec/changes/workshop-core/tasks.md`, not rewritten)

All of P1.S1–P1.S6 are checked `[x]` except two explicitly deferred items, matching the orchestrator's stated expectation:
- `P1.S6.T6` (deploy to demo + re-run seed) — unchecked, deferred to the orchestrator after the PR.
- `P1.S6.T7` (real-browser check at 390×844) — unchecked, deferred to the orchestrator after the PR.

No other unfinished phase-1 tasks found. Diff vs `main`: 77 files changed, +9622/-46 — roughly 3x the ~3,300-line planning estimate in the forecast table (explicitly labeled "not an exact diff count" there), worth noting for future forecast calibration but not a defect.

## 3. Spec-scenario → test mapping

**Capability: app-shell-navigation**

| Scenario | Status | Test evidence |
|---|---|---|
| Shell renders on every protected screen | COVERED | `web/src/app/AppShell.test.tsx` |
| Unauthenticated user never sees the shell | SUGGESTION (structural, untested behaviorally) | Confirmed by reading `router.tsx`/`RequireSession.tsx`: `/login` is a sibling top-level route with no `AppShell` ancestor; `RequireSession` unmounts children via `<Navigate to="/login"/>`. Correct by construction, no dedicated test. |
| Navigating updates the active tab | COVERED, partially | `aria-current` asserted via direct route entry for both tabs, not a simulated tap-between-tabs click |
| Logout available from shell / ends session | COVERED | `AppShell.test.tsx` logout tests |
| Inventory no longer renders its own logout | COVERED | `AppShell.test.tsx` "exactly one logout control" |
| Órdenes placeholder, no request | COVERED | `AppShell.test.tsx` (MSW `onUnhandledFrame:"error"` would fail otherwise) |
| Existing inventory flows unaffected | COVERED | `InventoryPage.test.tsx` + full green inventory suite |
| Shell needs no network (offline tab switch) | COVERED | `AppShell.test.tsx` offline test |

**Capability: customers**

| Scenario | Status | Test evidence |
|---|---|---|
| Replay no-op / conflict on create | COVERED | `test_replaying_an_identical_create_is_a_no_op`, `test_replaying_an_id_with_a_different_payload_is_a_conflict` |
| Landline / mobile / empty / invalid phone | COVERED | `test_a_landline_phone_is_normalized_and_classified`, `test_editing_only_the_name_leaves_phone_unchanged` (mobile), `test_an_empty_phone_is_accepted_with_no_mobile_classification`, `test_a_7_digit_or_1_prefixed_phone_is_rejected`, plus domain unit tests |
| Edit name / nonexistent / foreign | COVERED | `test_editing_only_the_name_leaves_phone_unchanged`, `test_editing_a_nonexistent_customer_is_not_found`, `test_another_workshops_customer_cannot_be_mutated` |
| Archive active / idempotent / foreign | COVERED | `test_archiving_an_active_customer_hides_it_from_the_default_listing`, `test_archiving_twice_keeps_the_first_archived_at`, `test_another_workshops_customer_cannot_be_mutated` |
| Search by name / phone / plate (full, partial, archived-excluded) | COVERED | `test_search_is_accent_insensitive`, `test_search_matches_a_phone_fragment`, `test_customer_search_matches_a_full_normalized_plate`, `test_customer_search_matches_a_partial_plate`, `test_customer_search_does_not_match_an_archived_vehicles_plate` |
| Create disabled offline (web) | COVERED | `NewCustomerPage.test.tsx` |
| **Previously visited customer list renders offline (web)** | **WARNING — not covered** | `CustomersPage.test.tsx` contains exactly one test (accent-search). No cold/offline-cache test exists, unlike `VehicleDetailPage.test.tsx`'s equivalent. Same persisted-cache infra is reused, so risk is low, but untested. |
| Tenant isolation (customers) | COVERED | `test_another_workshops_customer_is_invisible`, `test_another_workshops_customer_cannot_be_mutated` |
| Client-id reuse on retry / Spanish error messages (web) | COVERED | `NewCustomerPage.test.tsx` |
| Workshop switch clears cached customer queries (web) | COVERED (inferred) | `workshopSwitch.test.tsx`'s `renderAppOnCustomers` helper exists specifically for this extension; full assertion body not re-read this pass |

**Capability: vehicles**

| Scenario | Status | Test evidence |
|---|---|---|
| Create for existing / nonexistent / foreign / archived customer | COVERED | `test_create_saves_the_vehicle_with_its_owner`, `test_create_with_a_nonexistent_customer_id_is_not_found`, `test_create_with_a_foreign_customer_id_is_not_found`, `test_create_with_an_archived_customer_id_is_not_found` |
| Owner never reassignable on edit | COVERED | `test_an_edit_cannot_reassign_the_vehicle_to_a_different_customer` |
| Cascade archive on customer archive / already-archived unaffected | COVERED | `test_archiving_a_customer_archives_its_active_vehicles_and_frees_their_plates`, `test_an_already_archived_vehicle_is_unaffected_by_the_customer_archive_cascade` |
| Create idempotent (replay / conflict) | COVERED | `test_replaying_an_identical_create_is_a_no_op`, `test_replaying_an_id_with_a_different_plate_is_a_conflict` |
| Plate normalized on save (create) | COVERED | `test_a_plate_is_normalized_on_save` + domain unit tests |
| Duplicate active plate rejected (create path) | COVERED | `test_a_duplicate_active_plate_in_the_same_workshop_is_rejected` |
| **Duplicate active plate rejected on edit** | **WARNING — not covered** | Spec text says "created or edited," but only the create path is tested via `PATCH` |
| **Plate normalization on the edit path** | **WARNING — not covered** | No `PATCH` test asserts normalized plate storage, unlike the dedicated create-path test |
| Unplated vehicles allowed / plate freed by archive / per-workshop uniqueness | COVERED | `test_several_unplated_vehicles_are_always_allowed`, `test_archiving_a_vehicle_frees_its_plate_for_reuse`, `test_a_plate_unique_to_one_workshop_does_not_block_another` |
| Edit/detail for nonexistent or foreign vehicle | COVERED (foreign) / SUGGESTION (nonexistent) | `test_another_workshops_vehicle_cannot_be_mutated`, `test_another_workshops_vehicle_is_invisible`; a truly nonexistent id is not separately exercised |
| Archive active / idempotent | COVERED | `test_archiving_a_vehicle_frees_its_plate_for_reuse`, `test_archiving_twice_keeps_the_first_archived_at` |
| List customer's vehicles (active-only default) | COVERED | `test_listing_a_customers_vehicles_without_include_archived_returns_only_active` |
| Create disabled offline / cached detail renders offline (web) | COVERED | `NewVehiclePage.test.tsx`, `VehicleDetailPage.test.tsx` |
| Tenant isolation (vehicles) | COVERED | `test_another_workshops_vehicle_is_invisible`, `test_another_workshops_vehicle_cannot_be_mutated`, `test_workshop_b_creating_a_vehicle_under_workshop_as_customer_is_not_found` |
| `CustomerDetailPage` lists vehicles (web) | COVERED | `CustomerDetailPage.test.tsx` |

## 4. Findings summary

- **CRITICAL: 0**
- **WARNING: 3** — no offline-cache regression test for the customer list; no API test proves plate normalization on vehicle `PATCH`; no API test proves duplicate-plate rejection on vehicle `PATCH` (spec text covers both create and edit, only create is tested).
- **SUGGESTION: 3** — "no shell at `/login`" is structurally guaranteed (confirmed by reading `router.tsx`/`RequireSession.tsx`) but untested behaviorally; tab-tap navigation only indirectly exercised; nonexistent-vs-foreign vehicle id distinction untested on edit/detail (shared low-risk code path).
- All real commands pass: ruff check/format, pytest (139), eslint, tsc, vitest (117), vite build.
- `P1.S6.T6`/`P1.S6.T7` deferred per explicit orchestrator instruction — not a verification failure.

## 5. Recommendation

Phase 1 is functionally complete; every automated check is green. The 3 WARNING gaps are narrow (vehicle-edit plate path, customer-list-offline path) and do not block archiving. Recommend `sdd-archive` for phase 1, optionally filing a follow-up task to add the three missing regression tests before phase 2's heavier work-order code lands.


## 6. Resolution after verify

- Review (two read-only lenses over the phase diff) found two major defects: an explicit `null` on a required PATCH field (`full_name`, `make`, `vehicle_type`) crashed with a 500. Fixed in `6acbdd7` with schema-level validators and three regression tests, each confirmed RED first.
- Review minor: a customer archive and a concurrent vehicle create could interleave and leave an active vehicle under an archived customer. Fixed in `2067190` by locking the customer row (`get_for_update`) in both paths.
- Review minor: every protected screen rendered two `<h1>` (shell plus page). Fixed in `b9d040b`; the workshop name in the shell is no longer a heading.
- Verify WARNINGs on vehicle PATCH plate normalization and duplicate-plate rejection: both behaviors were already correct (coverage-only gaps); regression tests added in `2067190`.
- Still open: no dedicated test for the customer list rendering offline from the persisted cache. Accepted as low risk, since it reuses the same persisted-cache path the inventory and vehicle-detail tests already exercise.
- Checks after the fixes: pytest 141 passed; ruff check and format clean; eslint, tsc and vitest (117) clean.
- Real-browser check on the demo (390×844) found a layout defect the suites could not see: detail and form screens kept their old full-page `<main>` wrapper and rendered as a narrow centered strip inside the shell. Fixed in `1232af0`, re-checked on the demo (one `<main>`, one `<h1>`, full width). Phones now display as `3000-0002` (`92e525b`).
- Web suite after the browser fixes: 119 passed. `ItemDetailPage offline > shows how many changes are waiting to be sent` failed once in four full runs and passed in isolation and on three reruns. It is timing-sensitive, in code this phase did not change.

---

# Verify report — workshop-core, Phase 2 (P2.S1–P2.S7)

Change: `workshop-core`. Scope: phase 2 only — capabilities `work-orders`, `work-order-stock-consumption`, `whatsapp-sharing`. Branch `feat/workshop-core-work-orders`. Verified 2026-10-07.

## 1. Executed checks (real commands, this session)

| Command | Result |
|---|---|
| `docker compose up -d db` | Container already running (`taller-mecanico-db-1`) |
| `cd api && uv run ruff check .` | PASS — "All checks passed!" |
| `cd api && uv run ruff format --check .` | PASS — 94 files already formatted |
| `cd api && uv run pytest` | PASS — 191 passed, 1 pre-existing unrelated warning (httpx deprecation) |
| `cd web && npm run lint` | PASS — eslint clean |
| `cd web && npm run typecheck` | PASS — `tsc -b --noEmit` clean |
| `cd web && npm test -- --run` | PASS — 33 files, 143 tests passed |
| `cd web && npm run build` | PASS — main chunk 440.43 kB / gzip 130.71 kB, PWA precache generated |

All counts match the figures already recorded in `openspec/changes/workshop-core/tasks.md` (P2.S8.T4). Migration round-trip not re-executed this session — `test_migrations.py` (`alembic check`) passed as part of the pytest run above, and `tasks.md` P2.S7.T6 already recorded a clean `upgrade → downgrade -1 → upgrade head` round-trip for revision `8db9fb7d17ef`.

Diff vs `main` (merge-base `17a1b54`, the phase-1 merge commit — confirms this diff is phase-2-only): 77 files changed, +7490/-225. All 11 expected work-unit commits are present on the branch (`9f1a3ba` through `f842fc7`), matching every commit named in `tasks.md`.

## 2. Task completion (observed from `tasks.md`, not rewritten)

P2.S1 through P2.S6 and P2.S8 are fully checked `[x]`. P2.S7 is checked except two items, matching the orchestrator's stated expectation:
- `P2.S7.T8` (deploy phase 2 to the demo, re-run seed) — unchecked, deferred to the orchestrator after the PR.
- `P2.S7.T9` (real-browser check at 390×844 + Android Chrome photo-sharing check) — unchecked, deferred to the orchestrator after the PR.

P2.S8 (review-fix slice) is fully checked and its two fixes were spot-verified directly in source this session:
- `update_work_order` now calls `order_repo.get_for_update` (row-locked), not `get_by_id` — confirmed in `api/src/taller/workorders/application/use_cases.py`.
- `web/src/features/workorders/copy.ts` maps `work_order_create_failed` to its own Spanish message.

No other unfinished phase-2 tasks found.

## 3. Spec-scenario → test mapping

**Capability: work-orders**

| Scenario | Status | Test evidence |
|---|---|---|
| Creating an order for an existing vehicle | COVERED | `test_work_orders_api.py` |
| Creating for a nonexistent/foreign vehicle (404) | COVERED | `test_work_orders_api.py` |
| Sequential numbering within a workshop | COVERED | `test_work_orders_api.py` |
| Concurrent creates never assign the same number | COVERED | `test_work_order_concurrency.py` (re-run 5×, no flake per tasks.md) |
| Replaying an identical create (no second number) | COVERED | `test_work_orders_api.py` |
| Reusing an order id with a different payload (409) | COVERED | `test_work_orders_api.py` |
| Adding labor / inventory-part / external-part lines | COVERED | `test_work_order_lines_api.py` |
| Inventory-part line referencing nonexistent/foreign item (404) | COVERED | `test_work_order_lines_api.py` |
| Total reflects all three line kinds | COVERED | `test_work_order_lines_api.py` |
| Disallowed transition rejected (409) | COVERED | `test_stock_consumption.py` |
| Exactly one transition consumes stock | COVERED | `test_stock_consumption.py` |
| Cancelling after consumption reverses it | COVERED | `test_stock_consumption.py` |
| `completed`/`delivered` cannot be cancelled | COVERED | `test_stock_consumption.py` |
| Repeating a transition is a no-op | COVERED | `test_stock_consumption.py` |
| Editing lines in `completed` is allowed | COVERED | `test_stock_consumption.py::test_line_edits_are_locked_in_delivered_and_cancelled_but_allowed_in_completed` |
| Editing a delivered/cancelled order's **lines** rejected (409) | COVERED | same test above (PATCH line + DELETE line both asserted) |
| **Editing the order's own fields (`PATCH`) once delivered is rejected** | **WARNING — not covered** | `update_work_order` raises `WorkOrderLocked` when `order.status not in EDITABLE` (verified in source), but no test sends `PATCH /work-orders/{id}` against a delivered/cancelled order — only tenant-isolation and happy-path PATCH are tested |
| Replaying an identical line add is a no-op | COVERED | `test_work_order_lines_api.py` |
| Reusing a line id with a different payload (409) | COVERED | `test_work_order_lines_api.py` |
| Editing/removing a line not on the order (404) | COVERED | `test_work_order_lines_api.py` |
| Status transition disabled while offline | COVERED | `StatusActions.test.tsx` |
| **Line add/edit disabled while offline** | **WARNING — not covered** | `LineEditorDialog.tsx` wires `offline` into its submit-disable guard and renders the Spanish alert, but `LineEditorDialog.test.tsx` only renders with `offline={false}` — the offline branch is never exercised |
| A previously visited order detail renders offline | COVERED | `WorkOrderDetailPage.test.tsx` |
| Vehicle history shows its orders, most recent first | COVERED | `VehicleDetailPage.test.tsx` |
| Customer detail shows its work orders (across vehicles) | SUGGESTION — implemented, untested | `CustomerDetailPage.tsx` wires `useWorkOrdersForCustomer` and renders an "Órdenes" section, but `CustomerDetailPage.test.tsx` has exactly one test (vehicles list) with no assertion on the orders section — same gap shape phase 1's report flagged for `CustomersPage.test.tsx` |
| Another workshop's order is invisible / cannot be mutated (404) | COVERED | `test_work_orders_api.py`, `test_stock_consumption.py::test_workshop_b_cannot_change_status_or_edit_lines_on_workshop_as_order` |

**Capability: work-order-stock-consumption**

| Scenario | Status | Test evidence |
|---|---|---|
| Entering `in_progress` posts movements for every inventory-part line | COVERED | `test_stock_consumption.py` |
| Negative stock is flagged, never blocked | COVERED | `test_stock_consumption.py` |
| Increasing/decreasing quantity after consumption posts the delta | COVERED | `test_stock_consumption.py` |
| Cancelling after/before consumption reverses/skips reversal | COVERED | `test_stock_consumption.py` |
| Revision increments once per posting event | COVERED | `test_reconciliation_plan.py` + `stock.py` (`movement_id_for`, read directly in source) |
| Retrying consumption/edit/cancellation does not double-apply | COVERED | `test_stock_consumption.py` |
| Order-caused movement linked / manual movement unlinked | COVERED | `test_movement_order_link.py` |
| Existing idempotency preserved for non-order movements | COVERED | `test_movement_order_link.py::test_unlinked_movement_replay_is_unaffected_by_the_link_fields` |
| A failure during movement posting rolls back the status change | COVERED | `test_stock_consumption.py` (monkeypatched `record_movement` failure) |
| Concurrent overlapping-item transitions don't deadlock | COVERED | `test_work_order_concurrency.py` (re-run 5×, no flake) |

**Capability: whatsapp-sharing**

| Scenario | Status | Test evidence |
|---|---|---|
| Mobile/landline/phoneless visibility of the share action | COVERED | `ShareWhatsAppButton.test.tsx`, `WorkOrderDetailPage.test.tsx` |
| Triggering opens a `wa.me` link with the order's data | COVERED | `whatsapp.test.ts`, `ShareWhatsAppButton.test.tsx` |
| Photo sharing on a supporting browser invokes Web Share with files+summary | COVERED | `ShareWhatsAppButton.test.tsx` |
| Fallback on a non-supporting browser (text-only link, no picker) | COVERED | `ShareWhatsAppButton.test.tsx`, `whatsapp.test.ts::supportsFileShare` |
| No network request carries the photo / no IndexedDB retains it | SUGGESTION — correct by construction, untested | `ShareSheet.tsx` keeps picked `File`s only in local `useState`, with no `fetch`/API call and no IndexedDB/outbox/query-cache write anywhere in the share flow — confirmed by reading the full component — but no test asserts the absence of a network call or persisted storage |

## 4. Additional structural check

`GET /work-orders` accepts `vehicle_id`/`customer_id` query filters (used by `useWorkOrdersForVehicle`/`useWorkOrdersForCustomer`), and `SqlAlchemyWorkOrderRepository.list` applies them correctly scoped by `workshop_id` first (confirmed directly in source). No API-level test exercises `GET /work-orders?vehicle_id=`/`?customer_id=` directly — the only coverage is indirect, through MSW-mocked web tests that never reach the real backend filter. **WARNING** — correct by code reading, not verified end-to-end against a real database.

## 5. Findings summary

- **CRITICAL: 0**
- **WARNING: 3**
  1. `PATCH /work-orders/{id}` on a `delivered`/`cancelled` order has no test asserting the spec's named `work_order_locked` scenario (implementation present, verified in source).
  2. Line add/edit's offline-disable branch (`LineEditorDialog`) is wired but never exercised with `offline={true}`.
  3. The `vehicle_id`/`customer_id` list-filter capability backing vehicle/customer order history has no direct API-level test; only MSW-mocked web tests touch it indirectly.
- **SUGGESTION: 2**
  1. `CustomerDetailPage.test.tsx` has no assertion on the new "Órdenes" section (mirrors a phase-1 report finding of the same shape).
  2. "Photos never uploaded/stored" (whatsapp-sharing spec) is true by construction but has no dedicated negative-assertion test.

Expected/accepted pending items (not findings): `P2.S7.T8` (demo deploy) and `P2.S7.T9` (real-browser + Android check) are explicitly deferred to the orchestrator after the PR, per the task's own instructions — this does not block archive.

All full checks (API ruff/format/pytest; web lint/typecheck/test/build) pass. No regressions. No CRITICAL defects. The 3 WARNING and 2 SUGGESTION findings above are coverage gaps on correctly-implemented code paths, not functional defects.


## 6. Resolution after verify (phase 2)

- Review critical: `update_work_order` read the order without a lock and saved the full row, so it could revert a concurrent status change, line edit or stock reversal. Fixed in `b25c3d0` (`get_for_update`), with a deterministic concurrency test confirmed RED first.
- Review critical, refuted: "`CustomerDetailPage`'s unmocked orders request breaks its test" was false at the time. MSW 3's `onUnhandledFrame: "error"` covers HTTP and WebSocket, but only logs and fails the request; it never fails the test. `2edd179` now fails any test that makes an unmocked request (`request:unhandled` checked in `afterEach`). That exposed 14 tests in 5 files with missing mocks, all fixed. CLAUDE.md and P2.S8.T2 are corrected.
- Review minor: `work_order_create_failed` had no Spanish message. Fixed in `f842fc7`.
- Verify WARNINGs:
  - The locked header on `delivered`/`cancelled` and the `vehicle_id`/`customer_id` list filters were both already correct; regression tests were added in `6759566`.
  - The line editor's offline-disable path through its real container: also correct, test added in `7d2907b`.
- Real-browser check: "Cancelar orden" was a one-tap irreversible action shown first, because `allowed_transitions` is sorted alphabetically. Fixed in `b94f6d8`: forward actions come first, and cancel opens a confirmation dialog. Re-checked on the demo.
- Still open: the Android Chrome photo-sharing check (P2.S7.T9b) needs a real device.
- Checks after the fixes: pytest 195 passed; ruff check and format clean; eslint, tsc, vitest (146, stable across repeated runs) and build clean.
