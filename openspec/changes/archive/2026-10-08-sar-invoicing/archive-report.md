# Archive Report: sar-invoicing

**Archived**: 2026-10-08  
**Status**: Complete  
**Change**: sar-invoicing (fiscal profiles, CAI ranges, Factura and Nota de Crédito issuance, fiscal document print layouts, customer billing data, work-order invoicing lock, export enhancements)

---

## Executive Summary

The `sar-invoicing` change is archived. Both phases (Phase A: Factura issuance and supporting infrastructure, Phase B: Nota de Crédito and export integration) have been merged to main (PR #22 phase A on 2026-10-05, PR #23 phase B on 2026-10-07, merge commit 62ff317). Five new capability specifications have been promoted from the change folder to the baseline specs directory, and three deltas have been folded into existing baseline specs. All tests pass and the implementation is production-ready for the demo. One known follow-up remains open: real (non-demo) invoicing awaits a contador's review of printed samples of both Factura and Nota de Crédito layouts before production use.

---

## Artifacts Archived

| Artifact | Status | Location |
|---|---|---|
| `proposal.md` | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/proposal.md` |
| `exploration.md` | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/exploration.md` |
| `design.md` | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/design.md` |
| `tasks.md` | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/tasks.md` |
| `verify-report.md` | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/verify-report.md` |
| `specs/` (8 change specs, 5 new + 3 deltas) | Present | `openspec/changes/archive/2026-10-08-sar-invoicing/specs/` |

---

## Specs Promoted to Main Baseline

Five new capability specifications have been promoted from delta specs to the main baseline at `openspec/specs/`:

1. **fiscal-profile** (Phase A): One optional fiscal profile per workshop, holding issuer data per SAR Art. 10–11 (RTN, razón social, nombre comercial, address, phone, email, establecimiento code, punto de emisión code), and the data-driven opt-in gate for invoicing.

2. **cai-ranges** (Phase A, extended Phase B): CAI ranges authorized per document type (`01` Factura in Phase A, added `06` Nota de Crédito in Phase B), with row-locked correlative allocation, exhaustion and fecha-límite enforcement, and range warnings (Phase B).

3. **fiscal-invoices** (Phase A): Factura issuance from completed or delivered orders, with buyer identification rules, tax split, immutable snapshots, idempotent issuance, and order-line lock.

4. **fiscal-document-print** (Phase A, extended Phase B): Two independent print layouts (58 mm thermal and full-page letter) for fiscal documents, carrying every SAR mandatory field, with Phase B adding Nota de Crédito layouts.

5. **credit-notes** (Phase B): Nota de Crédito issuance for full-amount corrections of issued Facturas, with lock release to allow re-invoicing, immutable snapshots, and Phase B range allocation.

---

## Spec Deltas Folded Into Main Baseline

Three deltas have been folded into existing baseline specs:

### 1. Customers — Billing Name And RTN Fields

**Source**: New fields added in Phase A for fiscal issuance; `openspec/changes/sar-invoicing/specs/customers/spec.md` "ADDED Requirements".

**Folded into**: `openspec/specs/customers/spec.md` — One new requirement "Customer Billing Name And RTN Are Optional And Validated When Present" with five scenarios:
- An RTN with separators is accepted and normalized to 14 digits
- An RTN with the wrong digit count is rejected with HTTP 422 `invalid_rtn`
- Billing name and RTN are both optional
- Billing name and RTN are editable independently of phone
- Billing name and RTN participate in create idempotency like any other field

Marked `**Phase:** A` in the baseline.

### 2. Work Orders — Invoiced-Order Line Lock

**Source**: Phase A requirement preventing line edits while a non-credited Factura exists; `openspec/changes/sar-invoicing/specs/work-orders/spec.md` "ADDED Requirements".

**Folded into**: `openspec/specs/work-orders/spec.md` — One new requirement "Line Edits Are Rejected While The Order Has A Non-Credited Factura" with five scenarios:
- Adding a line to an invoiced, completed order is rejected with HTTP 409 `work_order_invoiced`
- `lines_editable` reports `false` while invoiced, even for completed status
- Moving an invoiced order to `delivered` is still allowed
- Editing the order's own fields (`notes`, etc.) is still allowed while invoiced
- Line edits are allowed again once the Factura is fully credited by a Nota de Crédito

Marked `**Phase:** A` in the baseline.

### 3. Data Export — Fiscal Document CSVs And Customer Billing Columns

**Source**: Phase B enhancements adding invoices, invoice lines, and credit notes CSVs; `openspec/changes/sar-invoicing/specs/data-export/spec.md` "MODIFIED Requirements" and "ADDED Requirements".

**Folded into**: `openspec/specs/data-export/spec.md`:
- **Modified** "The Export Produces A ZIP Of Per-Entity CSVs": now lists ten entities (added invoices, invoice lines, credit notes); clarifies that invoices and invoice lines hold immutable snapshots, not live order data; includes two new scenarios ("A workshop that never invoiced anything still gets empty fiscal CSVs" and "Invoice lines reflect the snapshot, not the order's current lines").
- **Added** "The Customers CSV Includes The Optional Billing Name And RTN": customers CSV includes `billing_name` and `rtn` columns (empty when absent), reflecting live customer values; marked `**Phase:** A` in the baseline.

---

## Open and Unfinished Work

### Follow-up: Real (Non-Demo) Invoicing Approval

**Status**: Blocked pending external review  
**Description**: The sar-invoicing implementation is complete and deployed to the demo at https://inventario-taller.danielbanariba.com, with both Factura (`01`) and Nota de Crédito (`06`) full functionality. Production deployment awaits explicit approval from a Honduras-based contador (tax accountant) after reviewing printed samples of:
- Factura 58 mm thermal layout
- Factura full-page letter layout
- Nota de Crédito 58 mm thermal layout
- Nota de Crédito full-page letter layout

The demo automatically watermarks all documents as "DEMOSTRACIÓN — SIN VALOR FISCAL" and is safe for indefinite demo use. Production requires the contador review before enabling real document issuance.

**Evidence**: Verify report Phase B section 6 ("Real (non-demo) invoicing stays off-limits until phase B ships and a contador reviews a printed sample of both layouts").

---

## Merge Commits

Both phases have been merged to the main branch:

| Phase | PR | Merge Commit | Date |
|---|---|---|---|
| Phase A: Fiscal profile, CAI ranges, Factura, print | PR #22 | `7a6c5d2` | 2026-10-05 |
| Phase B: Nota de Crédito, range warnings, export, print | PR #23 | `62ff317` | 2026-10-07 |

Both merges are to `main` with no feature branch remaining active. Implementation is complete.

---

## Task Completion Summary (from tasks.md)

**Phase A**: PA.S1–PA.S13 all checked `[x]` except three deferred closing steps (demo deploy, real-browser/print check, and their re-verify) — all now complete.

**Phase B**: PB.S1–PB.S8 all checked `[x]` except three deferred closing steps (demo deploy, real-browser/print check, and their re-verify) — all now complete.

**Total**: 171 tasks completed across both phases. Zero blocked or unresolved implementation tasks. The one follow-up work (contador review for production approval) is external, not a product implementation gap.

---

## Verification Summary (from verify-report.md)

### Phase A
- All automated checks pass: `ruff check/format`, `pytest` (371 passed), eslint, tsc, `vitest` (237).
- 3 WARNING findings (coverage gaps), 1 SUGGESTION, 0 CRITICAL. All warnings were resolved post-verify with tests added.
- Real-browser check on demo (390×844) at `556fe78` found and fixed four defects: printed issuance time format, 58 mm line overflow, missing "Cancelar" button, unformatted issuer phone.
- Rollback drill confirmed: migration `downgrade()` refuses while Facturas exist, passes with `-x discard_fiscal_documents=demo`, and the full round-trip (down/up) succeeds.

**Recommendation**: Functionally complete. All findings resolved.

### Phase B
- All automated checks pass: `ruff check/format`, `pytest` (399 passed), eslint, tsc, `vitest` (265).
- 0 CRITICAL, 0 WARNING, 1 SUGGESTION (structural property, no action needed). Phase A's three historical warnings remain resolved.
- Real-browser check on the demo (390×844) verified both Nota de Crédito layouts and the ten export CSVs; the lines unlock/relock cycle and the range warnings were checked on a scratch workshop in the local dev stack (every demo order is delivered, and the demo ranges are far from both thresholds). The seed reruns without creating anything.
- Rollback drill confirmed: migration `downgrade()` refuses while credit notes exist, passes with the demo flag.

**Recommendation**: Functionally complete. Production-ready for demo. External contador review required for production deployment (see "Open and Unfinished Work").

---

## Specification Reconciliation: Phase Statements Folded

The baseline specs describe the shipped system, so every phase-qualified or design-dependent statement was replaced by what the design fixed and the code does:

1. **cai-ranges**: registration accepts both `01` and `06`; the phase A scenario "A credit-note range is rejected before Phase B" became "Registering a credit-note range". The active range is the usable one with the earliest fecha límite, then the lowest range start, then its id (AD-4; `_selection_key` in `api/src/taller/invoicing/domain/ranges.py`). The warnings use 60 days before the latest usable fecha límite and 50 or fewer remaining numbers summed over the usable ranges, per document type, never blocking issuance (AD-18; `EXPIRY_WARNING_DAYS`, `LOW_NUMBERS_THRESHOLD`).
2. **fiscal-invoices**: the tax split is computed once on the invoice total, `(200·T + 115) // 230`, with tax-inclusive printed line values (AD-8; `split_tax_inclusive_total` in `api/src/taller/invoicing/domain/tax.py`).
3. **fiscal-document-print**: both copies print in one job, the issuer's copy on its own page on the letter layout, with "Solo original" dropping it for a reprint (AD-16).
4. **Phase markers**: the `**Phase:**` line at the top of each spec stays, as in the `workshop-core` baselines; the ones the deltas carried inside individual requirements (customers, work-orders, data-export, cai-ranges) were removed.

---

## Open Discrepancies: Code vs. Spec

None. Every phase-qualified or design-dependent statement was folded into the shipped behavior (see the section above), and no spec statement was found to contradict the code.

One reviewer note, not a defect: `SqlAlchemyFiscalInvoiceRepository.mark_credited` (`api/src/taller/invoicing/adapters/repositories.py`) updates a Factura by id alone, unlike its sibling methods. It is safe today because its only caller, `issue_credit_note` (`api/src/taller/invoicing/application/use_cases.py`), first loads and locks that Factura with `invoice_repo.get_for_update(workshop_id=..., invoice_id=...)` and stops if it is not found, so the id it later updates always belongs to the session's workshop. Adding the `workshop_id` filter to `mark_credited` itself would keep it safe if a second caller appears.

---

## Traceability

All artifacts preserved in the archive:
- `proposal.md`: Product intent, scope, and two-phase approach.
- `exploration.md`: Honduras tax research (SAR/CAI Art. references, field maps, vendor comparisons).
- `design.md`: 20+ architecture decisions, state machines, data models (schema per phase, immutability guards, migration/downgrade), API surface, and web architecture.
- `tasks.md`: 171 tasks (all completed) with completion evidence (commits, test counts, real-browser observations).
- `verify-report.md`: Verification findings and resolution details for both phases, including coverage gaps, test value gate pass, and real-device defects found and fixed.
- `specs/`: 8 change specs (5 new capabilities, 3 deltas on existing) used to drive implementation.

All observation IDs for findings, decisions, and test adjustments are preserved within the archived documents.

---

## Archive Completion Checklist

- [x] Main specs updated correctly (5 new capabilities created; 3 deltas folded into existing specs)
- [x] Phase-qualified statements folded into final state (baseline specs now describe shipped behavior)
- [x] Change folder moved to archive (git mv successful, no diff after move)
- [x] Archive preserves all artifacts (proposal, design, tasks, verify, specs present)
- [x] Archived artifacts retain original bytes (shell copy + git mv only, no Read/Write truncation)
- [x] Active changes directory cleaned (no sar-invoicing/ remains in openspec/changes/)
- [x] Specs folded correctly (deltas merged with acceptance of phase-specific behavior as final)
- [x] References updated (deploy/demo/README.md and CLAUDE.md)

---

## Summary

Both phases of sar-invoicing have been merged to main and the implementation is functionally complete. Automation tests all pass (API 399, web 265), real-browser checks on the demo found and fixed four defects, and the migration round-trip (down/up) succeeds. Five new capability specs and three deltas have been promoted to the baseline. One external follow-up remains: a Honduras contador must review and approve printed samples of both document layouts before production deployment. The demo is safe for indefinite use and accurately represents the final feature.
