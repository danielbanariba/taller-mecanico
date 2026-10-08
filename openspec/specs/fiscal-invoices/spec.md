# Fiscal Invoices Specification

**Phase:** A

## Purpose

Issuing a Factura (SAR document type `01`) from a `completed` or `delivered` work order: the data-driven opt-in gate, buyer identification rules, the 15% ISV split out of the already tax-inclusive order total, the immutable snapshot that a later edit can never change, the fixed SAR number format, idempotent issuance, and tenancy. Issuing a Factura never changes the order's own total, payments, or balance (D1); it records, in its own immutable document, what SAR requires on top of that unchanged total.

## Requirements

### Requirement: Invoicing Is Gated By A Complete Fiscal Profile And An Active CAI Range

The system MUST allow issuing a Factura only when the workshop has a complete fiscal profile (per `fiscal-profile`) and an active CAI range of document type `01` that is neither exhausted nor past its fecha límite (per `cai-ranges`). Absent either condition, the issuance request MUST fail with `detail: "invoicing_not_configured"` (HTTP 409), and no Factura-related action MUST be offered anywhere in the UI.

#### Scenario: No fiscal profile at all

- GIVEN a workshop with no fiscal profile
- WHEN a Factura issuance is requested for one of its eligible orders
- THEN the response is HTTP 409 with `detail: "invoicing_not_configured"`
- AND no document is created

#### Scenario: A complete profile but no active Factura range

- GIVEN a workshop with a complete fiscal profile and no CAI range of document type `01`
- WHEN a Factura issuance is requested
- THEN the response is HTTP 409 with `detail: "invoicing_not_configured"`
- AND no document is created

#### Scenario: Both conditions met allow issuance

- GIVEN a workshop with a complete fiscal profile and an active, unexhausted, unexpired Factura range
- WHEN a Factura issuance is requested for an eligible order
- THEN the issuance succeeds

### Requirement: Factura Issuance Requires A `completed` Or `delivered` Order With No Existing Non-Credited Factura

The system MUST allow issuing a Factura only from a work order whose status is `completed` or `delivered`. A request against an order in any other status MUST fail with `detail: "work_order_not_invoiceable"` (HTTP 409). A request against an order that already has a non-credited Factura MUST fail with `detail: "work_order_already_invoiced"` (HTTP 409); an order may hold at most one non-credited Factura.

#### Scenario: Issuing from a `quote`, `approved`, or `in_progress` order is rejected

- GIVEN a work order in status `quote`, `approved`, or `in_progress`
- WHEN a Factura issuance is requested for it
- THEN the response is HTTP 409 with `detail: "work_order_not_invoiceable"`
- AND no document is created

#### Scenario: Issuing from a `completed` order succeeds

- GIVEN a work order in status `completed`, with no existing non-credited Factura
- WHEN a Factura issuance is requested for it
- THEN the Factura is issued

#### Scenario: Issuing from a `delivered` order succeeds

- GIVEN a work order in status `delivered`, with no existing non-credited Factura
- WHEN a Factura issuance is requested for it
- THEN the Factura is issued

#### Scenario: A second Factura is rejected while the first is not credited

- GIVEN a work order that already has a non-credited Factura
- WHEN another Factura issuance is requested for the same order
- THEN the response is HTTP 409 with `detail: "work_order_already_invoiced"`
- AND no second document is created

### Requirement: The Buyer Defaults To CONSUMIDOR FINAL; Identification Is Required From L 10,000 Including ISV

The system MUST record the buyer as the legend "CONSUMIDOR FINAL" unless a billing name and RTN are supplied. When the Factura's total, ISV included, is L 10,000.00 or more, a billing name and RTN MUST be supplied, or the issuance MUST fail with `detail: "buyer_identification_required"` (HTTP 409). Below that threshold, identification remains optional. The billing name and RTN used, whatever their source, MUST be captured on the Factura's own snapshot.

#### Scenario: A consumidor final invoice below the threshold needs no identification

- GIVEN an eligible order whose total is L 9,999.99
- WHEN a Factura is issued with no billing name or RTN
- THEN the Factura is issued with buyer "CONSUMIDOR FINAL"

#### Scenario: A consumidor final invoice at or above the threshold without identification is rejected

- GIVEN an eligible order whose total is L 10,000.00
- WHEN a Factura is issued with no billing name or RTN
- THEN the response is HTTP 409 with `detail: "buyer_identification_required"`
- AND no document is created

#### Scenario: Supplying identification at the threshold allows issuance

- GIVEN an eligible order whose total is L 10,000.00
- WHEN a Factura is issued with a billing name and a valid RTN
- THEN the Factura is issued, carrying that billing name and RTN

#### Scenario: Buyer data is prefilled from the customer and editable at issuance

- GIVEN a customer with a saved billing name and RTN, who owns the vehicle on an eligible order
- WHEN the issuance form is opened
- THEN the customer's billing name and RTN are prefilled, and may be edited before the Factura is issued

### Requirement: The Invoice Total Equals The Order's Total, Split Into Gravado 15% And ISV Without Rounding Loss

The system MUST set the Factura's total to exactly the work order's total at the moment of issuance, in integer cents, with no discount, rounding, or adjustment of that amount. The system MUST derive a gravado (base) amount and a 15% ISV amount from that same total such that gravado plus ISV equals the total exactly, in integer cents (D1: line prices already include ISV, so the split happens only at issuance, never on the order itself).

The split is computed once, on the invoice total `T`: gravado is `T × 100 / 115` rounded to the nearest cent (`(200·T + 115) // 230` in integers, which never ties) and ISV is `T` minus gravado. Printed line values are the entered, tax-inclusive amounts.

#### Scenario: A clean total splits exactly

- GIVEN an eligible order whose total is L 1,150.00
- WHEN a Factura is issued
- THEN the Factura's gravado is L 1,000.00 and its ISV is L 150.00
- AND gravado plus ISV equals L 1,150.00 exactly

#### Scenario: Gravado plus ISV always equals the total, whatever the rounding rule

- GIVEN an eligible order whose total, in integer cents, is any amount
- WHEN a Factura is issued
- THEN the Factura's printed gravado plus its printed ISV equals the Factura's total exactly, in integer cents
- AND the order's own total, payments, and balance are unchanged by the issuance

### Requirement: The Factura Number Follows The Fixed SAR Format

The system MUST format the Factura's number as `NNN-NNN-01-NNNNNNNN`: the fiscal profile's establecimiento code, the fiscal profile's punto de emisión code, the fixed document type `01`, and the allocated correlative zero-padded to 8 digits.

#### Scenario: A number is assembled from the profile and the allocated correlative

- GIVEN a fiscal profile with establecimiento code `001` and punto de emisión code `001`, and an active Factura range whose next correlative is `1`
- WHEN a Factura is issued
- THEN its number is `001-001-01-00000001`

### Requirement: Factura Issuance Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when issuing a Factura. An issuance request replayed with the exact same id and payload MUST be a no-op that returns the existing Factura (HTTP 200) and MUST NOT allocate another correlative. A request reusing an existing Factura id with a different payload MUST fail with `detail: "fiscal_invoice_id_conflict"` (HTTP 409).

#### Scenario: Replaying an identical issuance is a no-op

- GIVEN a Factura was already issued with client-generated id `F1`
- WHEN the same issuance request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing Factura, with the same number
- AND no second document is created and no number is consumed

#### Scenario: Reusing a Factura id with a different payload is a conflict

- GIVEN a Factura already exists with client-generated id `F1`
- WHEN an issuance request reuses `F1` for a different order
- THEN the response is HTTP 409 with `detail: "fiscal_invoice_id_conflict"`
- AND the existing Factura is unchanged

### Requirement: The Issued Factura Is An Immutable Snapshot

The system MUST capture, at the moment of issuance, the issuer data, CAI, range, fecha límite, number, date, buyer, lines (description, quantity, unit value), the gravado/ISV breakdown, the total, and the total in words in Spanish, as a single immutable record. A later edit to the fiscal profile, the customer, or any order field that remains editable MUST NOT change a previously issued Factura or how it reprints.

#### Scenario: Editing the fiscal profile after issuance leaves the Factura unchanged

- GIVEN an issued Factura
- WHEN the workshop's fiscal profile razón social is edited afterward
- THEN reprinting that Factura still shows the razón social recorded at issuance

#### Scenario: Editing the customer's billing data after issuance leaves the Factura unchanged

- GIVEN an issued Factura carrying a customer's billing name and RTN
- WHEN the customer's billing name is edited afterward
- THEN reprinting that Factura still shows the billing name recorded at issuance

### Requirement: Factura Issuance May Occur Before Full Payment

The system MUST allow issuing a Factura regardless of the order's paid total or balance due. Payments remain independent of the Factura: they are neither required for issuance nor printed on the document.

#### Scenario: Issuing with an outstanding balance

- GIVEN an eligible order with a balance due greater than zero
- WHEN a Factura is issued for it
- THEN the issuance succeeds
- AND the order's balance due is unaffected by the issuance

### Requirement: The Factura Action Is Offered First On The Order Detail Screen, Without Hiding The Non-Fiscal Receipt

The system MUST show the "Emitir factura" action — or, once issued, a link to the issued Factura — ahead of the existing non-fiscal receipt links on an eligible order's detail screen, without removing or hiding those receipt links. The non-fiscal receipt MUST remain available, unchanged, for every order regardless of invoicing status or configuration.

#### Scenario: An eligible, uninvoiced order shows the Factura action first

- GIVEN an order eligible for Factura issuance, not yet invoiced, on a workshop with invoicing configured
- WHEN the order detail screen is rendered
- THEN the "Emitir factura" action appears before the receipt links
- AND both receipt links are still present and clickable

#### Scenario: An invoiced order links to the Factura, still ahead of the receipt

- GIVEN an order that already has an issued Factura
- WHEN the order detail screen is rendered
- THEN a link to the issued Factura appears before the receipt links
- AND both receipt links are still present and clickable

#### Scenario: A workshop with no fiscal profile sees no Factura action, and the receipt is unaffected

- GIVEN a workshop with no fiscal profile
- WHEN an eligible order's detail screen is rendered
- THEN no Factura-related action is shown
- AND the receipt links behave exactly as they did before this capability existed

### Requirement: Factura Reads And Issuance Are Isolated Per Workshop

The system MUST scope every Factura read and issuance request by the authenticated user's workshop id (`get_current_workshop_id`), including the order it is issued against. A Factura belonging to another workshop, or an issuance request against another workshop's order, MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's Factura is invisible

- GIVEN workshop A has an issued Factura and workshop B does not
- WHEN a user authenticated for workshop B requests that Factura by id
- THEN the response reports it as not found

#### Scenario: Issuing against another workshop's order is rejected

- GIVEN workshop A has an eligible order
- WHEN a user authenticated for workshop B requests a Factura issuance against that order's id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND no document is created

### Requirement: Factura Writes Require A Live Connection; Reads Stay Available Offline

The system MUST disable Factura issuance in the UI with a Spanish message when the device is offline. Reading a previously fetched Factura (list or detail) MUST remain available offline from the persisted query cache, using `workshopQueryKey`-prefixed query keys.

#### Scenario: Issuance is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the Factura issuance dialog for an eligible order
- THEN the issue action is disabled
- AND a Spanish message explains that issuing a Factura requires a connection

#### Scenario: A previously fetched Factura renders offline

- GIVEN a Factura was fetched while online and is cached
- WHEN the device goes offline and that Factura's detail is revisited
- THEN the previously fetched Factura still renders from the persisted cache
