# Delta for Data Export

**Phase:** B

## MODIFIED Requirements

### Requirement: The Export Produces A ZIP Of Per-Entity CSVs

The system MUST produce a single ZIP archive containing one CSV file per entity: customers, vehicles, items, inventory movements, work orders, work order lines, payments, invoices, invoice lines, and credit notes. The invoices CSV holds every issued Factura's own snapshot fields (issuer data, CAI, number, buyer, breakdown, and total as recorded at issuance), not recomputed from the live order, profile, or customer. The invoice lines CSV holds the snapshot's line-level detail (description, quantity, unit value) separately from the work order lines CSV, because an order's current lines may no longer match what was actually invoiced (for example, after a full credit note reopened the order for editing). The credit notes CSV holds every issued Nota de Crédito, including its reference to the original Factura.

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

## ADDED Requirements

### Requirement: The Customers CSV Includes The Optional Billing Name And RTN

The customers CSV MUST include each customer's optional `billing_name` and `rtn` columns. They hold the normalized values the customer record stores now, and are empty when the customer has none. These are the live customer values; what a given Factura actually printed lives only in the invoices CSV's own snapshot.

#### Scenario: A customer's billing data is exported

- GIVEN a customer with billing name "Repuestos El Sol S. de R.L." and RTN `08011990123456`, and another customer with neither
- WHEN "Exportar todo" is requested
- THEN the customers CSV carries that billing name and RTN on the first customer's row
- AND both columns are empty on the second customer's row
