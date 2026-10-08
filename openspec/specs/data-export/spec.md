# Data Export Specification

**Phase:** 3

## Purpose

A one-tap "Exportar todo" export of the current workshop's data as a ZIP of per-entity CSVs, so a shop owner is never forced to stay on the product to keep access to their own data. This is read-only and introduces no new entity of its own; it composes existing per-feature data scoped exactly like every other inventory query.

## Requirements

### Requirement: The Export Produces A ZIP Of Per-Entity CSVs

The system MUST produce a single ZIP archive containing one CSV file per entity: customers, vehicles, items, inventory movements, work orders, work order lines, payments, invoices, invoice lines, and credit notes.

The invoices CSV holds every issued Factura's own snapshot fields (issuer data, CAI, number, buyer, breakdown, and total as recorded at issuance), not recomputed from the live order, profile, or customer. The invoice lines CSV holds the snapshot's line-level detail (description, quantity, unit value) separately from the work order lines CSV, because an order's current lines may no longer match what was actually invoiced (for example, after a full credit note reopened the order for editing). The credit notes CSV holds every issued Nota de Crédito, including its reference to the original Factura.

(Previously: the ZIP contained exactly seven entities — customers, vehicles, items, inventory movements, work orders, work order lines, and payments — with no fiscal documents, since fiscal invoicing did not exist.)

#### Scenario: The export contains one file per entity

- GIVEN a workshop with data in every entity listed above
- WHEN "Exportar todo" is requested
- THEN the resulting ZIP contains exactly one CSV file for each of: customers, vehicles, items, inventory movements, work orders, work order lines, payments, invoices, invoice lines, and credit notes

#### Scenario: An entity with no rows still produces an (empty-body) CSV

- GIVEN a workshop with no recorded payments
- WHEN "Exportar todo" is requested
- THEN the ZIP still contains a payments CSV with only a header row

#### Scenario: A workshop that never invoiced anything still gets empty fiscal CSVs

- GIVEN a workshop with no fiscal profile, no CAI ranges, and no issued invoices or credit notes
- WHEN "Exportar todo" is requested
- THEN the ZIP still contains invoices, invoice lines, and credit notes CSVs, each with only a header row

#### Scenario: Invoice lines reflect the snapshot, not the order's current lines

- GIVEN a work order with an issued Factura, whose lines were edited after a full credit note reopened the order for editing
- WHEN "Exportar todo" is requested
- THEN the invoice lines CSV shows the lines as they were at the moment the Factura was issued, not the order's current lines

### Requirement: The Payments CSV Includes All Payments, Voided And Non-Voided, With Void Metadata

The system MUST export every recorded payment in the `payments.csv` file, including both non-voided and voided payments. Voided payments MUST NOT be deleted or hidden; they MUST appear as records with their `voided_at` timestamp and `void_reason` filled, while non-voided payments have those fields empty. The `paid_hnl` value in `work_orders.csv` counts only non-voided payments and therefore differs from the sum of all amounts in the payments CSV.

#### Scenario: A voided payment is exported with its void metadata

- GIVEN a work order with a recorded payment of 200.00 that was later voided with reason "duplicado"
- WHEN "Exportar todo" is requested
- THEN the payments CSV contains one row for that payment
- AND its columns include `voided_at` (a timestamp) and `void_reason` ("duplicado")
- AND that payment does not contribute to the `paid_hnl` total in the work_orders CSV

#### Scenario: Non-voided payments have empty void columns

- GIVEN a work order with a recorded, non-voided payment
- WHEN "Exportar todo" is requested
- THEN the payments CSV contains one row for that payment
- AND its `voided_at` column is empty
- AND its `void_reason` column is empty

### Requirement: Every CSV Is UTF-8 With A BOM For Excel Compatibility

The system MUST encode every CSV in the export using UTF-8 with a byte-order mark (`utf-8-sig`), so that Excel on Windows renders Spanish accented characters correctly instead of mojibake.

#### Scenario: Accented content survives a round trip through Excel

- GIVEN a customer named `José Núñez` exists in the workshop
- WHEN the customers CSV from the export is opened in Excel on Windows
- THEN `José Núñez` renders with its accent and tilde intact, not as mojibake

### Requirement: The Export Is Scoped Only By The Authenticated Workshop

The system MUST scope every row in every CSV by the authenticated user's workshop id (`get_current_workshop_id`), and MUST NOT accept or honor any client-supplied workshop id for scoping the export.

#### Scenario: Export contains only the requesting workshop's data

- GIVEN workshop A and workshop B each have customers, vehicles, items, and orders
- WHEN a user authenticated for workshop A requests "Exportar todo"
- THEN every row in every CSV belongs to workshop A
- AND no row from workshop B appears anywhere in the ZIP

#### Scenario: A client-supplied workshop id is ignored

- GIVEN a user authenticated for workshop A
- WHEN an export request attempts to pass a different workshop id as a parameter
- THEN the export still scopes exclusively to workshop A, the authenticated workshop

### Requirement: The Export Requires A Live Connection

The system MUST require an active connection to generate and download the export; it is not served from the persisted offline query cache or any other client-side store.

#### Scenario: Export is unavailable offline

- GIVEN the device has no network connection
- WHEN the user triggers "Exportar todo"
- THEN a Spanish message explains that exporting requires a connection
- AND no partial or stale export is downloaded

### Requirement: Repeating An Export Is Side-Effect Free

The system MUST treat every export request as a read: requesting "Exportar todo" any number of times MUST produce a fresh read of the workshop's current data and MUST NOT create, modify, or delete any record.

#### Scenario: Two consecutive exports reflect the same state unchanged

- GIVEN no writes occur between two export requests
- WHEN "Exportar todo" is requested twice in a row
- THEN both ZIPs contain the same rows
- AND no database record was created, modified, or deleted by either request

### Requirement: Each CSV Is Internally Consistent; Consistency Across Files Under Concurrent Writes Is Best-Effort

The system MUST produce every CSV in the export as one internally consistent read of its own entity's rows: a CSV MUST NOT contain a partial row, a duplicated row, or a row reflecting two different states of the same record. When no write occurs to any entity while an export is in progress, every CSV in the resulting ZIP MUST reflect that one same moment. When a write does occur to one entity while a different entity's CSV is being produced, the two CSVs MAY reflect slightly different moments; the export MUST NOT be required to hold one transactional snapshot across every entity to satisfy this capability.

#### Scenario: No writes during the export yields one consistent moment across every file

- GIVEN no writes occur to any entity while the export is in progress
- WHEN the export finishes
- THEN every CSV in the ZIP reflects that same moment in time

#### Scenario: A write to one entity during the export does not corrupt another entity's file

- GIVEN a write to the payments table happens while the export is being generated
- WHEN the export finishes
- THEN the payments CSV may or may not include that write
- AND every CSV's own rows remain internally consistent, with no partial or duplicated row

### Requirement: The Customers CSV Includes The Optional Billing Name And RTN

The customers CSV MUST include each customer's optional `billing_name` and `rtn` columns. They hold the normalized values the customer record stores now, and are empty when the customer has none. These are the live customer values; what a given Factura actually printed lives only in the invoices CSV's own snapshot.

#### Scenario: A customer's billing data is exported

- GIVEN a customer with billing name "Repuestos El Sol S. de R.L." and RTN `08011990123456`, and another customer with neither
- WHEN "Exportar todo" is requested
- THEN the customers CSV carries that billing name and RTN on the first customer's row
- AND both columns are empty on the second customer's row
