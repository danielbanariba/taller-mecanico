# Proposal: SAR invoicing (opt-in Factura and Nota de Crédito from work orders)

Projects touched: **api** and **web** in both phases, plus `deploy/demo/` (seed script and runbook).

Every fiscal rule below cites `docs/research/notas/_research-sar-facturacion.md` (the "research note"); article numbers refer to the consolidated Reglamento of Acuerdo 481-2017 unless marked CT (Código Tributario). The research note is not legal advice: a Honduran contador must confirm the module before any workshop issues real invoices with it. The exploration is `openspec/changes/sar-invoicing/exploration.md`.

## Intent

The roadmap's next step after the workshop core is "SAR/CAI invoicing as an opt-in module (CAI range, RTN, ISV 15% breakdown, HNL only)" (`odd/tasks/inventory-mvp-rebuild.md:26`).

- **The gap is real and unserved.** No competitor found, local or imported, covers inventory, quotes and CAI together (`docs/research/Necesidades de talleres en Honduras.md:13-26`). A workshop that already has its CAI keeps a second tool, or a print shop's paper invoice book, next to this app.
- **It must stay opt-in.** The same research warns that CAI "no debe ser la puerta de entrada": most target shops do not have a CAI yet, so invoicing must never gate inventory, quotes or work orders (`Necesidades…md:28-30`). A workshop that never opts in keeps today's behavior, including the non-fiscal receipt, unchanged.
- **The regime allows it without any SAR integration.** A web app can operate as an autoimpresor "sistema computarizado" (Art. 50, 51): the workshop files a Declaración Jurada that the system meets Art. 53, requests its own CAI per document type (Art. 47, 59, 61), and types it into the app. Electronic invoicing is not mandatory today (Art. 57), so there is no clearance API to build.
- **Getting it wrong has a real cost.** Issuing a document without its legal requirements is a falta formal sanctioned with temporary closure of the establishment (CT Art. 149–150, 159–161). Correctness of every mandatory field is the core of this change, not a polish item.

**Why now:** work orders, payments, the receipt print pattern, per-workshop numbering, tenancy and the export already exist, and the regulation has been read from the primary text.

**Success looks like:** a workshop owner enters the fiscal data and CAI ranges once, then issues a correctly numbered, fully detailed Factura from a completed order on a phone, prints it on 58 mm or letter paper, corrects a mistake with a Nota de Crédito, never issues past the range or its fecha límite, and finds every fiscal document in "Exportar todo".

## Scope

Two phases, **one PR per phase**. Phase B builds on phase A. Each phase deploys to the public demo and extends `deploy/demo/seed-demo-account.sh` idempotently.

### In Scope

**Phase A: fiscal profile, CAI ranges, buyer RTN, Factura issuance, print and order lock**

- **Fiscal profile** (one per workshop): RTN, razón social, nombre comercial, address, phone, email, establecimiento code and punto de emisión code (Art. 10–11). Reached from the shell's "Más" menu; online-only writes; workshop-scoped.
- **Opt-in by data:** invoicing stays disabled until the profile is complete and an active CAI range exists for the document type. The app never contacts SAR.
- **In-app notice** on the settings screen: the workshop must register the system with SAR and file the Declaración Jurada (Art. 47, 53), must confirm with its contador, and needs thermal paper certified for 5-year legibility if it prints on 58 mm (Art. 38).
- **CAI ranges** per document type (`01` in this phase): CAI, range start and end, fecha límite de emisión. Overlapping ranges of one type are rejected; a range is immutable once a number has been taken from it.
- **Range enforcement:** issuance is blocked when the range is exhausted or its fecha límite has passed (Art. 62), comparing the `America/Tegucigalpa` calendar date through the injectable `Clock`, the fecha límite day itself included.
- **Customer billing data:** optional RTN and billing name (razón social) on the customer, prefilled at issuance and editable there.
- **Factura issuance** from a `completed` or `delivered` order:
  - one non-credited Factura per order, for the order's full amount;
  - online-only, idempotent by client-generated id: a replay returns the same document and consumes no number;
  - a gap-free correlative from the active range, allocated under a row lock, formatted `NNN-NNN-01-NNNNNNNN` (Art. 10–11);
  - buyer "CONSUMIDOR FINAL" by default, or the buyer's name and RTN; a consumidor final from L 10,000 must be identified (Art. 10–11);
  - all lines gravado 15%, with the base and ISV split out of the tax-inclusive total (D1);
  - an immutable snapshot of issuer, CAI, range, fecha límite, number, date, buyer, lines, breakdown, total, and total in words in Spanish, so a later edit to the profile, customer or order never changes a reprint (Art. 53.2–53.3).
- **Invoiced-order lock:** while an order has a non-credited Factura, its line add, edit and remove are rejected, and cancellation stays impossible.
- **Print:** 58 mm (measured `@page` height) and letter layouts on their own routes outside the shell, reusing the receipt's layout pattern but not `ReceiptBody`, each carrying every Art. 10–11 field, the total in words, and the original-to-customer and copy-to-issuer destinations.
- The demo seed adds a fiscal profile, a range and one issued Factura (see open question 3).

**Phase B: Notas de Crédito, export and range warnings**

- **Nota de Crédito** (`06`, Art. 4.32, 25–26) from an issued Factura: full amount only, referencing the original's CAI, correlative and date, with the buyer name and RTN, a required reason, the total in numbers and in words. It needs its own CAI range of type `06` (Art. 59, 61), allocated and enforced exactly like Facturas.
- Once the Factura is fully credited, the order's lock lifts and the order may be invoiced again. A Factura can be credited only once.
- **Print** of the credit note in both layouts, including blank signature and ID lines for whoever receives it (Art. 25–26).
- **Export:** invoices and credit notes CSVs in the existing ZIP.
- **Range warnings:** from 60 days before the fecha límite, matching Art. 59's 2-month window for requesting a new range, and when few numbers remain (threshold fixed by `sdd-design`).
- The demo seed adds one credit note.

### Out of Scope

- SAR text-file generation (Art. 53.5); the format is unknown (research note, "Still open").
- The monthly notification of unused or invalid documents (Art. 42).
- The "ANULADA" action (Art. 41); every v1 correction is a Nota de Crédito.
- Several establecimientos or puntos de emisión per workshop.
- Nota de Débito (`07`, Art. 27–28).
- Exento and exonerado amounts, the 18% rate, exonerated buyers' document data, and discounts other than zero (Art. 10–11).
- Partial invoicing and partial credit notes.
- Electronic invoicing / CAEE (Art. 4.22, 57) and the optional barcode (Art. 53.4).
- Tickets (Art. 4.27, 52).
- Sending the document by WhatsApp or email; Art. 14.5 mandates no channel.
- Offline issuance, any edit to an issued document, libro de ventas or ISV return filing, multi-currency, and multi-user roles.
- Any change to order totals, payments, balances, the daily cash summary, stock consumption or the non-fiscal receipt.

## Capabilities

### New Capabilities

- `fiscal-profile` (A): the workshop's fiscal data, its validation, the data-driven opt-in gate, the SAR registration notice, the entry point from the shell's "Más" menu, online-only writes and tenancy.
- `cai-ranges` (A, warnings in B): registering ranges per document type, overlap and immutability rules, active-range selection, gap-free correlative allocation under a lock, exhaustion and fecha límite blocking (Art. 62), and the warnings (Art. 59).
- `fiscal-invoices` (A): Factura issuance from an eligible order, buyer rules including the L 10,000 identification (Art. 10–11), the ISV split (D1), the immutable snapshot, number format, idempotency, tenancy, and reads.
- `fiscal-document-print` (A, credit note layout in B): the 58 mm and letter layouts and every mandatory printed field for both document types.
- `credit-notes` (B): full-amount credit notes against an issued Factura, their own range, reference fields, reason, single-credit rule, idempotency, and the lock release.

### Modified Capabilities

- `work-orders` (A, lock release in B): a new invoiced-order lock. Line add, edit and remove are rejected with HTTP 409 and a new code (for example `work_order_invoiced`) while the order has a non-credited Factura, and `lines_editable` reports `false`. Status changes from `completed` to `delivered` and the order's own fields stay allowed. "Order And Line Totals Are Computed In Lempiras From Final Line Prices" (`openspec/specs/work-orders/spec.md:91-100`) is **not** modified: per D1 the order response still carries no tax amount.
- `customers` (A): optional RTN and billing name, validated when present; the idempotent-creation payload comparison and the edit include them.
- `data-export` (B): "The Export Produces A ZIP Of Per-Entity CSVs" gains invoices and credit notes files.

**Not modified:** `non-fiscal-receipt`, `payments`, `daily-cash-summary`, `work-order-stock-consumption`, `vehicles`, `whatsapp-sharing`, `app-shell-navigation` (its spec does not specify the "Más" menu, so the new entry is specified in `fiscal-profile`). The receipt's Purpose sentence ("SAR/CAI fiscal invoicing is out of scope for this entire change") will read as dated once this ships; `sdd-archive` may reword it without a requirement change.

## Approach

**API: a new hexagonal feature** (working name `taller.invoicing`; `sdd-design` fixes the name and boundary).

- `domain/`: fiscal profile, CAI range, Factura, Nota de Crédito, the document number value object, the ISV split, and total in words in Spanish, all pure and unit-tested.
- `application/`: use cases and `Protocol` ports; `adapters/`: SQLAlchemy repositories, schemas and the router mounted in `taller/main.py`.
- The fiscal profile is its own table keyed by `workshop_id`, so identity's `Workshop` and `WorkshopRepository` stay untouched and a workshop that never opts in has no row.
- **Dependency on work orders.** Invoicing reads an order's status, lines and customer through `workorders` application functions, one way only. The lock is checked in `workorders` either through a schema-only reference by table name (the precedent of `inventory_movements` pointing at `work_orders`) or a `workorders`-owned port. `sdd-design` picks one and records it as an architecture decision.

**ISV split (D1).** Prices entered on lines already include 15% ISV. At issuance the invoice derives the base and the ISV from the order total, in integer cents, and the printed gravado plus ISV equals the total exactly. Whether ISV is computed on the total or per line, and whether a line's printed unit value is tax-inclusive, is left to `sdd-design`.

**Numbering.**

- `workshop_counters` is unbounded and has no expiry, so it is not reused.
- Each `cai_ranges` row holds its next correlative and is locked `FOR UPDATE` at issuance. The bound, the fecha límite and the allocation are checked under that one lock.
- Errors are English codes (for example `cai_range_exhausted`, `cai_range_expired`, `invoicing_not_configured`); Spanish messages live in `copy.ts`.

**Issuance flow.** In one transaction:

1. Lock the order row; line edits take the same lock, so no edit lands between the snapshot and the lock.
2. Check eligibility: status `completed` or `delivered`, a complete profile, no non-credited Factura, and the buyer rules.
3. Lock the active range and allocate the correlative.
4. Write the snapshot.

An exact replay of the client id returns the stored document; a different payload is a 409.

**Web.**

- A new `web/src/features/invoicing/` holds the settings screen (profile, ranges, notice), the issuance dialog on the order detail, the document detail, the credit note flow, and lazy print routes outside the shell (siblings of `<AppShell>` under `RequireSession`, like the receipts).
- `customers` gains the RTN and billing name fields; the order detail shows "Emitir factura" only when invoicing is configured and the order is eligible, and links to the issued document otherwise.
- Every Spanish string, including legends such as "CONSUMIDOR FINAL", "ORIGINAL: CLIENTE" and "COPIA: EMISOR", lives in `copy.ts`.

**Offline boundary.** Every new write is online-only, like payments. Reads (profile, ranges, issued documents) use the persisted query cache with `workshopQueryKey`-prefixed keys, so an issued document can be reopened offline. The outbox is untouched.

**Postgres hygiene.** Explicit indexes on every FK and `workshop_id`; partial unique indexes (for example one non-credited Factura per order) declared on the models with `postgresql_where` so `alembic check` sees them; `ON DELETE RESTRICT` everywhere, because fiscal documents are never deleted (Art. 5, 41, 43). The new customer columns are nullable, a metadata-only change.

**Delivery.** One PR per phase; both exceed the 400-line review budget, so under `ask-on-risk` the orchestrator asks for the chain strategy before applying each phase.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `api/src/taller/invoicing/{domain,application,adapters}/` | New (A, B) | Fiscal profile, CAI ranges, Facturas, credit notes, number format, ISV split, total in words, router |
| `api/src/taller/workorders/{application/use_cases.py,adapters/repositories.py,adapters/schemas.py,adapters/router.py,domain/errors.py}` | Modified (A, B) | Invoiced-order line lock, `lines_editable`, shared order-row lock with issuance, lock release on full credit |
| `api/src/taller/customers/{domain,application,adapters}/` | Modified (A) | Optional RTN and billing name, validation, idempotency payload |
| `api/src/taller/export/adapters/{sources.py,router.py}` | Modified (B) | Invoices and credit notes CSVs |
| `api/src/taller/main.py` | Modified (A) | Mount the invoicing router |
| `api/migrations/versions/*.py` | New (A, B) | One migration per phase, each with a working `downgrade()` |
| `api/tests/{invoicing,workorders,customers,export}/` | New/Modified | Domain unit tests (split, words, number), API tests on real Postgres, numbering and lock concurrency tests |
| `web/src/features/invoicing/` | New (A, B) | Settings, ranges, issuance, document detail, print routes, credit notes, `copy.ts` |
| `web/src/features/customers/` | Modified (A) | RTN and billing name in forms and detail |
| `web/src/features/workorders/WorkOrderDetailPage.tsx` | Modified (A, B) | Issue or open the Factura; respect the lock |
| `web/src/app/router.tsx`, `web/src/app/AppShell.tsx` | Modified (A) | Settings route, print routes, "Más" menu entry |
| `web/src/test/handlers.ts` | Modified (A, B) | MSW handlers for every new endpoint |
| `deploy/demo/seed-demo-account.sh`, `deploy/demo/README.md` | Modified (A, B) | Idempotent fiscal seed; document what the demo contains |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| The workshop's Declaración Jurada states Art. 53 compliance while v1 lacks the Art. 53.5 text files | High | Open question 1; no real workshop issues invoices until a contador confirms; follow-up research on the format |
| A missing or wrong mandatory field exposes a workshop to closure (CT Art. 159–161) | Med | One rendering assertion per Art. 10–11 and Art. 25–26 field on both layouts; contador review of a printed sample before real use |
| Concurrent issuance skips or duplicates a correlative | Med | Range row lock; concurrency test like the counter and stock-lock tests; replays never consume a number |
| A line edit commits between the snapshot and the lock | Med | Issuance and line edits serialize on the same order-row lock; concurrency test |
| A one-cent mismatch between gravado, ISV and total | Med | Integer cents; the rounding rule fixed in design with property-style tests over many totals |
| Issuing on or after the fecha límite because of a UTC boundary | Med | `America/Tegucigalpa` date through the injectable `Clock`; tests at the day boundary (Art. 62) |
| Rolling back destroys documents that must be kept (Art. 5, 41, 43) | Med | See the rollback plan: never downgrade a database holding real documents |
| The public demo prints documents that look like real facturas | Med | Open question 3 (watermark and fictional CAI) |
| The 15% rate is wrong for some line (an exemption the PwC inference missed) | Low | Recorded as an assumption; exento/exonerado deferred; contador confirmation |
| Phase A has no correction path until phase B ships | Med | Open question 2: phase A goes to the demo only |
| Migration drift on partial unique indexes | Med | Declare them on the models; `alembic check` in every phase |
| Test surface grows (MSW fails on unmocked requests) | Med | One handler per new endpoint; SAVEPOINT `db_session` for every repository test |

## Rollback Plan

The demo database (`taller-demo-db`) is separate from the dev database, and today the demo is the only deployment, so every fiscal document in it is fictional. Each phase follows the archived procedure:

1. **Before deploying:** dump the demo database (`docker exec taller-demo-db pg_dump -U taller taller_demo > taller_demo-<phase>.sql`) and record `alembic current` and the deployed commit.
2. **Rollback on the demo:** with the phase's code checked out, `uv run --frozen --env-file ~/.config/taller-mecanico/demo.env alembic downgrade <previous revision>`, then `git checkout --detach <previous commit>` in the demo worktree, rebuild the web with `demo.env`, and restart both units. On `main`, revert the phase's merge commit.
3. **Order:** phase B rolls back before phase A.
4. **Any database holding real fiscal documents:** never run the downgrade. Revert the code only and keep the tables, so documents stay available for custody (Art. 5, 41, 43); the opt-in disappears with the UI, and a forward fix follows.
5. **Client side:** older builds never read the new query keys, logout clears them, and the service worker auto-updates. The outbox is untouched.

Phase effects: phase A's `downgrade()` drops the invoices, ranges and profile tables and the customer RTN columns; orders, payments, stock and receipts are unaffected, because the lock is derived from the invoices table. Phase B's `downgrade()` drops the credit notes table; the export returns to seven files. Each `downgrade()` is exercised locally (upgrade, downgrade, upgrade) before its PR is opened.

## Dependencies

- Phase B requires phase A, merged and deployed.
- Existing: `workorders` (status, lines, payments), `customers`, `taller.export`, the receipt print pattern, the injectable `Clock`, `get_current_workshop_id`, the demo seed idiom.
- No new runtime dependency is expected; total in words is a small in-house function. If design proposes a library, it must be justified there.
- Outside the app: each workshop's own SAR registration and CAI (Art. 47, 53, 61) and a contador's review.

## Size Forecast (rough, authored lines = additions + deletions, tests included)

| Phase | API | Web | Seed/docs | Total | ≈400-line slices |
|------|-----|-----|-----------|-------|------------------|
| A: profile, ranges, RTN, Factura, print, lock | ~2,600 (incl. ~1,200 tests) | ~2,400 (incl. ~900 tests) | ~120 | **~4,800–5,600** | ~12–14 |
| B: credit notes, export, warnings | ~1,300 (incl. ~600 tests) | ~1,300 (incl. ~500 tests) | ~60 | **~2,500–3,000** | ~6–8 |

`sdd-tasks` produces the exact forecast and guard lines.

## Decisions

| # | Decision | Status | Basis |
|---|----------|--------|-------|
| D1 | Line prices include 15% ISV; the invoice splits base and ISV out of the final amount. Order totals, payments and balances are unchanged, and the order response still carries no tax amount. | Decided by the user | Art. 10–11 breakdown; `work-orders/spec.md:91-100` |
| D2 | v1 documents are Factura (`01`) and Nota de Crédito (`06`); Nota de Débito is out. | Decided by the user | Art. 4.32, 25–28 |
| A1 | Opt-in by data: a complete fiscal profile plus an active range per document type; the app never contacts SAR; the workshop obtains its own CAI. | Assumption, confirm | Art. 47, 53, 59, 61 |
| A2 | One establecimiento and one punto de emisión per workshop. | Assumption, confirm | Art. 59 |
| A3 | One Factura per order, full amount, from a `completed` or `delivered` order; online-only; idempotent client id; gap-free correlative under a row lock. | Assumption, confirm | Art. 10–11 |
| A4 | All lines gravado 15%; exento, exonerado and 18% out of v1; rounding rule left to design. | Assumption, confirm | Research note, "Tax rates" |
| A5 | Buyer "CONSUMIDOR FINAL" by default; optional RTN and billing name stored on the customer and editable at issuance; a consumidor final from L 10,000 must be identified. | Assumption, confirm | Art. 10–11 |
| A6 | Every correction is a full-amount Nota de Crédito referencing the original; no "ANULADA" in v1; a fully credited order unlocks; partial credit notes are a follow-up. | Assumption, confirm | Art. 4.32, 25–26, 41, 42 |
| A7 | Issued documents are immutable snapshots; while an order has a non-credited Factura, line edits and cancellation are blocked. | Assumption, confirm | Art. 53.2–53.3; Art. 5, 43 |
| A8 | Block issuance when the range is exhausted or past its fecha límite; warn from 60 days before and when few numbers remain. | Assumption, confirm | Art. 59, 62 |
| A9 | 58 mm and letter layouts with every mandatory field, the total in words and the original/copy destinations. | Assumption, confirm | Art. 10–11, 38 |
| A10 | Invoices and credit notes CSVs in the existing export. | Assumption, confirm | Art. 53.3 |
| A11 | In-app notice: register the system and file the Declaración Jurada, confirm with a contador, certified thermal paper. | Assumption, confirm | Art. 38, 47, 53 |
| A12 | The out-of-scope list above (Art. 53.5 files, Art. 42 notification, multiple points, Nota de Débito, exento/exonerado, partial documents, CAEE). | Assumption, confirm | Art. 27–28, 42, 53.5, 57 |
| A13 | Two phases, one PR each: A as listed, B as listed. | Assumption, confirm | Dependencies above |

## Open Questions

**Product decisions (for the user; each has a recommended answer).**

1. **Art. 53.5 and real use.** Can a workshop truthfully file the Declaración Jurada (Art. 53) while v1 cannot generate SAR text files (Art. 53.5)? *Recommended:* keep Art. 53.5 out of v1, but no real workshop issues invoices with the app until a contador confirms; research the text-file format as its own follow-up change.
2. **Phase A without corrections.** Phase A can issue a Factura but cannot correct one, since the Nota de Crédito is the only legal correction after issuance (Art. 4.32, 25–26). *Recommended:* phase A ships to the demo only, and real issuance waits for phase B. The alternative is moving credit notes into phase A, which makes that PR larger.
3. **Fiscal documents on the public demo.** *Recommended:* the demo build marks every fiscal document "DEMOSTRACIÓN — SIN VALOR FISCAL" (driven by the same build-time demo configuration as the prefilled account) and seeds an obviously fictional profile and CAI.
4. **What "identified" means from L 10,000** (Art. 10–11). *Recommended:* require the billing name and RTN, compared against the invoice total with ISV included; the contador confirms whether another identity document suffices.
5. **Re-invoicing a fully credited `delivered` order.** Its lines stay locked by the existing `delivered` rule. *Recommended:* keep that rule; such an order may be re-invoiced with corrected buyer data only, and amount corrections on delivered orders are deferred.
6. **Issuing before full payment.** *Recommended:* allowed; the Factura records the sale, payments stay independent and are not printed on it.
7. **The non-fiscal receipt for an invoiced order.** *Recommended:* it stays available, unchanged; the order detail shows the Factura action first.
8. **Credit note side effects.** *Recommended:* none on payments or stock; a refund is recorded by voiding payments through the existing flow.
9. **Zero-value fields on print** (exento, exonerado, descuentos; Art. 10–11). *Recommended:* print them as L 0.00; the contador confirms.
10. **RTN format.** The verified note gives none; the market research says 14 digits (`Necesidades…md:30`). *Recommended:* exactly 14 digits after stripping separators, with no check-digit validation in v1.
11. **Invoice lines in the export.** *Recommended:* add a third CSV with the snapshot lines, because the order lines CSV shows current lines, not what was invoiced.

**Design questions (for `sdd-design`).**

- ISV rounding: on the total or per line, and whether a printed line unit value is tax-inclusive (D1, Art. 10–11).
- The invoicing package boundary and how `workorders` checks the lock without an import cycle.
- The snapshot schema, and generating the total in words server-side so reprints never change.
- Range selection: pre-registering the next range (Art. 59), overlap rules, the low-numbers threshold.
- How original and copy are produced: one print job with both copies, or a destination legend per copy.
- Whether establecimiento and punto de emisión codes may change while an unexhausted range exists (recommended: no, since a CAI is per punto de emisión, Art. 59).
- Whether an order's own fields (complaint, odometer, notes) stay editable while invoiced (recommended: yes, they are not printed).

## Success Criteria

Each criterion is covered by automated tests and observable on the public demo after the phase is deployed and seeded.

**Phase A**

- [ ] A workshop with no fiscal profile sees no invoicing action on any order, and its orders, payments, receipts and export behave exactly as before.
- [ ] After saving a complete profile and a Factura range, a completed order offers "Emitir factura". Issuing assigns the range's first correlative in `NNN-NNN-01-NNNNNNNN` form, and a double submit returns the same document without consuming a second number.
- [ ] An order totaling L 1,150.00 yields an invoice whose gravado 15% and ISV add up to exactly L 1,150.00, with the total in words; the order's own response still has no tax field.
- [ ] A consumidor final invoice from L 10,000 without buyer identification is rejected with a Spanish message.
- [ ] Issuance is rejected once the range is exhausted, and once the fecha límite has passed in `America/Tegucigalpa`; it succeeds on the fecha límite day itself.
- [ ] On an invoiced `completed` order, line add, edit and remove are rejected with a 409, while moving it to `delivered` and recording a payment still work.
- [ ] Editing the fiscal profile or the customer after issuance leaves the reprinted invoice unchanged.
- [ ] Both layouts render every Art. 10–11 field, including "Factura", the CAI, rango autorizado, fecha límite and both copy destinations.
- [ ] Another workshop's invoice is a 404; concurrent issuance in one workshop never skips or duplicates a correlative.
- [ ] `alembic check`, ruff, pytest, eslint, typecheck, vitest and build pass, and `downgrade()` succeeds locally.

**Phase B**

- [ ] With a range of type `06`, a full credit note against a Factura references its CAI, number and date, requires a reason, and prints with signature and ID lines in both layouts.
- [ ] After the credit note, the order's lines are editable again if it is `completed`, and a new Factura can be issued; a second credit note against the same Factura is rejected.
- [ ] "Exportar todo" contains invoices and credit notes CSVs with only the current workshop's documents.
- [ ] The settings screen warns from 60 days before a range's fecha límite and when its remaining numbers fall below the design threshold.
