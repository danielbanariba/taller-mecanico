# Fiscal Document Print Specification

**Phase:** A

## Purpose

Printable layouts for an issued fiscal document — a Factura in Phase A, a Nota de Crédito from Phase B — reusing the non-fiscal receipt's print pattern (a measured 58 mm thermal layout and a full-page layout) without reusing `ReceiptBody` itself, since a fiscal document's mandatory fields (Art. 10–11, and Art. 25–26 for credit notes) differ from the receipt's. Printing never mutates anything; it only renders an already-issued, immutable document.

## Requirements

### Requirement: Two Independent Printable Layouts Exist For Each Fiscal Document

The system MUST provide two independently rendered printable layouts for an issued fiscal document — a 58 mm thermal layout and a full-page layout — each its own route outside the app shell, under `RequireSession`, following the receipt's `@page` pattern: the 58 mm layout measures its own rendered content height to size `@page`, falling back to a reasonable default height until that measurement resolves; the full-page layout only sets print margins.

#### Scenario: The 58 mm layout renders in print preview

- GIVEN an issued Factura
- WHEN its 58 mm print route is opened and print preview is invoked
- THEN the page renders at 58 mm width with the document's content legible

#### Scenario: The full-page layout renders in print preview

- GIVEN an issued Factura
- WHEN its full-page print route is opened and print preview is invoked
- THEN the page renders at a standard page size with the document's content legible

#### Scenario: Printing before the 58 mm measurement resolves still produces a valid page

- GIVEN the 58 mm layout has just mounted and its content height has not yet been measured
- WHEN print preview is invoked at that instant
- THEN the page still renders at a valid 58 mm width with a fallback page height

### Requirement: Both Layouts Carry Every Art. 10–11 Mandatory Field Of A Factura

Both layouts MUST render, for an issued Factura: the issuer's RTN, razón social, nombre comercial, address, phone, and email; the word "Factura"; the CAI, rango autorizado, and fecha límite de emisión; the Factura's own number; the buyer's name and RTN or the legend "CONSUMIDOR FINAL"; the issuance date; each line's description, quantity, and unit value; the exento/exonerado/gravado breakdown with the ISV for the gravado tarifa; the currency "L"; the total in numbers; the total in words in Spanish; and any discount.

#### Scenario: Every mandatory field is present on both layouts

- GIVEN an issued Factura
- WHEN either print layout is rendered
- THEN every field listed above is present in the rendered output

### Requirement: Both Copy Destinations Are Printed

Both layouts MUST mark which copy is which: the original, destined for the customer, and the copy, destined for the issuer (Art. 10–11).

> **Design-dependent:** whether one print job renders both copies, or the same layout carries a destination legend toggled per copy, is fixed by `sdd-design`. The scenario below holds either way.

#### Scenario: Both destinations appear in the printed output

- GIVEN an issued Factura
- WHEN it is printed
- THEN an original-to-customer destination marking and a copy-to-issuer destination marking are both present somewhere in the printed output

### Requirement: Zero-Value Fields Print As L 0.00, Never Blank Or Omitted

When the exento, exonerado, or discount amounts are zero, both layouts MUST render them as "L 0.00", never as a blank field or an omitted row.

#### Scenario: A Factura with no exento, exonerado, or discount amounts still prints them as zero

- GIVEN an issued Factura whose exento, exonerado, and discount amounts are all zero
- WHEN either print layout is rendered
- THEN each of those fields shows "L 0.00"

### Requirement: The Demo Build Watermarks Every Fiscal Document As Non-Fiscal

Both layouts, when rendered from a demo build, MUST display "DEMOSTRACIÓN — SIN VALOR FISCAL" prominently on the printed document, driven by the same build-time demo configuration that prefills the demo account (`VITE_DEMO_PHONE`/`VITE_DEMO_PASSWORD`). A non-demo build MUST NOT display this watermark.

#### Scenario: The demo build shows the watermark

- GIVEN a build compiled with the demo configuration
- WHEN an issued Factura is printed
- THEN "DEMOSTRACIÓN — SIN VALOR FISCAL" is visible on the printed output

#### Scenario: A non-demo build shows no watermark

- GIVEN a build compiled without the demo configuration
- WHEN an issued Factura is printed
- THEN no "DEMOSTRACIÓN — SIN VALOR FISCAL" text is present

### Requirement: Printing A Fiscal Document Is Read-Only And Works Offline From Cache

The system MUST NOT create, modify, or delete any record as a result of printing or reprinting a fiscal document, any number of times. A document that was already fetched while online MUST remain printable offline from the persisted query cache.

#### Scenario: Printing the same document twice changes nothing

- GIVEN an issued Factura
- WHEN it is printed twice in a row
- THEN no database record was created, modified, or deleted by either print

#### Scenario: A previously fetched document prints offline

- GIVEN an issued Factura was fetched while online and is cached
- WHEN the device goes offline and its print route is opened
- THEN the document still renders for printing from the persisted cache

### Requirement: Fiscal Document Print Is Isolated Per Workshop

The system MUST only render a print layout for a fiscal document belonging to the authenticated workshop. A print request for another workshop's document MUST be treated as not found.

#### Scenario: Another workshop's document cannot be printed

- GIVEN workshop A has an issued Factura and workshop B does not
- WHEN a user authenticated for workshop B opens a print route for that document's id
- THEN the response reports it as not found
- AND no data from workshop A is rendered

### Requirement: Credit Note Layouts Carry Every Art. 25–26 Mandatory Field

**Phase:** B

Both layouts MUST render, for an issued Nota de Crédito: the buyer's name and RTN; the reason for the credit; the total in numbers and in words in Spanish; a reference to the original Factura's CAI, correlative, and issuance date; and blank signature and identification lines for whoever receives the document.

#### Scenario: Every mandatory credit note field is present on both layouts

- GIVEN an issued Nota de Crédito
- WHEN either print layout is rendered
- THEN the buyer's name and RTN, the reason, the total in numbers and words, the original Factura's CAI/correlative/date, and blank signature and ID lines are all present
