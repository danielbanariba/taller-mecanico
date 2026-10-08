# Tasks: SAR invoicing (opt-in Factura and Nota de Crédito from work orders)

Change: `sar-invoicing` · Inputs: `proposal.md` (approved 2026-10-08), the eight capability specs under `specs/`, `design.md` (including "Sequencing inside each phase", "Resolved Questions" and "Spec reconciliation"). Slice order below follows `design.md`'s own sequencing exactly — no deviation was required. Task IDs are `P<phase>.S<n>.T<m>`, where `<phase>` is `A` or `B` per the proposal/design phase names. Each task carries a `[inline]`/`[delegated]` route tag.

**Name confirmations.** Design flags five groups of unconfirmed identifiers (seven individual names) it could not read this session. Each is confirmed as the first task of the first slice that uses it: `PA.S1.T1` (test schema build method), `PA.S3.T1` (the `Clock` protocol module and `daily_cash_summary`'s `ZoneInfo`), `PA.S5.T1` (`order_total_cents` and `WorkOrderRepository.get_for_update`), `PA.S6.T1` (`WorkOrderOut.lines_editable`'s line and the router's `_to_out` signature), `PA.S7.T1` (`web/src/test/handlers.ts`'s content), `PA.S11.T1` (the receipt's measured-height code), `PB.S3.T1` (`export/adapters/sources.py`'s function shape).

## Delivery Strategy

**Single PR per phase**, as approved (proposal A13, and the `workshop-core` precedent "un PR por fase"). Each slice below is one work-unit commit (Gitmoji + Conventional Commits) on the phase's branch; the branch already checked out for phase A is `feat/sar-invoicing`. Phase B starts only after phase A is merged and deployed to the demo, and the user approves starting phase B.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | Phase A ≈ **4,800–5,600** (API ~2,600 incl. ~1,200 tests; Web ~2,400 incl. ~900 tests; seed/docs ~120); Phase B ≈ **2,500–3,000** (API ~1,300 incl. ~600 tests; Web ~1,300 incl. ~500 tests; seed/docs ~60) — per `proposal.md`'s Size Forecast |
| 400-line budget risk | **High** for both phases (each is ~6–14× the 400-line budget) |
| Chained PRs recommended | **No** — overridden by the already-approved delivery decision below |
| Suggested split | None: one PR per phase, internally chained into the slices below as sequential commits (not separate PRs) |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

**Override note.** The 400-line guard would normally recommend chained/stacked PRs for a High-risk forecast. That recommendation is superseded here: the proposal (A13) and the project's own `workshop-core` precedent already settled on one PR per phase with an accepted size exception, specifically to keep each phase's fiscal behavior reviewable as one coherent, atomically revertible unit (per the Rollback Plan). `sdd-apply` must still record the exception explicitly before starting each phase's first slice.

```text
Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High
```

### Per-slice line estimate (planning estimate, not an exact diff count)

| Phase | Slice | Goal | Est. lines | Risk |
|---|---|---|---|---|
| A | S1 | API: migration (all tables, triggers, guarded downgrade), invoicing models, customer RTN/billing end-to-end, immutability tests | ~500 | High |
| A | S2 | API: pure invoicing domain (number, tax split, words, buyer rules, range selection) + unit/property tests | ~500 | High |
| A | S3 | API: fiscal profile + `GET /invoicing/settings` readiness, `shared/timezone.py`, code lock + tests | ~400 | High |
| A | S4 | API: CAI range create/`PATCH` (overlap, immutability, deadline bounds, profile mutex) + tests | ~400 | High |
| A | S5 | API: `issue_invoice`, issuance route and reads + tests | ~450 | High |
| A | S6 | API: `workorders` invoiced-order lock + numbering/lock-race concurrency + invariant test | ~400 | High |
| A | S7 | Web: customer billing name/RTN in the form and detail + tests | ~350 | High |
| A | S8 | Web: invoicing `api.ts`/`hooks.ts`/`copy.ts`/routes; "Más" entry; settings page + tests | ~550 | High |
| A | S9 | Web: profile form and range forms + tests | ~450 | High |
| A | S10 | Web: `InvoiceSection`, `IssueInvoiceDialog`, `InvoiceDetailPage`, lock message + tests | ~500 | High |
| A | S11 | Web: print primitives, `InvoiceDocument`, both print pages, copies, demo band + tests | ~550 | High |
| A | S12 | Closing: seed, docs, migration/downgrade drill, real-browser and print check | ~120 | Medium |
| **A total** | | | **~5,170** | **High** |
| B | S1 | API: phase B migration, credit-note domain/use case/routes, `mark_credited`, lock release, `06` readiness + tests incl. credit concurrency | ~550 | High |
| B | S2 | API: `range_warnings` and settings output + boundary tests | ~300 | High |
| B | S3 | API: three fiscal CSVs + customer columns + export tests | ~450 | High |
| B | S4 | Web: credit note dialog, detail, documents list + tests | ~500 | High |
| B | S5 | Web: `CreditNoteDocument` and both print pages + tests | ~450 | High |
| B | S6 | Web: warnings on settings page and dialogs + tests | ~350 | High |
| B | S7 | Closing: seed (`06` range, credit note, re-issued Factura), docs, downgrade drill, real-browser and print check | ~60 | Medium |
| **B total** | | | **~2,660** | **High** |

### Suggested Work Units

Each row is one work-unit commit inside its phase's single PR (no separate PR per slice).

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| PA.S1 | Fiscal schema + customer billing | Phase A PR | `uv run pytest tests/invoicing/test_fiscal_immutability.py tests/customers/test_customer_rtn.py` | N/A — API-only | Migration `downgrade()` (guarded, AD-20); revert customer domain/schema edits |
| PA.S2 | Pure invoicing domain | Phase A PR | `uv run pytest tests/invoicing/test_tax_split.py tests/invoicing/test_amount_in_words.py tests/invoicing/test_document_number.py tests/invoicing/test_range_selection.py tests/invoicing/test_buyer_rules.py` | N/A | Revert `invoicing/domain/` files; no schema/route depends on them yet |
| PA.S3 | Fiscal profile + settings readiness | Phase A PR | `uv run pytest tests/invoicing/test_profile_api.py` | N/A | Revert profile use case/router; models stay (used later) |
| PA.S4 | CAI range create/`PATCH` | Phase A PR | `uv run pytest tests/invoicing/test_cai_ranges_api.py` | N/A | Revert range use case/router |
| PA.S5 | `issue_invoice` | Phase A PR | `uv run pytest tests/invoicing/test_issue_invoice_api.py` | N/A | Revert issuance use case/router |
| PA.S6 | `workorders` invoiced lock | Phase A PR | `uv run pytest tests/workorders/test_invoiced_lock.py tests/invoicing/test_invoice_concurrency.py` | N/A | Revert `active_invoice`/lock call sites; `workorders` behaves as before |
| PA.S7 | Web: customer billing | Phase A PR | `npm test -- --run src/features/customers` | Manual: edit a customer's billing name/RTN at 390×844 | Revert `CustomerForm.tsx`/`CustomerDetailPage.tsx` edits |
| PA.S8 | Web: settings page | Phase A PR | `npm test -- --run src/features/invoicing/settings` | Manual: open "Más → Facturación" with no profile | Remove `invoicing/` web feature folder and its shell entry |
| PA.S9 | Web: profile/range forms | Phase A PR | `npm test -- --run src/features/invoicing/settings` | Manual: save a profile and register a range | Remove the two form components and sub-routes |
| PA.S10 | Web: issuance flow | Phase A PR | `npm test -- --run src/features/invoicing/issue src/features/invoicing/documents` | Manual: issue a Factura from an order at 390×844 | Remove issuance dialog/section/detail components |
| PA.S11 | Web: print | Phase A PR | `npm test -- --run src/features/invoicing/print` | Manual: print preview both layouts at 390×844 | Remove print routes/components |
| PA.S12 | Phase A close | Phase A PR | full phase verification (below) | Real-browser check at 390×844 on demo | Revert seed/docs; schema rollback per AD-20 |
| PB.S1 | Credit notes core | Phase B PR | `uv run pytest tests/invoicing/test_credit_notes_api.py tests/invoicing/test_credit_note_concurrency.py` | N/A | Migration `downgrade()` (guarded, AD-20) |
| PB.S2 | Range warnings | Phase B PR | `uv run pytest tests/invoicing/test_range_warnings.py` | N/A | Revert `range_warnings` wiring |
| PB.S3 | Export | Phase B PR | `uv run pytest tests/export/` | N/A | Revert the three new export sources/file-dict entries |
| PB.S4 | Web: credit note flow | Phase B PR | `npm test -- --run src/features/invoicing/documents` | Manual: issue a credit note at 390×844 | Remove credit-note dialog/detail components |
| PB.S5 | Web: credit note print | Phase B PR | `npm test -- --run src/features/invoicing/print` | Manual: print preview the credit note | Remove credit-note print components |
| PB.S6 | Web: warnings | Phase B PR | `npm test -- --run src/features/invoicing/settings` | Manual: see a warning on the settings page | Remove `RangeWarnings.tsx` and its call sites |
| PB.S7 | Phase B close | Phase B PR | full phase verification (below) | Real-browser check at 390×844 on demo | Revert seed/docs; schema rollback per AD-20 |

---

## Phase A: fiscal profile, CAI ranges, buyer RTN, Factura issuance, print and order lock

### Slice PA.S1 — API: migration (all tables, triggers, guarded downgrade), invoicing ORM models, customer RTN/billing end-to-end, immutability + customer tests

- [x] **PA.S1.T1** [inline] Confirm whether `api/tests/conftest.py` builds the test schema through Alembic or `metadata.create_all` (design, "Not readable in this session"). This decides whether the AD-10 trigger DDL must be attached via `event.listen(table, "after_create", DDL(...))` in the models module (if `create_all`) or reaches tests automatically through the migration (if Alembic). Record the confirmed mechanism; it gates `PA.S1.T17`.
  - **Confirmed:** `api/tests/conftest.py`'s session-scoped `test_engine` fixture runs `alembic.command.upgrade(alembic_cfg, "head")` against the test database (not `metadata.create_all`). The AD-10 trigger DDL in the migration therefore reaches tests automatically; `PA.S1.T15` needs no `event.listen` hook.
- [x] **PA.S1.T2** [inline] Create the invoicing package skeleton: `api/src/taller/invoicing/__init__.py`, `domain/__init__.py`, `application/__init__.py`, `adapters/__init__.py`.
- [x] **PA.S1.T3** [inline] Create `api/src/taller/customers/domain/rtn.py`: `Rtn.from_raw(raw)` strips spaces and `-`, requires exactly 14 digits, else raises `InvalidRtn`. Modify `api/src/taller/customers/domain/errors.py`: add `InvalidRtn`.
- [x] **PA.S1.T4 (RED)** [delegated] Write `api/tests/customers/test_customer_rtn.py`: `Rtn.from_raw("0801-1990-123456") == "08011990123456"`; 13 and 15 digit variants raise `InvalidRtn`. **Defect it catches:** a malformed RTN reaches a fiscal document (`customers` delta, "An RTN with the wrong digit count is rejected").
- [x] **PA.S1.T5 (GREEN)** [inline] Confirm T4 passes against T3's implementation.
- [x] **PA.S1.T6** [inline] Modify `api/src/taller/customers/domain/entities.py`: add `billing_name`, `rtn` to `Customer`.
- [x] **PA.S1.T7** [delegated] Modify `api/src/taller/customers/application/use_cases.py`: include `billing_name`/`rtn` in the create-replay comparison (`{full_name, phone, notes, billing_name, rtn}`); `PATCH` accepts an explicit `null` to clear either field.
- [x] **PA.S1.T8** [delegated] Modify `api/src/taller/customers/adapters/{models,schemas,router}.py`: `billing_name varchar(200) NULL`, `rtn varchar(14) NULL` with `ck_customers_rtn_digits`; `CustomerOut`/`CustomerCreateRequest`/`CustomerUpdateRequest` gain both fields; map `InvalidRtn` → 422 `invalid_rtn`.
- [x] **PA.S1.T9 (RED)** [delegated] Extend `api/tests/customers/test_customers_api.py`: an RTN with separators is normalized and stored (`customers` delta, "An RTN with separators is accepted and normalized"); a 13/15-digit RTN gives 422 `invalid_rtn` ("An RTN with the wrong digit count is rejected"); billing name and RTN are both optional ("Billing name and RTN are both optional"); both are editable independently of phone, name and mobile/landline flag ("Billing name and RTN are editable independently of phone"); a create replay reusing an id with a different RTN gives 409 `customer_id_conflict`, original unchanged ("Billing name and RTN participate in create idempotency like any other field"). **Defects it catches:** a malformed RTN reaches an invoice; a retry silently overwrites billing data; a partial update clobbers an omitted field.
- [x] **PA.S1.T10 (GREEN)** [inline] Run T9, confirm green against T6–T8.
- [x] **PA.S1.T11** [delegated] Create `api/migrations/versions/<rev>_fiscal_invoicing.py`: the customer columns and check; `fiscal_profiles`; `cai_ranges`; `fiscal_invoices`; `fiscal_invoice_lines`; the `taller_fiscal_invoice_guard` and `taller_fiscal_append_only` trigger functions and their triggers; a guarded `downgrade()` (AD-20: `SELECT EXISTS (SELECT 1 FROM fiscal_invoices)`, raise unless `-x discard_fiscal_documents=demo`). Schema exactly per `design.md`'s "Data model per phase → Phase A". **Done as** `api/migrations/versions/db3dfe52854a_add_fiscal_invoicing_schema.py` (revises `ffb1eb564de6`, the prior head).
- [x] **PA.S1.T12** [inline] Modify `api/migrations/env.py`: add `import taller.invoicing.adapters.models` alongside the existing feature imports (per T1's confirmed registration idiom).
- [x] **PA.S1.T13** [delegated] Create `api/src/taller/invoicing/adapters/models.py`: `FiscalProfileModel`, `CaiRangeModel`, `FiscalInvoiceModel`, `FiscalInvoiceLineModel` with every index from T11 declared on the models (including `uq_fiscal_invoices_order_active` with `postgresql_where`, so `alembic check` sees it), plus the shared snapshot dataclasses/mixin (`IssuerSnapshot`, `CaiSnapshot`, `Amounts`) per AD-10.
- [x] **PA.S1.T14 (RED)** [delegated] Write `api/tests/invoicing/test_fiscal_immutability.py`: a raw `UPDATE fiscal_invoices SET total_cents = ...` raises; a raw `DELETE` raises; `UPDATE ... SET credited_at = now()` from `NULL` succeeds once and fails the second time. **Defect it catches:** an application bug or ad-hoc script rewrites or deletes a legal document (AD-10; Art. 5, 41, 43).
  - **Note:** the "fails the second time" assertion binds two distinct Python timestamps as parameters rather than SQL `now()`, which is frozen to the start of the enclosing (SAVEPOINT-joined) Postgres transaction for the whole test and would make the second `UPDATE` an undetectable no-op.
- [x] **PA.S1.T15 (GREEN)** [inline] If T1 found the test schema built via `metadata.create_all`, attach the trigger DDL with `event.listen(table, "after_create", DDL(...))` in `adapters/models.py`; otherwise no extra step. Run T14, confirm green.
  - T1 confirmed Alembic; no extra step taken. T14 is green (see verification below).
- [x] **PA.S1.T16** [inline] Run this slice's verification: `docker compose up -d db`; `cd api && uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- [x] **PA.S1.T17** [inline] Work-unit commit on `feat/sar-invoicing`: `:sparkles: feat(invoicing): add the fiscal invoicing schema, triggers and customer billing fields`.

### Slice PA.S2 — API: pure invoicing domain (number, tax split, words, buyer rules, range selection) + unit/property tests

- [x] **PA.S2.T1 (RED)** [delegated] Write `api/tests/invoicing/test_document_number.py`: `DocumentNumber(establishment="001", emission_point="001", document_type=DocumentType.INVOICE, correlative=1)` stringifies to `001-001-01-00000001`; `correlative=99999999` keeps 8 digits; an out-of-bounds correlative raises. **Defect it catches:** an unpadded or misordered number printed on a legal document (`fiscal-invoices`, "A number is assembled from the profile and the allocated correlative").
  - **Name confirmation:** `DocumentType` uses lowercase members (`invoice = "01"`, `credit_note = "06"`), not design's illustrative uppercase `INVOICE`/`CREDIT_NOTE` — matching this codebase's existing `StrEnum` convention (`LineKind`, `PaymentMethod`, `WorkOrderStatus`, all lowercase). Confirmed this is the right call because the same Interfaces/Contracts block also writes `WorkOrderStatus.COMPLETED`/`.DELIVERED`, which do not exist in the real enum (lowercase `completed`/`delivered`) — proving that block's casing is illustrative, not literal.
- [x] **PA.S2.T2 (GREEN)** [inline] Create `api/src/taller/invoicing/domain/document_number.py` (`DocumentType`, `DocumentNumber`). Run T1, confirm green.
- [x] **PA.S2.T3 (RED)** [delegated] Write `api/tests/invoicing/test_tax_split.py`: for every `T` in 0..200,000 and 10,000 random large values, `taxable + isv == T`; `T = 100000` gives exactly `86957`/`13043`; `T = 115000` gives `100000`/`15000`. **Defect it catches:** float division; ISV computed forward as 15% of the base (one cent over the total at `T = 100000`); wrong rounding direction (`fiscal-invoices`, "A clean total splits exactly" / "Gravado plus ISV always equals the total, whatever the rounding rule").
- [x] **PA.S2.T4 (GREEN)** [inline] Create `api/src/taller/invoicing/domain/tax.py` (`Amounts`, `split_tax_inclusive_total`) per AD-8's formula. Run T3, confirm green.
- [x] **PA.S2.T5 (RED)** [delegated] Write `api/tests/invoicing/test_amount_in_words.py`: the AD-9 example table (0.50, 1, 16, 21, 31, 100, 101, 115, 500, 700, 999, 1,000, 1,150, 21,000, 101,000, 1,000,000, 2,021,001.50, the maximum); above the maximum raises. **Defect it catches:** missing apocope; `CIENTO` mishandled for exactly 100; singular `LEMPIRA` dropped; missing `DE` after an exact million; accents lost; overflow returns garbage.
  - **Resolved the apparent 3-group vs. 12-digit inconsistency:** AD-9 describes 3 groups ("millions, thousands, units", each 0-999, max 999,999,999) but the Bound says "valid up to 999,999,999,999" (12 digits). Resolved by applying the thousands-and-units grouping twice — once to the millions multiplier itself (0..999,999), once to the remainder below a million — which reaches exactly `MAX_LEMPIRAS = 999_999_999_999` with no new word and matches every worked example in AD-9 and the Interfaces/Contracts block verbatim.
- [x] **PA.S2.T6 (GREEN)** [inline] Create `api/src/taller/invoicing/domain/amount_in_words.py`. Run T5, confirm green.
- [x] **PA.S2.T7 (RED)** [delegated] Write `api/tests/invoicing/test_buyer_rules.py`: no name/no RTN → "CONSUMIDOR FINAL"; name alone → named consumidor final; name + RTN → identified; RTN alone raises `BuyerNameRequired`; `999999` cents with no identification is allowed, `1000000` cents without RTN or name raises `BuyerIdentificationRequired`. **Defect it catches:** the L 10,000 boundary is off by one, or an RTN prints without a name (`fiscal-invoices`, threshold scenarios).
- [x] **PA.S2.T8 (GREEN)** [inline] Create `api/src/taller/invoicing/domain/buyer.py` and extend `domain/errors.py` with `BuyerNameRequired`, `BuyerIdentificationRequired`. Run T7, confirm green.
- [x] **PA.S2.T9 (RED)** [delegated] Write `api/tests/invoicing/test_range_selection.py`: `select_range` picks the earlier fecha límite over a lower `range_start`; the fecha límite day itself is usable, the next day is not; an exhausted current range falls through to a standby one; missing/expired/exhausted follow the AD-6 rule (`cai_range_missing` if no range at all, else `cai_range_expired` if any range still has numbers, else `cai_range_exhausted`); `overlaps()` treats adjacent ranges (1–500, 501–1000) as non-overlapping, intersecting ones as overlapping, and different types/codes as never colliding. **Defect it catches:** the wrong range is used, wasting a current range's numbers; an off-by-one on Art. 62; a false "exhausted" with a standby range registered; valid consecutive ranges rejected or duplicate numbers made possible.
- [x] **PA.S2.T10 (GREEN)** [delegated] Create `api/src/taller/invoicing/domain/ranges.py` (`CaiRange`, `RangeState`, `select_range`, `range_states`, `overlaps`, plus `remaining`/`in_use`/`usable_on` on `CaiRange`) and extend `domain/errors.py` with `CaiRangeMissing`, `CaiRangeExpired`, `CaiRangeExhausted`. Run T9, confirm green.
  - **Name confirmation:** `overlaps(candidate, others)` (one range against a sequence) per the Interfaces/Contracts block's literal signature, not a pairwise `overlaps(a, b)` — and it compares `establishment_code`/`emission_point_code` too (not just `document_type`), matching AD-4's "of the same workshop, document type, establecimiento and punto de emisión" and the Testing Strategy's "other codes or types never collide".
- [x] **PA.S2.T11** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/invoicing/`.
  - **Result:** `ruff check` clean, `ruff format --check` clean (125 files), `pytest tests/invoicing/` 52 passed; full `uv run pytest` 297 passed.
- [x] **PA.S2.T12** [inline] Work-unit commit: `:sparkles: feat(invoicing): add the pure invoicing domain (numbering, tax split, words, buyer rules, ranges)`.

### Slice PA.S3 — API: fiscal profile + `GET /invoicing/settings` readiness, `shared/timezone.py`, code lock + tests

- [ ] **PA.S3.T1** [inline] Confirm the module that defines the `Clock` protocol (imported via `get_clock`) and where `daily_cash_summary` keeps its `ZoneInfo("America/Tegucigalpa")` (design, "Not readable in this session"). Record the confirmed import path; it gates every invoicing use case that needs the current date.
- [ ] **PA.S3.T2** [inline] Create `api/src/taller/shared/timezone.py`: `HONDURAS_TZ = ZoneInfo("America/Tegucigalpa")`, `local_today(clock) = clock().astimezone(HONDURAS_TZ).date()` (AD-7).
- [ ] **PA.S3.T3 (RED)** [delegated] Write `api/tests/invoicing/test_profile_api.py` (new file, before `save_profile`/the router exist):
  - Saving a complete profile for the first time stores it (`fiscal-profile`, "Saving a complete profile for the first time"). **Defect:** an incomplete profile is accepted as ready.
  - An RTN not 14 digits after stripping separators gives 422 `invalid_rtn` ("An RTN that is not 14 digits...").
  - A workshop with no profile reports none, with no invoicing action implied anywhere ("A workshop that never saves a profile has no row"). **Defect:** a stub profile is created on first read.
  - Repeating an identical save changes nothing; a later save updates only the changed field ("Repeating an identical save changes nothing" / "A later save updates only the fields that changed"). **Defect:** an upsert overwrites untouched fields.
  - Editing codes before any range exists succeeds; with an active range, editing codes gives 409 (literal spec detail `fiscal_profile_codes_locked` — **note:** design AD-3 originally named this differently; the design now uses the spec's literal string since it is the tested contract); once every range is exhausted/expired, editing succeeds again (fiscal-profile code-lock scenarios). **Defect:** a CAI prints under codes SAR never granted it, or codes stay permanently locked after every range finishes.
  - Workshop B cannot see workshop A's profile ("Another workshop's profile is invisible"). **Defect:** a missing `workshop_id` filter leaks fiscal data.
  - `GET /invoicing/settings` with no profile reports `profile: null` and `documents[0].ready == false`, `blocked_reason: "fiscal_profile_missing"`; with a complete profile and no range, `ready == false`, `blocked_reason: "cai_range_missing"`. **Defect:** the settings endpoint and issuance eligibility can disagree because they are not backed by one shared readiness function.
- [ ] **PA.S3.T4 (GREEN)** [delegated] Create `api/src/taller/invoicing/domain/profile.py` (`FiscalProfile`, completeness check, email regex, phone via `PhoneNumber`); extend `domain/errors.py` with `FiscalProfileMissing`, `FiscalProfileCodesLocked`, `InvalidEmail`, `InvalidEstablishmentCode`, `InvalidEmissionPointCode`; create `application/ports.py` (`FiscalProfileRepository`) and `application/use_cases.py` (`save_profile`, `get_settings` computing readiness for document type `01` via `ranges.range_states`); create `adapters/repositories.py` (`SqlAlchemyFiscalProfileRepository`), `adapters/schemas.py` (`FiscalProfileOut`, `InvoicingSettingsOut`, `DocumentReadinessOut`), `adapters/router.py` (`invoicing_router` with `PUT /invoicing/profile`, `GET /invoicing/settings`); modify `api/src/taller/main.py` to mount `invoicing_router`. Run T3, confirm green.
- [ ] **PA.S3.T5** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/invoicing/`.
- [ ] **PA.S3.T6** [inline] Work-unit commit: `:sparkles: feat(invoicing): add the fiscal profile and invoicing settings readiness`.

### Slice PA.S4 — API: CAI range create and `PATCH` (overlap, immutability, deadline bounds, profile mutex) + tests

- [ ] **PA.S4.T1 (RED)** [delegated] Write `api/tests/invoicing/test_cai_ranges_api.py` (before `create_range`/`update_range` exist):
  - A `01` range with bounds 1–100 and a fecha límite stores with `next_correlative` at 1 (`cai-ranges`, "Registering a Factura range"). **Defect:** `next_correlative` starts anywhere else.
  - A `06` range in phase A gives 422 `unsupported_document_type` ("A credit-note range is rejected before Phase B"). **Defect:** the DB check also rejects `01`, or accepts `06` early.
  - Replaying an identical registration gives 200, no second row; reusing the id with a different payload gives 409 `cai_range_id_conflict` (replay scenarios). **Defect:** a retry duplicates or silently overwrites a CAI authorization.
  - An overlapping range of the same type gives 409 `cai_range_overlap`; identical bounds on a different document type are allowed (overlap scenarios). **Defect:** valid non-overlapping ranges rejected, or overlap accepted (future duplicate numbers).
  - Editing an untouched range succeeds; editing a range that already issued a document gives 409, literal spec detail `cai_range_immutable` (**note:** design AD-4 originally named this differently; the design now uses the spec's literal string). **Defect:** a used CAI is silently rewritten, or an unused range can never be corrected.
  - Bounds validation: `range_start > range_end` or `range_end > 99,999,999` gives 422 `invalid_cai_range`; a past `issue_deadline` gives 422 `cai_deadline_passed`; one more than 366 days out gives 422 `cai_deadline_too_far`. **Defect:** a typo deadline (wrong year) is accepted and later printed.
  - Workshop B cannot see or edit workshop A's range ("Another workshop's range is invisible"). **Defect:** a missing `workshop_id` filter leaks or mutates another tenant's CAI.
- [ ] **PA.S4.T2 (GREEN)** [delegated] Modify `application/ports.py` (`CaiRangeRepository`: `list`, `get_by_id`, `add`, `save`, `allocate`) and `application/use_cases.py` (`create_range`, `update_range`, taking the profile row lock per AD-5 before the overlap check); modify `adapters/repositories.py` (`SqlAlchemyCaiRangeRepository`, including `allocate()`'s `UPDATE ... RETURNING`, unused until `PA.S5` but declared now per the Interfaces/Contracts shape), `adapters/schemas.py` (`CaiRangeOut`, create/patch requests), `adapters/router.py` (`POST`/`PATCH /invoicing/cai-ranges`). Run T1, confirm green.
- [ ] **PA.S4.T3** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/invoicing/`.
- [ ] **PA.S4.T4** [inline] Work-unit commit: `:sparkles: feat(invoicing): add CAI range registration and correction`.

### Slice PA.S5 — API: `issue_invoice`, the issuance route and reads + tests

- [ ] **PA.S5.T1** [inline] Confirm the exact signature of `order_total_cents` (`workorders/domain/money.py:13`) and of `WorkOrderRepository.get_for_update` — specifically whether it eager-loads lines via `populate_existing` (design, "Not readable in this session"). Record the confirmed signatures; they gate `PA.S5.T3`.
- [ ] **PA.S5.T2 (RED)** [delegated] Write `api/tests/invoicing/test_issue_invoice_api.py` (before `issue_invoice` exists), citing `fiscal-invoices` and `cai-ranges`:
  - No fiscal profile gives 409 `invoicing_not_configured` ("No fiscal profile at all"). **Defect:** issuance proceeds with no issuer data to snapshot.
  - A complete profile with no `01` range gives the same 409 ("A complete profile but no active Factura range"). **Defect:** the gate skips the range-missing case.
  - Both present allows issuance ("Both conditions met allow issuance").
  - Issuing from `quote`/`approved`/`in_progress` gives 409 `work_order_not_invoiceable`. **Defect:** unfinished work gets a legal document.
  - Issuing from `completed` and from `delivered` both succeed.
  - A second Factura while the first is not credited gives 409 `work_order_already_invoiced`. **Defect:** an order ends up with two live Facturas.
  - Below L 10,000 with no buyer data succeeds as CONSUMIDOR FINAL; at/above L 10,000 with no identification gives 409 `buyer_identification_required`; supplying identification at the threshold succeeds. **Defect:** the L 10,000 boundary is off by one.
  - An L 1,150.00 order yields gravado L 1,000.00 / ISV L 150.00 summing exactly to the total; the order's own total/payments/balance are unchanged. **Defect:** a snapshot field is missing, or the order response leaks tax.
  - The number is `001-001-01-00000001` for a fresh profile/range ("A number is assembled from the profile and the allocated correlative").
  - Replaying an identical issuance gives 200, same number, no number consumed; reusing the id for a different order gives 409 `fiscal_invoice_id_conflict`. **Defect:** a retry burns a correlative, a gap SAR would see.
  - Issuing with an outstanding balance succeeds and the balance is unaffected.
  - Editing the fiscal profile or the customer after issuance leaves `GET /invoicing/invoices/{id}` byte-identical (immutable-snapshot scenarios). **Defect:** a reprint renders from live data.
  - Clock at `2026-11-01T05:59Z` with deadline `2026-10-31` issues with `issue_date` `2026-10-31`; at `06:00Z` gives 409 `cai_range_expired` (`cai-ranges`, UTC-boundary scenario). **Defect:** a UTC day boundary blocks or allows past the Honduran fecha límite evening.
  - Issuing against workshop A's order while authenticated as B gives 404 `work_order_not_found`. **Defect:** tenant leak.
- [ ] **PA.S5.T3 (GREEN)** [delegated] Create `domain/documents.py` (`FiscalInvoice` snapshot dataclass); modify `application/ports.py` (`FiscalInvoiceRepository`) and `application/use_cases.py` (`issue_invoice` per AD-6's eight steps: normalize buyer, lock order, replay, eligibility, lock profile, select+allocate range, build+insert snapshot; `get_invoice`, `list_order_invoices`); modify `adapters/repositories.py` (`SqlAlchemyFiscalInvoiceRepository`), `adapters/schemas.py` (`FiscalInvoiceOut`, `FiscalInvoiceSummaryOut`, create request), `adapters/router.py` (`POST /invoicing/invoices`, `GET /invoicing/invoices/{id}`, `GET /invoicing/invoices?order_id=`), including the `IntegrityError`-naming-`fiscal_invoices_pkey` retry-once-then-409 rule. Run T2, confirm green.
- [ ] **PA.S5.T4** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/invoicing/`.
- [ ] **PA.S5.T5** [inline] Work-unit commit: `:sparkles: feat(invoicing): issue a Factura from an eligible work order`.

### Slice PA.S6 — API: `workorders` invoiced-order lock + numbering/lock-race concurrency + invariant test

- [ ] **PA.S6.T1** [inline] Confirm the exact line in `workorders/adapters/schemas.py` that sets `lines_editable = order.status in EDITABLE` and the router's `_to_out` signature (design, "Not readable in this session"). Record both; they gate `PA.S6.T3`.
- [ ] **PA.S6.T2 (RED)** [delegated] Write `api/tests/workorders/test_invoiced_lock.py` (before `active_invoice`/the lock exist), citing the `work-orders` delta:
  - Adding a line to an invoiced `completed` order gives 409 `work_order_invoiced`, lines unchanged. **Defect:** the lock is missing.
  - `lines_editable` is `false` on that order even though its status allows edits. **Defect:** the UI still offers an edit action the server will reject.
  - `completed → delivered` still succeeds on an invoiced order. **Defect:** the lock over-reaches into status transitions.
  - `PATCH` of `notes`/`complaint`/`odometer_km` still succeeds while invoiced. **Defect:** the lock over-reaches into non-line fields.
  - On a `delivered`, non-invoiced order, line edits still give the existing `work_order_locked` code, unchanged (regression check). **Defect:** the new check shadows or replaces the existing delivered/cancelled lock's error code.
  - `add_line`/`remove_line`'s existing replay paths still answer before this new check is reached (regression check). **Defect:** the new lock turns a harmless retry into a 409.
- [ ] **PA.S6.T3 (GREEN)** [delegated] Modify `workorders/domain/entities.py` (`InvoiceRef`), `domain/errors.py` (`WorkOrderInvoiced`), `application/ports.py` (`active_invoice` on `WorkOrderRepository`), `application/use_cases.py` (call `active_invoice` right after the existing `EDITABLE` check in `add_line`/`update_line`/`remove_line`), `adapters/repositories.py` (`active_invoice` via `sqlalchemy.table("fiscal_invoices", ...)` by table name only, never an `invoicing` import), `adapters/schemas.py` (`WorkOrderOut.active_invoice`; `lines_editable = status in EDITABLE and active_invoice is None`), `adapters/router.py` (409 `work_order_invoiced` mapping). Run T2, confirm green.
- [ ] **PA.S6.T4 (RED)** [delegated] Create `api/tests/invoicing/test_invoice_concurrency.py` using the committed-connections-plus-threads harness (as for login throttling and stock locks), cleaned up with `TRUNCATE` (AD-10 triggers):
  - Eight threads issuing for eight distinct orders in one workshop give correlatives 1..8, unique and gap-free. **Defect:** read-then-write allocation loses an update under concurrency.
  - Two threads issuing with the same client id give one 201 and one 200, and `next_number` advances by exactly 1. **Defect:** a rolled-back retry leaves a numbering gap.
  - A range with one number left and two concurrent issuers give one 201 and one `cai_range_exhausted`. **Defect:** the `LIMIT 1 FOR UPDATE` false-exhaustion trap AD-5 names.
  - When the current range runs out mid-burst, a standby range takes over with no false error. **Defect:** selection races against allocation.
  - A line edit and an issuance on the same order, started together, in both arrival orders: either the edit commits and the snapshot contains it, or the edit gets 409 — never a snapshot that disagrees with the committed lines. **Defect:** the snapshot and the line edit are not serialized on the order-row lock.
- [ ] **PA.S6.T5 (GREEN)** [inline] Confirm the AD-5 lock order (order row, then profile row, then range row) already implemented in `PA.S4`/`PA.S5` satisfies T4; fix any ordering gap it surfaces.
- [ ] **PA.S6.T6 (RED)** [inline] Add to `test_issue_invoice_api.py`: no status in `INVOICEABLE` has `CANCELLED` reachable from it in `TRANSITIONS`. **Defect it catches:** a future back-edge (`completed → cancelled`) would let an invoiced order be cancelled with no guard.
- [ ] **PA.S6.T7 (GREEN)** [inline] Confirm T6 passes against the existing `TRANSITIONS` table (no production change expected).
- [ ] **PA.S6.T8** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- [ ] **PA.S6.T9** [inline] Work-unit commit: `:sparkles: feat(workorders): lock lines while an order has a non-credited Factura`.

### Slice PA.S7 — Web: customer billing name and RTN in the form and detail

- [ ] **PA.S7.T1** [inline] Confirm the current content of `web/src/test/handlers.ts` (design, "Not readable in this session") — specifically whether the per-test `server.use(...)` pattern (design correction 1) already fully applies. Record the confirmed pattern; every invoicing/customers web test in this change follows it.
- [ ] **PA.S7.T2 (RED)** [delegated] Add to `web/src/features/customers/CustomerForm.test.tsx` and `CustomerDetailPage.test.tsx` (`server.use` per test): the form renders and submits "Nombre de facturación (razón social)" and "RTN"; a 422 `invalid_rtn` response renders its Spanish message, not the generic fallback; `CustomerDetailPage` renders both fields when present and renders nothing (not a literal "null"/"undefined") when absent. **Defects:** the new fields are never sent; a new error code falls through to the generic message; an absent optional field renders a literal null string.
- [ ] **PA.S7.T3 (GREEN)** [delegated] Modify `web/src/features/customers/api.ts` (types gain `billing_name`/`rtn`), `copy.ts` (`invalid_rtn` message), `CustomerForm.tsx`, `CustomerDetailPage.tsx`. Run T2, confirm green.
- [ ] **PA.S7.T4** [inline] Run this slice's verification: `cd web && npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PA.S7.T5** [inline] Work-unit commit: `:sparkles: feat(customers): add billing name and RTN to the customer form and detail`.

### Slice PA.S8 — Web: invoicing `api.ts`/`hooks.ts`/`copy.ts`/routes; "Más" entry; settings page

- [ ] **PA.S8.T1 (RED)** [delegated] Write `web/src/features/invoicing/settings/InvoicingSettingsPage.test.tsx` (`server.use` per test, before the page exists): with no profile, the SAR/contador/thermal-paper notice is visible with a "Configurar" action (`fiscal-profile`, "The notice is shown before the profile is complete"); with a complete profile, the same notices are still visible ("The notice is still shown after the profile is complete"); each readiness entry's `blocked_reason` renders a distinct Spanish text; range states (`active`/`standby`/`exhausted`/`expired`) each render distinct labels; offline disables profile-save and range-create with the Spanish message. **Defects:** opt-in path unclear with no profile; the notice disappears once most needed; a blocked state shown as ready, or every reason rendering the same text; a write attempted offline.
- [ ] **PA.S8.T2 (RED)** [delegated] Add to `web/src/app/AppShell.test.tsx`: the "Más" menu shows a "Facturación" entry regardless of profile state, navigating to `/ordenes/facturacion` (`fiscal-profile`, "The menu entry is visible with no profile yet"). **Defect:** the entry is hidden until a profile exists, blocking the only path to create the first one.
- [ ] **PA.S8.T3 (GREEN)** [delegated] Create `invoicing/api.ts` (typed client for `GET /invoicing/settings`, `PUT /invoicing/profile`), `invoicing/copy.ts` (SAR notice text, state labels, `blocked_reason` map), `invoicing/hooks.ts` (`useInvoicingSettings`, the `settings` query key from AD-15's table), `invoicing/routes.tsx`, `settings/{InvoicingSettingsPage,SarNotice,ReadinessSummary,CaiRangeList}.tsx`. Modify `app/AppShell.tsx` (the menu entry), `app/copy.ts`, `app/router.tsx` (spread `invoicingShellRoutes` into `/ordenes`'s children, per the `caja` precedent). Run T1–T2, confirm green.
- [ ] **PA.S8.T4** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PA.S8.T5** [inline] Work-unit commit: `:sparkles: feat(invoicing): add the fiscal settings page and its shell entry`.

### Slice PA.S9 — Web: profile form and range forms

- [ ] **PA.S9.T1 (RED)** [delegated] Write `FiscalProfileForm.test.tsx`/`CaiRangeForm.test.tsx` (`server.use` per test): the profile form sends every required field; a 422 per-field error renders its own Spanish message; the range form offers only `document_type: "01"`; a 409 `cai_range_overlap` and a 422 `cai_deadline_too_far` render distinct messages; editing an in-use range's bounds is disabled in the UI with an explanation, not a silent 409 after submit; double-clicking "Guardar" on the range form sends one client id; offline disables both forms. **Defects:** a validation error falls through to a generic message or a required field is omitted; the form offers a document type the API will reject; a double click sends two ids.
- [ ] **PA.S9.T2 (GREEN)** [delegated] Create `FiscalProfilePage.tsx`, `FiscalProfileForm.tsx`, `CaiRangePage.tsx`, `CaiRangeForm.tsx`; modify `invoicing/api.ts`/`hooks.ts` (`useSaveProfile`, `useCreateCaiRange`, `useUpdateCaiRange`), `invoicing/copy.ts` (remaining range error-code mappings), `invoicing/routes.tsx` (`/ordenes/facturacion/datos`, `/ordenes/facturacion/rangos/{nuevo,:rangeId}`). Run T1, confirm green.
- [ ] **PA.S9.T3** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PA.S9.T4** [inline] Work-unit commit: `:sparkles: feat(invoicing): add the fiscal profile and CAI range forms`.

### Slice PA.S10 — Web: `InvoiceSection`, `IssueInvoiceDialog`, `InvoiceDetailPage`, lock message

- [ ] **PA.S10.T1 (RED)** [delegated] Add to `WorkOrderDetailPage.test.tsx` (`server.use` per test): a workshop with no fiscal profile renders no invoicing UI, receipt links unaffected (`fiscal-invoices`, "A workshop with no fiscal profile sees no Factura action, and the receipt is unaffected"); a ready, uninvoiced, eligible order shows "Emitir factura" ahead of the receipt links, both still present ("An eligible, uninvoiced order shows the Factura action first"); an invoiced order links to the Factura, still ahead of the receipt ("An invoiced order links to the Factura, still ahead of the receipt"); a 409 `work_order_invoiced` on a line action renders "La orden tiene una factura emitida…" from `workorders/copy.ts`. **Defects:** a non-opted-in workshop sees fiscal UI; the Factura action hides the receipt instead of preceding it; a double-invoice action is offered; a new error code falls through to a generic message.
- [ ] **PA.S10.T2 (RED)** [delegated] Write `IssueInvoiceDialog.test.tsx`: prefill from `useCustomer(order.customer.id)`'s billing data, editable before submit (`fiscal-invoices`, "Buyer data is prefilled from the customer and editable at issuance"); the client-side L 10,000/RTN mirror blocks submit until both fields are filled, server still authoritative; a double click sends one client id; success calls `setQueryData` for the invoice and invalidates the order detail, the order's invoice list and settings, then navigates to the invoice detail (AD-15's query-key table); offline disables the issue action with the Spanish message. **Defects:** a stale prefill is sent; a retry/double-click risks two Facturas; a stale cache shows the pre-issuance state after a successful issue.
- [ ] **PA.S10.T3 (RED)** [delegated] Write `InvoiceDetailPage.test.tsx`: a previously fetched Factura renders offline from the persisted cache (`fiscal-invoices`, "A previously fetched Factura renders offline"). **Defect:** an offline reopen fails instead of reading the cache.
- [ ] **PA.S10.T4 (GREEN)** [delegated] Create `issue/buyer.ts` (client mirror of the AD-11 rules), `issue/InvoiceSection.tsx`, `issue/IssueInvoiceDialog.tsx`, `documents/InvoiceDetailPage.tsx`, `documents/InvoiceSummary.tsx`; modify `invoicing/api.ts`/`hooks.ts` (`useIssueInvoice`, `useInvoice`, `useOrderInvoices`, remaining AD-15 query keys), `invoicing/copy.ts` (issuance error-code map); modify `workorders/WorkOrderDetailPage.tsx` (render `InvoiceSection`), `workorders/api.ts` (`active_invoice` on the order type), `workorders/copy.ts` (`work_order_invoiced` message). Run T1–T3, confirm green.
- [ ] **PA.S10.T5** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PA.S10.T6** [inline] Work-unit commit: `:sparkles: feat(invoicing): issue a Factura from the order detail screen`.

### Slice PA.S11 — Web: print primitives, `InvoiceDocument`, both print pages, copies, demo band

- [ ] **PA.S11.T1** [inline] Confirm the receipt's existing measured-`@page`-height technique (`useLayoutEffect` + `getBoundingClientRect`, per `CLAUDE.md`'s description of the 58 mm receipt layout; design, "Not readable in this session"). Record the exact hook so `ThermalPageStyle` reimplements it without importing `ReceiptBody` or its files (AD-16; correction 2: receipt code stays untouched).
- [ ] **PA.S11.T2 (RED)** [delegated] Write `ThermalPageStyle.test.tsx`: after the content height is measured, `@page` is `58mm <h>mm; margin: 0`; before measurement resolves, the fallback `58mm 297mm` is emitted (`fiscal-document-print`, "Printing before the 58 mm measurement resolves still produces a valid page"). **Defects:** the measured height is never applied; an unmeasured print attempt produces an invalid page.
- [ ] **PA.S11.T3 (RED)** [delegated] Write `InvoiceDocument.test.tsx`, one fixture-driven assertion per "Printed field map" Factura row (issuer fields; "FACTURA"; CAI; rango autorizado; fecha límite; number; buyer or "CONSUMIDOR FINAL"; date; each line's description/quantity/unit value; exento/exonerado/gravado 15%/ISV 15%/descuentos; currency "L"; total; total in words; both destination legends) (`fiscal-document-print`, "Every mandatory field is present on both layouts"); `buyer` null renders "CONSUMIDOR FINAL", not a blank; zero exento/exonerado/discount render "L 0.00", never blank ("A Factura with no exento, exonerado, or discount amounts still prints them as zero"); both copies render by default, "ORIGINAL: CLIENTE" then "COPIA: EMISOR", with a "Solo original" toggle dropping the second ("Both destinations appear in the printed output"). **Defect per row:** that specific Art. 10–11 field missing on one layout — the exact CT Art. 159–161 closure exposure the risk table names; a zero amount rendered as an empty cell; a forgotten second print leaving the issuer without its copy.
- [ ] **PA.S11.T4 (RED)** [delegated] Write `DemoBand.test.tsx` (env stubbed with `vi.stubEnv`): `isDemoBuild()` true shows "DEMOSTRACIÓN — SIN VALOR FISCAL" on each copy; unset shows none (`fiscal-document-print`, demo-watermark scenarios). **Defect:** the demo prints a realistic-looking Factura, or a real build carries the watermark.
- [ ] **PA.S11.T5 (GREEN)** [delegated] Modify `web/src/features/auth/demoAccount.ts` (`isDemoBuild()`); create `print/ThermalPageStyle.tsx`, `print/LetterPageStyle.tsx`, `print/PrintActionBar.tsx` (`print:hidden`), `print/DemoBand.tsx`, `print/InvoiceDocument.tsx`, `print/Invoice58Page.tsx`, `print/InvoiceLetterPage.tsx`; wire the two print routes as lazy siblings of `<AppShell>` under `RequireSession` in `app/router.tsx`. Run T2–T4, confirm green.
- [ ] **PA.S11.T6** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PA.S11.T7** [inline] Work-unit commit: `:sparkles: feat(invoicing): print the Factura on 58 mm and letter layouts`.

### Slice PA.S12 — Closing: seed, docs, migration/downgrade drill, real-browser and print check

- [ ] **PA.S12.T1** [inline] Extend `deploy/demo/seed-demo-account.sh` per "Demo seed growth → Phase A": `PUT /invoicing/profile` for "Taller Demostración S. de R.L." / "Taller Demo", RTN `99999999999999`, fictional address, phone `2200-0000`, `demo@example.invalid`, codes `001`/`001`; `PATCH` María Hernández's customer with billing name "María Hernández" and RTN `99999999990001`; register a `01` range (fictional CAI, bounds 1–500, deadline = seed date + 364 days on first creation); issue a Factura against the seeded "Corolla alignment" `delivered` order, L 400.00, consumidor final (gravado L 347.83 / ISV L 52.17 per AD-8's worked table). Add the idempotency check: run the script twice, confirm the second run creates zero new fiscal rows.
- [ ] **PA.S12.T2** [inline] Update `deploy/demo/README.md`: document the seeded profile/range/Factura, the yearly re-registration note for the seeded range's deadline, and AD-20's rollback change (the demo downgrade now runs `alembic -x discard_fiscal_documents=demo downgrade <prev>` after the `pg_dump`, never a bare downgrade once fiscal rows exist).
- [ ] **PA.S12.T3** [inline] Update `CLAUDE.md`'s **Architecture** section: add an `invoicing` subsection (fiscal profile/CAI range/Factura domain, the AD-2 schema-only lock reference from `workorders`, the AD-5 lock order, the AD-10 immutability trigger, the AD-20 forward-only rollback rule).
- [ ] **PA.S12.T4** [inline] Exercise the phase-A migration round-trip locally: `uv run alembic upgrade head`, `uv run alembic downgrade -1`, `uv run alembic upgrade head` against an empty dev database; confirm `uv run pytest tests/test_migrations.py` is green. Record the result.
- [ ] **PA.S12.T5** [delegated] Exercise the AD-20 guard: with the demo seed's one Factura row committed, run `uv run alembic downgrade -1` **without** `-x discard_fiscal_documents=demo` and confirm it raises, row intact; then confirm the same downgrade **with** the flag succeeds on a disposable database (never on the seeded demo without a prior `pg_dump`, per the Rollback Plan). Record both results.
- [ ] **PA.S12.T6** [inline] Run the full phase-A verification suite and record each result: API (`docker compose up -d db`; `uv run ruff check . && uv run ruff format --check . && uv run pytest`); Web (`npm run lint && npm run typecheck && npm test -- --run && npm run build`); migrations (T4, T5).
- [ ] **PA.S12.T7** [delegated] Deploy phase A to the demo per `deploy/demo/README.md`'s procedure, and re-run the seed script against it (per T1's idempotency check).
- [ ] **PA.S12.T8** [delegated] Real-browser check at **390×844** against the deployed demo: a workshop with no fiscal profile shows no invoicing action anywhere, orders/payments/receipts/export behave exactly as before; after saving the seeded profile and range, the seeded order shows "Emitir factura"/the issued Factura link ahead of the receipt links; the issued Factura's print preview (58 mm and letter) shows every Art. 10–11 field, the demo watermark, and both copy destinations, and printing twice changes nothing server-side; attempting to add a line to an invoiced `completed` order shows the Spanish `work_order_invoiced` message, while moving it to `delivered` and recording a payment still work; offline, a previously visited settings screen and an issued Factura's detail/print still render, every write disabled with its message. Record every defect found and whether it was fixed before closing this slice.
- [ ] **PA.S12.T9** [inline] Record explicitly (proposal open questions 1–2): **real (non-demo) invoicing stays off-limits until phase B ships and a contador has reviewed a printed sample of both layouts.** No configuration or documentation produced by this phase invites a real workshop to issue a real Factura with v1; phase A's deployment target is the public demo only.
- [ ] **PA.S12.T10** [inline] Re-run this slice's verification after any T8 fixes.
- [ ] **PA.S12.T11** [inline] Work-unit commit(s): `:memo: docs(invoicing): seed the demo fiscal profile and document the phase A rollback` (plus one atomic commit per T8 fix, if any).

---

## Phase B: Notas de Crédito, export and range warnings

Starts only after phase A is merged and deployed, and the user explicitly approves starting phase B.

### Slice PB.S1 — API: phase B migration, credit-note domain/use case/routes, `mark_credited`, lock release, `06` readiness + tests incl. credit concurrency

- [ ] **PB.S1.T1** [delegated] Create `api/migrations/versions/<rev>_fiscal_credit_notes.py`: `fiscal_credit_notes` per "Data model per phase → Phase B", the `taller_fiscal_append_only` trigger on it, a guarded `downgrade()` (AD-20, on `fiscal_credit_notes`). Confirm whether `api/migrations/env.py` needs any change (the new model lives in the already-imported `taller.invoicing.adapters.models` module); record the confirmation.
- [ ] **PB.S1.T2** [inline] Modify `api/src/taller/invoicing/adapters/models.py`: add `FiscalCreditNoteModel` matching T1's schema exactly (every unique/check constraint and index from the Phase B data model table).
- [ ] **PB.S1.T3** [inline] Modify `domain/documents.py` (`FiscalCreditNote` snapshot dataclass) and `domain/errors.py` (`InvoiceAlreadyCredited`, `InvalidCreditNoteReason`, `CreditNoteIdConflict`, `CreditNoteNotFound`).
- [ ] **PB.S1.T4 (RED)** [delegated] Write `api/tests/invoicing/test_credit_notes_api.py` (before `issue_credit_note` exists), citing `credit-notes`:
  - A full credit note references the Factura's CAI, number, and issuance date, carries the same buyer name/RTN, and equals the Factura's full total ("A full credit note references its original Factura"). **Defect:** a missing Art. 25–26 reference, or a mismatched amount.
  - No reason gives 422 ("A credit note with no reason is rejected"). **Defect:** a reasonless correction is accepted.
  - No `06` range at all gives 409 `invoicing_not_configured` ("No active document-type-06 range blocks credit note issuance"). **Defect:** the opt-in gate is bypassed for the correction type.
  - An exhausted `06` range gives 409 `cai_range_exhausted` ("An exhausted document-type-06 range blocks issuance"). **Defect:** exhaustion enforcement does not extend to credit notes.
  - A second credit note against the same Factura gives 409 `credit_note_already_issued`. **Defect:** double reversal of one sale.
  - Replaying an identical issuance gives 200, no number consumed; reusing the id against a different Factura gives 409 `credit_note_id_conflict`. **Defect:** a retry burns a `06` correlative.
  - After the credit note, a `completed` order's lines become editable again, and a new Factura may be issued allocating a new `01` correlative ("Lines become editable again after a full credit note" / "A new Factura may be issued after a full credit note"). **Defect:** the lock is not released, or re-invoicing collides with the stale partial-unique index.
  - A `delivered`, fully-credited order's lines stay `work_order_locked`, but a new Factura may be issued with corrected buyer data, same lines/total ("Re-invoicing a delivered, fully credited order with corrected buyer data"). **Defect:** amount corrections sneak into a delivered order, or re-invoicing is blocked entirely.
  - Payments, balance, and stock are unchanged by the credit note ("A credit note has no effect on payments or stock"). **Defect:** a credit note accidentally reverses a payment or stock movement.
  - Editing the customer after a credit note leaves it unchanged on reprint. **Defect:** a reprint renders from live data.
  - Workshop B cannot see workshop A's credit note. **Defect:** tenant leak.
- [ ] **PB.S1.T5 (GREEN)** [delegated] Implement `issue_credit_note`/`get_credit_note` in `application/use_cases.py` per AD-13's five steps; create `CreditNoteRepository`/`SqlAlchemyCreditNoteRepository`; modify `adapters/schemas.py` (`FiscalCreditNoteOut`, request shape; `FiscalInvoiceOut`/`FiscalInvoiceSummaryOut` gain `credit_note: {id, number, issue_date} | null`), `adapters/router.py` (`POST`/`GET /invoicing/credit-notes`); remove the phase-A-only `unsupported_document_type` gate for `06` in `create_range`. Run T4, confirm green.
- [ ] **PB.S1.T6 (RED)** [delegated] Create `api/tests/invoicing/test_credit_note_concurrency.py`: two concurrent credit notes against one Factura give one 201 and one 409 `invoice_already_credited`, and the `06` range's `next_number` advances by exactly 1. **Defect it catches:** a credit race without the order-row and invoice-row locks lets both succeed, double-crediting one Factura.
- [ ] **PB.S1.T7 (GREEN)** [inline] Confirm the AD-5 lock order (order, then invoice, then profile, then range) already serializes this; fix any gap T6 surfaces.
- [ ] **PB.S1.T8** [inline] Run this slice's verification: `docker compose up -d db`; `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- [ ] **PB.S1.T9** [inline] Work-unit commit: `:sparkles: feat(invoicing): issue a full credit note and release the invoiced-order lock`.

### Slice PB.S2 — API: `range_warnings` and the settings output + boundary tests

- [ ] **PB.S2.T1 (RED)** [delegated] Write `api/tests/invoicing/test_range_warnings.py` (before `range_warnings` exists), citing `cai-ranges`: 61 days to the latest usable range's fecha límite gives no warning, 60 days gives `range_expires_soon` with `days_left` ("A warning appears exactly 60 days before the fecha límite" / "No fecha-límite warning appears more than 60 days out"); 51 numbers remaining gives no warning, 50 gives `range_low_numbers` with `remaining` ("A low-remaining-numbers warning appears once remaining numbers fall below the design-fixed threshold"); a standby successor in the usable set silences both warnings. **Defects:** an off-by-one on the Art. 59 window or the chosen threshold; a warning fires about a range a successor already covers, training the owner to ignore warnings.
- [ ] **PB.S2.T2 (GREEN)** [delegated] Implement `range_warnings(ranges, today)` (`LOW_NUMBERS_THRESHOLD = 50`, `EXPIRY_WARNING_DAYS = 60`, AD-18) in `domain/ranges.py` (or a new `domain/warnings.py`); wire it into `get_settings`'s `DocumentReadinessOut.warnings`. Run T1, confirm green.
- [ ] **PB.S2.T3** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/invoicing/`.
- [ ] **PB.S2.T4** [inline] Work-unit commit: `:sparkles: feat(invoicing): warn before a CAI range expires or runs low`.

### Slice PB.S3 — API: three fiscal CSVs + customer columns + export tests

- [ ] **PB.S3.T1** [inline] Confirm the exact function shape of `api/src/taller/export/adapters/sources.py`'s existing per-entity sources (explicit column lists, `WHERE workshop_id = :current`) and `adapters/router.py`'s file-dict structure (design, "Not readable in this session"). Record the confirmed pattern so the three new sources match it exactly.
- [ ] **PB.S3.T2 (RED)** [delegated] Extend `api/tests/export/test_export_api.py` (before the three new sources exist), citing `data-export`: the ZIP contains ten files, not seven ("The export contains one file per entity"); a workshop with no fiscal data still gets header-only `fiscal_invoices.csv`/`fiscal_invoice_lines.csv`/`fiscal_credit_notes.csv` ("A workshop that never invoiced anything still gets empty fiscal CSVs"); `fiscal_invoices.csv` lists only the current workshop's documents, and a credit note row references its invoice id; after a full credit note reopens an order for editing, `fiscal_invoice_lines.csv` still shows the lines as they were at issuance, not the order's current lines ("Invoice lines reflect the snapshot, not the order's current lines"); a credit-note `reason` starting with `=` is prefixed with `'`; `customers.csv` carries `billing_name`/`rtn`, empty when absent ("A customer's billing data is exported"). **Defects:** a forgotten or duplicated entity; an empty result set crashes the builder; a tenant leak or dangling reference; the export reads live order lines instead of the immutable snapshot; a crafted reason executes as a formula; the new customer fields are left out of "Exportar todo".
- [ ] **PB.S3.T3 (GREEN)** [delegated] Add the three workshop-scoped sources to `sources.py` (`fiscal_invoices`, `fiscal_invoice_lines`, `fiscal_credit_notes`, columns per AD-19's table, rows ordered by `issued_at, number`); extend the existing `customers` source with `billing_name`/`rtn`; add the three new entries to `router.py`'s file dict. Run T2, confirm green.
- [ ] **PB.S3.T4** [inline] Run this slice's verification: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/export/`.
- [ ] **PB.S3.T5** [inline] Work-unit commit: `:sparkles: feat(export): add invoices, invoice lines and credit notes to the export`.

### Slice PB.S4 — Web: credit note dialog, credit note detail, and the documents list on the order detail

- [ ] **PB.S4.T1 (RED)** [delegated] Write `CreditNoteDialog.test.tsx` (`server.use` per test): submitting with no reason is blocked client-side before any request; offline disables the issue action with the Spanish message; on success, invalidates the invoice detail, the order's document list, the order detail (so `active_invoice`/`lines_editable` refresh), and settings. **Defects:** an empty reason reaches the server and bounces with a generic error; a credit-note write is attempted offline; a stale lock state is shown after crediting.
- [ ] **PB.S4.T2 (RED)** [delegated] Add to `InvoiceSection.test.tsx`: once an invoice has a credit note, the order's document list shows both documents, and — if the order is `completed` — a new "Emitir factura" action reappears. **Defect:** the UI never reflects that the lock lifted.
- [ ] **PB.S4.T3 (RED)** [delegated] Write `CreditNoteDetailPage.test.tsx`: a previously fetched credit note renders offline from the persisted cache. **Defect:** an offline reopen fails instead of reading the cache.
- [ ] **PB.S4.T4 (GREEN)** [delegated] Create `documents/CreditNoteDialog.tsx`, `documents/CreditNoteDetailPage.tsx`; modify `invoicing/api.ts`/`hooks.ts` (`useIssueCreditNote`, `useCreditNote`, AD-15's credit-note query key), `invoicing/copy.ts` (credit-note error-code map), `invoicing/routes.tsx` (`/ordenes/:orderId/nota-credito/:creditNoteId`), `issue/InvoiceSection.tsx` (list both document types; offer "Emitir nota de crédito"), `documents/InvoiceDetailPage.tsx` (the credit-note action and link). Run T1–T3, confirm green.
- [ ] **PB.S4.T5** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PB.S4.T6** [inline] Work-unit commit: `:sparkles: feat(invoicing): issue a credit note from an issued Factura`.

### Slice PB.S5 — Web: `CreditNoteDocument` and both print pages

- [ ] **PB.S5.T1 (RED)** [delegated] Write `CreditNoteDocument.test.tsx`, one fixture-driven assertion per "Printed field map" Nota de Crédito row (issuer fields as of this issuance; "NOTA DE CRÉDITO"; its own CAI/rango autorizado/fecha límite; number; buyer name/RTN copied from the Factura; date; gravado 15%/ISV 15%; total; total in words; the original's CAI/number/date reference; the reason; blank "Firma"/"Identidad" lines; both destination legends) (`fiscal-document-print`, "Every mandatory credit note field is present on both layouts"). **Defect per row:** a missing Art. 25–26 field — the exact CT Art. 159–161 closure exposure the risk table names.
- [ ] **PB.S5.T2 (GREEN)** [delegated] Create `print/CreditNoteDocument.tsx` (reusing `ThermalPageStyle`/`LetterPageStyle`/`PrintActionBar`/`DemoBand` from `PA.S11`, not `ReceiptBody`), `print/CreditNote58Page.tsx`, `print/CreditNoteLetterPage.tsx`; wire the two print routes as lazy siblings of `<AppShell>`. Run T1, confirm green.
- [ ] **PB.S5.T3** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PB.S5.T4** [inline] Work-unit commit: `:sparkles: feat(invoicing): print the credit note on 58 mm and letter layouts`.

### Slice PB.S6 — Web: warnings on the settings page and in the dialogs

- [ ] **PB.S6.T1 (RED)** [delegated] Add to `RangeWarnings.test.tsx`/`InvoicingSettingsPage.test.tsx`: a `range_expires_soon` warning renders its days-left Spanish text, and a `range_low_numbers` warning renders its remaining-count text, both on the settings page. **Defect:** warnings are computed by the API but never shown to the owner who must act on them.
- [ ] **PB.S6.T2 (RED)** [delegated] Add to `IssueInvoiceDialog.test.tsx`/`CreditNoteDialog.test.tsx`: when the active range carries a warning, the dialog shows one Spanish warning line without blocking submission. **Defect:** a workshop issues documents for weeks without ever seeing its range is about to lapse.
- [ ] **PB.S6.T3 (GREEN)** [delegated] Create `settings/RangeWarnings.tsx`; modify `invoicing/api.ts`/`hooks.ts` (confirm the web `warnings` type matches `PB.S2`'s API change), `invoicing/copy.ts` (warning-code text), `settings/InvoicingSettingsPage.tsx`, `issue/IssueInvoiceDialog.tsx`, `documents/CreditNoteDialog.tsx`. Run T1–T2, confirm green.
- [ ] **PB.S6.T4** [inline] Run this slice's verification: `npm run lint && npm run typecheck && npm test -- --run`.
- [ ] **PB.S6.T5** [inline] Work-unit commit: `:sparkles: feat(invoicing): show range-expiry and low-numbers warnings`.

### Slice PB.S7 — Closing: seed (`06` range, credit note, re-issued Factura), docs, downgrade drill, real-browser and print check

- [ ] **PB.S7.T1** [inline] Extend `deploy/demo/seed-demo-account.sh` per "Demo seed growth → Phase B": register a `06` range (fictional CAI, bounds 1–100, same deadline rule); issue a credit note against the seeded Factura, reason "Datos del comprador incorrectos"; re-issue a Factura on the same order with buyer "María Hernández" and her RTN. Re-run the idempotency check (two runs, zero new fiscal rows on the second).
- [ ] **PB.S7.T2** [inline] Update `deploy/demo/README.md`: document the seeded `06` range, credit note, and re-issued Factura; the export's growth to ten files; confirm "phase B rolls back before phase A" is stated.
- [ ] **PB.S7.T3** [inline] Update `CLAUDE.md`'s **Architecture** section: extend the `invoicing` subsection with the credit-note snapshot, the lock-release mechanism (AD-13), the `range_warnings` threshold (AD-18), and the export's growth to ten files (AD-19).
- [ ] **PB.S7.T4** [inline] Exercise the phase-B migration round-trip locally: `uv run alembic upgrade head`, `uv run alembic downgrade -1`, `uv run alembic upgrade head` against an empty dev database; confirm `uv run pytest tests/test_migrations.py` is green.
- [ ] **PB.S7.T5** [delegated] Exercise the AD-20 guard on `fiscal_credit_notes`: with the demo seed's one credit note row committed, `uv run alembic downgrade -1` without the flag raises, row intact; with `-x discard_fiscal_documents=demo` it succeeds on a disposable database. Confirm phase A's `credited_at` stamps survive a phase-B-only downgrade harmlessly.
- [ ] **PB.S7.T6** [inline] Run the full phase-B verification suite and record each result: API (`docker compose up -d db`; `uv run ruff check . && uv run ruff format --check . && uv run pytest`); Web (`npm run lint && npm run typecheck && npm test -- --run && npm run build`); migrations (T4, T5).
- [ ] **PB.S7.T7** [delegated] Deploy phase B to the demo per `deploy/demo/README.md`'s procedure, and re-run the seed script against it.
- [ ] **PB.S7.T8** [delegated] Real-browser check at **390×844** against the deployed demo: the credit note dialog requires a reason, is disabled offline, and both print layouts render the reason, the original Factura's reference, and blank signature/ID lines; after the credit note, a `completed` order's lines are editable again and a new Factura can be issued and printed; "Exportar todo" downloads a ZIP with ten CSVs; the settings screen and the issue/credit-note dialogs show the range warnings once the seeded range is within the thresholds (or confirm by temporarily registering a near-expiry range in a scratch workshop, removed afterward, never on the shared demo account). Record every defect found and whether it was fixed before closing this slice.
- [ ] **PB.S7.T9** [inline] Re-run this slice's verification after any T8 fixes.
- [ ] **PB.S7.T10** [inline] Work-unit commit(s): `:memo: docs(invoicing): seed the demo credit note and document the phase B rollback` (plus one atomic commit per T8 fix, if any).
