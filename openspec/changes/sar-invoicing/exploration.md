## Exploration: sar-invoicing (opt-in SAR Factura 01 and Nota de Crédito 06 from work orders)

Fiscal rules below come from `docs/research/notas/_research-sar-facturacion.md` (the "research note"), which summarizes the consolidated Reglamento of Acuerdo 481-2017 and the Código Tributario (CT). Article numbers refer to the Reglamento unless marked CT. The note is not legal advice; a Honduran contador must confirm the module before any workshop issues real invoices with it.

### Current State

**Regulation (what the module must satisfy).**

- **Modality.** A web app can only be an autoimpresor "sistema computarizado" (Art. 50, 51). Tickets are a separate document type reserved for a registered máquina registradora, so the app must issue Facturas (Art. 4.27, 4.43, 52). Electronic invoicing (CAEE) is a medio of autoimpresor and is not mandatory today (Art. 4.9, 4.22, 57).
- **System requirements (Art. 53).** Integration with an accounting or inventory system (53.1), security and audit controls (53.2), persistence and immediate availability of current and historical transactions (53.3), an optional 2D/3D barcode (53.4), and text files for SAR (53.5). There is no software certification: the taxpayer files a Declaración Jurada that its system meets Art. 53, and registers each system, server and punto de emisión (Art. 47, 53). The taxpayer, not the software provider, requests authorization (Art. 61).
- **CAI.** One CAI per punto de emisión and document type (Art. 59), or per system and document type for a sistema computarizado (Art. 61). Validity is at most one year, and after the fecha límite de emisión documents are invalid whatever range remains (Art. 62). A new range may be requested once the current one is exhausted, or within the 2 months before its fecha límite (Art. 59).
- **Always issue.** The under-L 50 exception does not apply to autoimpresor issuers (Art. 9).
- **Factura content (Art. 10–11).** Issuer RTN, name or razón social, nombre comercial, address, phone and email; the word "Factura"; the CAI, rango autorizado and fecha límite de emisión; the destination of each copy (original to the customer, copy to the issuer). Number `NNN-NNN-NN-NNNNNNNN` (establecimiento, punto de emisión, document type `01`, correlative), which restarts at `00000001` after `99999999`. At issuance: buyer name and RTN (or the legend "CONSUMIDOR FINAL"), the date, each line's description, quantity and unit value, the breakdown exento / exonerado / gravado by tarifa with the tax per tarifa, currency (L), the total in numbers and in words, and discounts. From L 10,000 a consumidor final must be identified.
- **Corrections.** "ANULADA" applies to an error caught before delivery, keeping both copies (Art. 41). Reversals, returns and later discounts after issuance need a Nota de Crédito, type `06` (Art. 4.32, 25–26). It references the original's CAI, correlative and date, and carries the buyer name and RTN, the reason, the total in numbers and words, and the signature and ID of whoever receives it. A Nota de Débito is type `07` (Art. 27–28).
- **Reporting.** Unused or invalid documents (expiry, data change, theft, technical failure, and others) are reported to SAR within the first 10 business days of the next month (Art. 42).
- **Print and custody.** No minimum paper size; thermal paper only if legibility for at least 5 years is certified (Art. 38). No mandated delivery channel for an absent customer (Art. 14.5). Copies, including voided ones, are kept for the CT prescription period and must be available to SAR (Art. 5, 41, 43).
- **Penalties.** Issuing without the legal requirements is a falta formal sanctioned with temporary closure and a fine scaled to income (CT Art. 149–150, 159–161).
- **Tax rate.** The Reglamento only asks for a breakdown "por tarifa o alícuota"; per PwC (secondary) the general ISV rate is 15%, and the note infers, without checking the Ley del ISV, that no exemption covers auto repair labor or parts.
- **Superseded claim.** An older note (`docs/research/notas/_research-honduras-local.md`) said a mandatory nationwide e-invoicing rollout was in progress. The verified note contradicts it (Art. 57; vatupdate, Aug 2026), and the verified note governs this change.

**API.**

- **Workshop.** `Workshop` has only `id`, `name`, `created_at` (`api/src/taller/identity/domain/entities.py:11`, `adapters/models.py:12-19`). `WorkshopRepository` has only `get_by_id`/`add`, no update path (`identity/application/ports.py:21-24`). Nothing fiscal exists.
- **Money.** `order_total_cents` (`api/src/taller/workorders/domain/money.py:13-19`) sums `quantity * unit_price_cents` over non-removed lines, with no tax anywhere. This is archived design AD-10 (`openspec/changes/archive/2026-10-07-workshop-core/design.md:256`) and a MUST in `openspec/specs/work-orders/spec.md:91-100` ("no tax amount is present anywhere in the response").
- **Numbering.** `workshop_counters` is a gap-free, unbounded per-workshop named counter (`INSERT … ON CONFLICT DO UPDATE … RETURNING`, `api/src/taller/workorders/adapters/repositories.py:33-47`; Protocol at `application/ports.py:12-21`). It has no start, end or expiry.
- **Status and locks.** The six-state table is acyclic; `completed` and `delivered` cannot be cancelled (`openspec/specs/work-orders/spec.md:102-161`). Lines stay editable in `completed` and lock in `delivered`/`cancelled` with `work_order_locked` (`spec.md:163-192`). `WorkOrderOut.lines_editable` is `order.status in EDITABLE` (`api/src/taller/workorders/adapters/schemas.py:317`). Cancelling an order with non-voided payments raises `WorkOrderHasPayments` (`application/use_cases.py:238-241`, `domain/errors.py:96`).
- **Payments.** Allowed in `approved`, `in_progress`, `completed`, `delivered`; paid and balance are always derived (`openspec/specs/payments/spec.md`).
- **Customer.** `full_name`, optional `phone`, `notes`; no RTN or razón social (`api/src/taller/customers/domain/entities.py:18-34`, `web/src/features/customers/api.ts:3-12`).
- **Export.** `taller.export` builds an in-memory ZIP of `utf-8-sig` CSVs, one source function per entity in `adapters/sources.py` plus one router dict entry; the baseline spec fixes the seven files (`openspec/specs/data-export/spec.md:11-25`).
- **Conventions.** Tenancy through `get_current_workshop_id`; idempotent creates by client-generated id (replay is a no-op, a different payload is 409); every non-movement write is online-only; English error codes, Spanish copy in `copy.ts`; `alembic check` drift test (`api/tests/test_migrations.py`); injectable `Clock` and `America/Tegucigalpa` day boundaries (daily cash summary).

**Web.**

- The non-fiscal receipt (`web/src/features/workorders/receipt/`) is gated to `completed`/`delivered` (`useReceiptOrder.ts`), renders outside the app shell, measures its own height for a 58 mm `@page`, and uses `@page { margin: 12mm }` for letter/A4. Its spec scopes fiscal invoicing out (`openspec/specs/non-fiscal-receipt/spec.md:7`).
- There is no settings screen; the auth `Workshop` type is `{id, name}` (`web/src/features/auth/api.ts:10-13`). The shell's "Más" menu (Caja del día, Exportar todo, Cerrar sesión) is the natural entry point for workshop-level screens.

### Affected Areas

- **API, new feature:** `api/src/taller/invoicing/{domain,application,adapters}/` for the fiscal profile, CAI ranges, invoices and credit notes (package name fixed by design).
- **API, modified:** `api/src/taller/customers/` (optional RTN and billing name), `api/src/taller/workorders/` (invoiced-order line lock, `lines_editable`), `api/src/taller/export/adapters/{sources.py,router.py}` (new CSVs), `api/src/taller/main.py` (mount the router), `api/migrations/versions/*.py`.
- **Web, new feature:** `web/src/features/invoicing/` (settings screen, range management, issuance flow, document detail, print routes, credit note flow), with `api.ts`, `copy.ts`, `hooks.ts`.
- **Web, modified:** `web/src/features/customers/` (RTN fields), `web/src/features/workorders/WorkOrderDetailPage.tsx` (issue/view invoice), `web/src/app/router.tsx` and the shell's "Más" menu, `web/src/test/handlers.ts`.
- **Demo:** `deploy/demo/seed-demo-account.sh`, `deploy/demo/README.md`.
- **Unchanged:** identity's `Workshop`/`WorkshopRepository` (the fiscal profile is its own table), the outbox, the stock ledger, `ReceiptBody`.

### Approaches / Open Decisions

#### 1. Where the ISV breakdown comes from

- **(a) Treat entered prices as tax-inclusive and split at issuance.** No change to lines, totals, payments or the work-orders spec; the breakdown lives only on the invoice.
- **(b) Add a tax-exclusive price mode on lines.** Breaks `work-orders/spec.md:91-100`, needs a migration of every line and dual-mode UI.

**Decided by the user (D1):** (a). Still open for `sdd-design`: whether ISV is computed once on the invoice total or per line and summed, and whether the printed line unit value is the entered (tax-inclusive) amount or the base. The constraint is that the printed gravado plus ISV must equal the order total exactly, in integer cents.

#### 2. Fiscal profile and the opt-in gate

- **(a) A `fiscal_profiles` table in the invoicing feature, one row per workshop.** Identity stays untouched; a workshop that never opts in has no row and sees no change.
- **(b) Columns on `workshops`.** Needs a new update path in identity and nullable fiscal columns on every tenant.
- **(c) An explicit enable toggle.** Adds a state that can disagree with the data.

**Recommendation:** (a), with a data-driven gate: issuing is possible only when the profile is complete and an active range exists for the document type. The app never talks to SAR; the workshop types in its CAI.

#### 3. Bounded, gap-free correlative

- **(a) Reuse `workshop_counters` with a new name.** Unbounded, no expiry, no link to a CAI; a range change would need a reset that breaks the counter's contract.
- **(b) A `cai_ranges` row per authorized range holding `next_correlative`, locked `FOR UPDATE` at issuance.** The number, the range bounds and the fecha límite are checked under the same lock; an idempotent replay returns the existing document and consumes nothing.

**Recommendation:** (b). Ranges carry their document type (`01` or `06`), CAI, start, end and fecha límite; overlapping ranges of the same type are rejected; a range becomes immutable once a number has been taken from it. Whether a next range can be pre-registered and picked up automatically (Art. 59 allows requesting it within 2 months of the fecha límite) is for `sdd-design`; the recommendation is yes.

#### 4. What an issued document stores

- **(a) Render from the live order, customer and profile.** A later edit to any of them silently changes a reprint.
- **(b) An immutable snapshot at issuance:** issuer data, CAI, range, fecha límite, number, date, buyer, lines, breakdown, total and total in words.

**Recommendation:** (b). It is the only way to satisfy immutability and Art. 53.3, and it makes reprints exact. Total in words is computed server-side and stored, so a later change to the words function never alters a reprint.

#### 5. Package boundary and the invoiced-order lock

Payments block cancellation because they live inside `workorders`. Invoicing needs to read an order (status, lines, customer) and `workorders` needs to know whether an order is invoiced, which would be an import cycle.

- **(a) Invoicing inside `workorders`, like payments.** No cycle, but the feature package grows a second domain.
- **(b) A separate `taller.invoicing` package that calls `workorders` application functions (one-way), with the lock checked by `workorders` through a schema-only reference by table-name string,** the same precedent as `inventory_movements` pointing at `work_orders` without a Python import.
- **(c) As (b), but the lock is a `workorders`-owned Protocol port implemented by an invoicing adapter.**

**Recommendation:** (b) or (c), decided by `sdd-design`, recorded as an architecture decision. Issuance and line edits must serialize on the same order row lock so a line edit cannot commit between the snapshot and the lock.

Note: because invoices are only issued from `completed`/`delivered`, and neither can be cancelled, the cancellation guard is already structurally true. The lock that matters is line add/edit/remove in `completed`.

#### 6. Corrections: ANULADA versus Nota de Crédito

- **ANULADA (Art. 41)** is only for an error caught before delivery, and a voided document must then be reported under Art. 42, which is out of v1.
- **Nota de Crédito (Art. 4.32, 25–26)** is the legal path after issuance.

**Decided by the user (D2):** Factura and Nota de Crédito only; no Nota de Débito. Proposed default: every correction is a full-amount credit note referencing the original; once fully credited, the order unlocks and may be invoiced again. Credit notes need their own CAI range of type `06` (Art. 59, 61).

#### 7. Buyer data

- Default "CONSUMIDOR FINAL". Optional buyer RTN and billing name stored on the customer, prefilled at issuance and editable there; the values used are snapshotted on the invoice.
- From L 10,000 a consumidor final must be identified (Art. 10–11). What counts as "identified" is not defined in the note; open question.
- RTN format: the market research says 14 digits (`docs/research/Necesidades de talleres en Honduras.md:30`), but the verified note does not state a format or check digit; open question.

#### 8. Printing

New routes outside the shell, reusing the receipt's pattern (measured 58 mm `@page`, letter with margins), never `ReceiptBody`. Each layout carries every Art. 10–11 field and the original/copy destinations; credit notes add the Art. 25–26 fields, including blank signature and ID lines for the receiver. Thermal paper must be certified for 5-year legibility (Art. 38), which belongs in the in-app notice.

#### 9. Range enforcement

Block issuance when the range is exhausted or its fecha límite has passed, compared as an `America/Tegucigalpa` calendar date through the injectable `Clock`, inclusive of the fecha límite day (Art. 62). Warn from 60 days before the fecha límite, matching Art. 59's 2-month window, and when few numbers remain (threshold for `sdd-design`).

#### 10. Export

Add invoices and credit notes CSVs to the ZIP, following the `sources.py` pattern. Whether snapshot lines need their own CSV is open; recommended yes, since the order lines CSV reflects current lines, not what was invoiced.

### Architecture decisions flagged for sdd-design

- The invoicing package boundary and the direction of its dependency on `workorders` (approach 5), as an explicit decision like the archived work-orders to inventory call.
- The ISV split and rounding rule (approach 1).
- The snapshot schema and where total in words is generated (approach 4).
- Range selection, pre-registration, overlap rules and the low-numbers threshold (approaches 3 and 9).
- How original and copy are produced on print (one job with both copies or a destination legend per copy).

### Risks

- **Art. 53.5 gap.** v1 does not generate SAR text files, yet the workshop's Declaración Jurada states the system meets Art. 53. A contador must confirm whether that is acceptable before real use.
- **Legal exposure from bugs.** A missing mandatory field is a falta formal with temporary closure (CT Art. 159–161). Every mandatory field needs a rendering test, and the layouts need contador review.
- **Numbering races.** Concurrent issuance in one workshop must never skip or duplicate a correlative; a concurrency test like the counter and stock-lock tests.
- **Lock races.** A line edit committing during issuance would make the snapshot disagree with the order.
- **Rounding.** A one-cent mismatch between the breakdown and the total is a visible error on a legal document.
- **Retention versus rollback.** Issued documents must be kept (Art. 5, 41, 43), so a schema downgrade on a database with real documents is not an acceptable rollback.
- **Demo misuse.** The public demo could print documents that look like real facturas.
- **Tax inference.** The 15%-on-everything assumption rests on PwC plus an unverified inference about exemptions.

### Ready for Proposal

Yes. D1 and D2 are decided by the user; every other choice has a recommendation marked as an assumption to confirm, and the remaining unknowns are listed as open questions in the proposal.
