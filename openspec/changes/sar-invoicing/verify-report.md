# Verify report — sar-invoicing, Phase A (PA.S1–PA.S13)

**Change**: `sar-invoicing` — Phase A (PA.S1–PA.S12 + PA.S13 review-fixes slice)
**Store**: openspec · **Branch**: `feat/sar-invoicing` (from `main`) · **Scope**: phase A only, per request

## 1. Executed checks (all re-run live, not read from prior records)

| Command | Result |
|---|---|
| `docker compose up -d db` | container running |
| `cd api && uv run ruff check .` | **All checks passed!** |
| `cd api && uv run ruff format --check .` | **138 files already formatted** |
| `cd api && uv run pytest` | **360 passed** |
| `cd web && npm run lint` | clean, exit 0 |
| `cd web && npm run typecheck` | clean, exit 0 |
| `cd web && npm test -- --run` | **55 test files, 232 tests passed** |
| `cd web && npm run build` | succeeded (`tsc -b && vite build`, PWA precache generated) |

All results match tasks.md's own recorded evidence exactly (same counts: 360 API tests, 232 web tests). No drift between claimed and observed state.

## 2. Task-completion state (observed, not rewritten)

Read `openspec/changes/sar-invoicing/tasks.md` in full (406 lines). Slices **PA.S1–PA.S13 are all checked `[x]`** except three tasks, exactly matching the request's "expected pending items":

- `PA.S12.T7` — deploy phase A to the demo (deferred until after the implementation batch)
- `PA.S12.T8` — real-browser check at 390×844 on the deployed demo (deferred, needs T7)
- `PA.S12.T10` — re-verify after T8 fixes (deferred, needs T8)

No other unchecked box exists in phase A. Phase B (`PB.S1`–`PB.S7`) is entirely unchecked, and I confirmed no phase-B code leaked in: `find` for `*CreditNote*`/`*credit_note*` across both `api/` and `web/` returned nothing.

`git log --oneline main..feat/sar-invoicing` shows **24 commits**, including every work-unit commit tasks.md claims by hash (`262e926`…`911fe02`, `0395ffa`, and PA.S13's `7effa36`/`a6b5d33`/`ea621e1`). Working tree is clean (per the session's git status).

## 3. Spec scenario → test mapping (phase A specs only)

Read all 8 spec files; `data-export` and `credit-notes` are tagged **Phase: B** and correctly out of scope (confirmed via each file's header). Within `fiscal-document-print`, its one Phase-B requirement ("Credit Note Layouts…") is likewise excluded.

Cross-referenced spec scenario titles against actual pytest/vitest function names (not just tasks.md's narrative) for `fiscal-profile`, `cai-ranges`, `fiscal-invoices`, `fiscal-document-print` (phase A), `work-orders` delta, `customers` delta. Coverage is comprehensive — the large majority of scenarios have a test whose name is a near-literal transcription of the scenario title (e.g. `test_a_utc_day_boundary_does_not_cause_an_incorrect_allow_or_block`, `test_registering_a_factura_range_starts_next_correlative_at_range_start`). I deep-dove the print field map specifically, since the task asked for it by name:

- `api/src/taller/invoicing/domain/documents.py`'s `FiscalInvoice` dataclass carries every Art. 10–11 field the research note lists (issuer RTN/razón social/nombre comercial/address/phone/email; CAI/rango/fecha límite; number; buyer-or-CONSUMIDOR-FINAL; date; exento/exonerado/gravado/ISV/descuento; total + total in words).
- `web/src/features/invoicing/print/InvoiceDocument.tsx` renders every one of those fields, and `InvoiceDocument.test.tsx` has a single fixture-driven test asserting every row by content, plus dedicated tests for the CONSUMIDOR FINAL fallback, zero-amount "L 0.00" rendering, and the ORIGINAL/COPIA destination legend.
- Both print routes (`Invoice58Page.tsx`, `InvoiceLetterPage.tsx`) render both copies by default; `InvoiceLetterPage.test.tsx` (added in PA.S13.T7) has a real regression test for the `break-before-page` wrapper and the letter `@page { margin: 12mm; }` rule — I verified this is a genuine test (not an echo) by reading its assertions directly.

**Three genuine coverage gaps found** (diagnostic findings only — SDD verify does not gate archive on these):

1. **WARNING** — `FiscalProfile.is_complete` (`api/src/taller/invoicing/domain/profile.py:43`) has zero test exercising it with a field missing. The fiscal-profile spec's own scenario "A profile missing one field is incomplete" is untested. In practice this is low-risk: `PUT /invoicing/profile` requires every field, so an incomplete row can never actually be saved — but the predicate itself, and the spec's named scenario, have no automated proof.
2. **WARNING** — No test for "a previously fetched fiscal profile renders offline" (fiscal-profile spec). Every invoicing web test file was checked (`rg offline` across all of `src/features/invoicing/`); only write-disabled-while-offline tests exist for the profile forms/settings page. The read-from-persisted-cache behavior itself is asserted for the Factura (`InvoiceDetailPage.test.tsx`) but never for the profile.
3. **WARNING** — No test asserts `GET /invoicing/invoices/{id}` is tenant-isolated (fiscal-invoices spec's "Another workshop's Factura is invisible"). I read `get_invoice_route`/`get_invoice` directly and confirmed the implementation **does** correctly scope by `workshop_id` — risk is low, the pattern matches every other feature in the codebase — but no regression test exists for this specific route (only the issuance-side tenant check, `test_issuing_against_another_workshops_order_is_not_found`, is tested).

**SUGGESTION** — fiscal-document-print's "a previously fetched document prints offline" has no direct test on `Invoice58Page`/`InvoiceLetterPage` (only on `InvoiceDetailPage`, via the same `useInvoice` hook and cache mechanism). Low risk since the mechanism is shared and already proven once, but the print routes themselves are untested for this specific scenario.

No CRITICAL findings. The PA.S13 review-fixes slice's own critical finding (the un-locked range-read race in `update_range`) was independently re-derived from source and confirmed fixed (`api/src/taller/invoicing/application/use_cases.py`'s `update_range` re-reads the range after acquiring the profile lock, before deciding immutability).

## 4. Summary

- **CRITICAL: 0** · **WARNING: 3** · **SUGGESTION: 1**
- All checks green, state matches tasks.md exactly, no undisclosed drift between claimed and actual implementation.
- Phase A is functionally complete pending only the three explicitly deferred closing steps (demo deploy, seed re-run, real-browser/print-preview check).

---

**Status**: success
**Summary**: Verified `sar-invoicing` phase A against its 6 in-scope spec files and tasks.md; re-ran every check live (API 360 passed, web 232 passed + build), confirmed all 24 branch commits exist, and traced spec scenarios to tests — found 3 WARNING-level coverage gaps (profile completeness, profile offline-read, invoice GET tenant isolation) and 1 SUGGESTION, 0 CRITICAL.
**Next**: close the three remaining PA.S12 tasks (closing steps, not implementation gaps; the coverage findings are diagnostic and do not gate archive)
**Risks**: Three untested-but-likely-safe spec scenarios (profile completeness invariant, profile offline cache read, invoice tenant isolation on GET-by-id) — recommend a small follow-up test addition, not a blocker.

## 5. Resolution after verify

- WARNINGs 1–3 (profile completeness, Factura tenant isolation on `GET /invoicing/invoices/{id}`, profile offline read) were all coverage gaps; the behavior was already correct. Tests added in `38a6fdf`, each confirmed RED against a temporarily broken production file.
- SUGGESTION (offline print on the print routes themselves): checked in the real browser instead. Offline, the Factura's detail and both print routes render from the persisted cache. No dedicated test was added, because the routes share `useInvoice` with the already-tested detail screen.
- Test Value Gate over every new phase A test:
  - The two issuance-level concurrency tests could only fail if the fiscal-profile mutex and `allocate`'s guarded `UPDATE` both broke; removing either one alone left them green. They were rewritten to drive `allocate` directly (`2e4faf0`).
  - The letter print test echoed its `@page` literal. It now asserts that no page size is forced (`10c97b1`).
- Real-browser check on the demo (390×844) found four defects the suites could not see, all fixed and re-checked on the redeployed demo:
  - the printed issuance time was the raw UTC ISO string (`557dc00`);
  - the 58 mm line table overflowed the paper width (`15af9b6`);
  - the issue dialog had no "Cancelar" (`c5563cf`);
  - the issuer phone printed unformatted (`596f2dc`).
- Seed rerun reported María Hernández as edited by a tester. Fixed in `95e6064`; two reruns now add nothing.
- Rollback drill on a scratch copy of the demo:
  - The guarded downgrade refuses while Facturas exist, and goes through with `-x discard_fiscal_documents=demo`.
  - The drill also exposed a pre-existing restore bug: `taller_unaccent_lower` resolved `unaccent` through `search_path`, which a `pg_dump` restore empties. Fixed by migration `1a57ba6a8108` (`556fe78`).
- Checks at `556fe78`: pytest 371 passed; ruff check and format clean; eslint, tsc and vitest (237) clean; build succeeded.
- Still open: none for phase A. Real (non-demo) invoicing stays off-limits until phase B ships and a contador reviews a printed sample of both layouts (PA.S12.T9).

---

# Verify report — sar-invoicing, Phase B (PB.S1–PB.S8)

**Change**: `sar-invoicing` — Phase B (PB.S1–PB.S7 + PB.S8 review-fixes slice)
**Store**: openspec · **Branch**: `feat/sar-invoicing-phase-b` (from `main`) · **Scope**: phase B only, per request; phase A requirements re-checked as still passing

## 1. Executed checks (all re-run live, not read from prior records)

| Command | Result |
|---|---|
| `docker compose up -d db` | container running |
| `cd api && uv run ruff check .` | All checks passed! |
| `cd api && uv run ruff format --check .` | 145 files already formatted |
| `cd api && uv run pytest -q` | 400 passed |
| `cd web && npm run lint` | clean, exit 0 |
| `cd web && npm run typecheck` | clean, exit 0 |
| `cd web && npm test -- --run` | 62 test files, 261 passed |
| `cd web && npm run build` | succeeded (tsc -b && vite build, PWA precache generated) |

All results match tasks.md's own recorded evidence exactly (400 API tests at PB.S8.T4, 261 web tests at PB.S6.T4/PB.S5.T3). No drift between claimed and observed state. Since this is one combined suite (not phase-filtered), phase A's own tests ran in the same execution and passed, confirming phase A requirements still pass alongside phase B.

## 2. Task-completion state (observed, not rewritten)

Read `openspec/changes/sar-invoicing/tasks.md` in full (468 lines). Slices **PB.S1–PB.S8 are all checked `[x]`** except the three explicitly deferred closing tasks, exactly matching the request's "expected pending items":

- `PB.S7.T7` — deploy phase B to the demo (done after verify, see section 6)
- `PB.S7.T8` — real-browser check at 390×844 on the deployed demo (done after verify, see section 6)
- `PB.S7.T9` — re-verify after any T8 fixes (depends on T8)

No other unchecked box exists in phase B. `git log --oneline main..feat/sar-invoicing-phase-b` shows **8 commits**, one per slice's work-unit commit, matching tasks.md's claimed hashes exactly: `e236d2f` (PB.S1), `fc4c364` (PB.S2), `5d06118` (PB.S3), `98ea0a5` (PB.S4), `b7fab87` (PB.S5), `4b037bc` (PB.S6), `feb8ff0` (PB.S7), `1feefce` (PB.S8). Working tree is clean.

## 3. Spec scenario → test mapping (phase B specs only)

Confirmed that `fiscal-invoices`, `fiscal-profile`, `work-orders`, `customers` carry **no Phase B deltas** — phase A fully, unaffected by this scope. Phase B touches exactly `credit-notes` (new) plus deltas on `cai-ranges`, `data-export`, `fiscal-document-print`.

**`credit-notes` (new capability, 10 requirements):** every scenario has a near-literal test in `api/tests/invoicing/test_credit_notes_api.py` (13 tests) plus `test_credit_note_concurrency.py` (2 tests):

| Scenario | Test |
|---|---|
| A full credit note references its original Factura | `test_a_full_credit_note_references_its_original_factura` |
| A credit note with no reason is rejected | `test_a_credit_note_with_no_reason_is_rejected` |
| No active document-type-06 range blocks issuance | `test_no_active_06_range_blocks_credit_note_issuance` |
| An exhausted document-type-06 range blocks issuance | `test_an_exhausted_06_range_blocks_issuance` |
| A second credit note against the same Factura is rejected | `test_a_second_credit_note_against_the_same_factura_is_rejected` |
| Replaying / reusing id with different payload | `test_replaying_an_identical_credit_note_is_a_noop`, `test_reusing_the_credit_note_id_for_a_different_invoice_is_a_conflict` |
| Lines editable again / new Factura may be issued | `test_lines_become_editable_again_after_a_full_credit_note` |
| Re-invoicing a delivered, fully credited order | `test_a_delivered_fully_credited_order_may_be_reinvoiced_with_corrected_buyer_data` |
| No effect on payments or stock | `test_a_credit_note_has_no_effect_on_payments_or_stock` |
| Editing customer leaves reprint unchanged | `test_editing_the_customer_after_a_credit_note_leaves_it_unchanged_on_reprint` |
| Another workshop's credit note is invisible | `test_another_workshops_credit_note_is_invisible` |
| (implicit) bogus invoice id | `test_a_bogus_invoice_id_is_not_found` |
| (implicit) concurrency / row locking | `test_two_concurrent_credit_notes_against_one_factura_credit_it_exactly_once` + PB.S8's `test_the_invoice_row_lock_alone_serializes_two_racers_checking_credited_at` |

Web-side offline requirement, read directly: `CreditNoteDialog.tsx`'s `handleSubmit` gates on `isOffline || trimmedReason.length === 0` before any request, the submit button carries `disabled={isOffline || ...}`, and an `Alert` shows `invoicingCopy.offline.issueCreditNoteDisabled` — covered by `CreditNoteDialog.test.tsx` (4 tests). "A previously fetched credit note renders offline" → `CreditNoteDetailPage.test.tsx`'s offline test (read directly: seeds `QueryClient` with `creditNoteQueryKey`, serves network errors, asserts the heading still renders).

Order-detail document list / re-issuance affordance (AD-15, exercising `credit-notes`' own lock-release requirement) → `InvoiceSection.test.tsx`'s three tests (read directly, all passing): lists a credited Factura with its credit note; offers "Emitir factura" again after full credit; offers "Emitir nota de crédito" for a non-credited Factura.

**`cai-ranges` delta (Phase B):**
- "A credit-note range is rejected before Phase B" is **correctly superseded**: the spec itself states "From Phase B, `06` is accepted as well," and the test was deliberately flipped (D2) into `test_a_credit_note_range_is_accepted_in_phase_b` (read directly, confirmed passing, 201 with `document_type: "06"`).
- "A warning appears exactly 60 days before..." / "No warning appears more than 60 days out" / "A low-remaining-numbers warning..." → `test_a_fecha_limite_warning_appears_exactly_60_days_before`, `test_no_fecha_limite_warning_appears_more_than_60_days_out`, `test_a_low_numbers_warning_appears_at_the_threshold` (plus 3 extra genuine boundary/suppression tests in `test_range_warnings.py`).
- UI rendering → `RangeWarnings.test.tsx` (3 tests, read directly: exact Spanish text assertions) plus `IssueInvoiceDialog.test.tsx`/`CreditNoteDialog.test.tsx` each asserting the warning line appears without blocking submit.
- PB.S8's fix regression test, read directly: `test_editing_an_untouched_credit_note_range_succeeds` — registers a `06` range, PATCHes only `issue_deadline`, asserts 200 (previously 422).

**`data-export` delta (Phase B):** every scenario has a literal test in `api/tests/export/test_export_api.py` (read directly, all present and passing): `test_the_export_contains_exactly_one_csv_per_entity` (extended to 10 files), `test_a_workshop_that_never_invoiced_anything_still_gets_empty_fiscal_csvs`, `test_invoice_lines_reflect_the_snapshot_not_the_orders_current_lines`, `test_customers_csv_carries_billing_name_and_rtn_empty_when_absent`, plus `test_a_credit_notes_csv_row_references_its_invoice`, `test_fiscal_invoices_csv_lists_only_the_current_workshops_documents` (tenant isolation), `test_a_credit_note_reason_starting_with_equals_is_escaped` (formula-injection guard).

**`fiscal-document-print` delta ("Credit Note Layouts Carry Every Art. 25–26 Mandatory Field"):** read `CreditNoteDocument.tsx`, `CreditNote58Page.tsx`, `CreditNoteLetterPage.tsx` end to end. Every field the design's "Printed field map" Nota de Crédito column and the research note's Art. 25–26 list name is present on both layouts: issuer fields, "NOTA DE CRÉDITO" name, its own CAI/rango/fecha límite, number, issuance date/time (`America/Tegucigalpa`), buyer name/RTN or "CONSUMIDOR FINAL", the original Factura's CAI/number/date reference, the reason, gravado 15%/ISV 15%/total in numbers and words (correctly omitting exento/exonerado/discount/lines per the field map's own "—" cells), blank "Firma"/"Identidad" lines, both copy-destination legends, and the demo watermark. `CreditNoteDocument.test.tsx` (3 tests) plus `CreditNote58Page.test.tsx`/`CreditNoteLetterPage.test.tsx` (3 tests) cover this directly. **No gap found.**

## 4. Findings

**CRITICAL: 0 · WARNING: 0 · SUGGESTION: 1**

No CRITICAL or WARNING findings specific to phase B. The two review findings already identified and fixed in PB.S8 were independently re-derived from source and confirmed fixed: `update_range` (`api/src/taller/invoicing/application/use_cases.py:444`) no longer raises `UnsupportedDocumentType` for any document type, and the new seam test isolating the invoice-row lock exists alongside the original concurrency test. Phase A's own three historical WARNINGs were already resolved per its own verify report; the full suite confirms no regression.

**SUGGESTION (diagnostic only):** the credit-note concurrency coverage still cannot structurally isolate the order-row lock from the invoice-row lock in the end-to-end case — by design, since a credit note's invoice always belongs to exactly one order. This is a structural property, not a gap, and PB.S8's seam test already isolates the invoice-row lock independently. No action recommended.

## 5. Summary

All checks green (400 API tests, 261 web tests, lint/format/typecheck/build clean). Every phase B spec scenario across `credit-notes` and the `cai-ranges`/`data-export`/`fiscal-document-print` deltas maps to a real, behavior-driving test, confirmed by reading test bodies directly. Every mandatory Art. 25–26 credit note field reaches the snapshot and both print layouts. Phase B is functionally complete pending only the three deferred closing steps (demo deploy, real-browser/print-preview check, its re-verify) — deployment/manual-check steps, not implementation gaps.

## 6. Resolution after verify

- **Missed by verify, flagged during PB.S3: range states across document types (PB.S9, `9e36df6`).** `get_settings` derived range states over both document types at once, so a usable `01` range and a usable `06` range competed for one `active` slot and one showed as standby, while its own registration response said active. Readiness was already per type, so issuance was never affected. Fixed with a RED test; on the deployed demo both ranges now show "Activo".
- **Found by the browser check: offline explanation (PB.S10, `5acd953`).** Offline, "Emitir factura" and "Emitir nota de crédito" were disabled with no reason shown: the message lived only inside the dialogs, which a disabled button can never open. The Factura case dated from phase A. Fixed with RED tests and re-checked on the demo.
- **Test value pass (PB.S11, `e368290`).** Of 60 new tests, three could not be turned red by any single implementation change. One was rewritten to build its own spec premise (a recorded payment and a consumed part) and proven red under two injected defects; the other two were removed as redundant, with the guards they appeared to cover tested elsewhere. This also settles the SUGGESTION in section 4: the end-to-end race it described is gone, and the invoice-row lock keeps its own seam test. The `credit-notes` concurrency scenario is now covered by that seam test plus the sequential "second credit note is rejected" test; the "never invoiced" export scenario by `test_the_export_contains_exactly_one_csv_per_entity` and `test_csv_zip.py`'s header-only test.
- **Demo deploy and seed (PB.S7.T7).** Deployed and seeded twice; the second run created nothing. Rollback drill on a copy of the post-seed dump: the downgrade refuses while a credit note exists, passes with the demo flag, and upgrades back.
- **Browser and print check (PB.S7.T8).** Passed at 390×844 on the demo, including both credit note print layouts (every Art. 25–26 field, no overflow at 58 mm, no forced page size on letter) and the ten-CSV export. The lines unlock/relock cycle and the range warnings were checked on a scratch workshop in the local dev stack, since every demo order is delivered and the demo ranges are far from both thresholds.
- **Re-verification (PB.S7.T9).** API 399 passed; web 264 passed in 62 files; lint, format, typecheck and build clean.
