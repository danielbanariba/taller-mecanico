# Credit Notes Specification

**Phase:** B

## Purpose

Correcting an issued Factura after delivery is only possible with a full-amount Nota de Crédito (SAR document type `06`, Art. 4.32, 25–26) — v1 has no partial credit notes and no "ANULADA" path. A credit note draws from its own CAI range, enforced exactly like a Factura's; once a Factura is fully credited, the invoiced-order lock it placed on the work order (per `work-orders`) lifts, and the order may be invoiced again.

## Requirements

### Requirement: A Credit Note Credits An Issued Factura In Full, With A Required Reason And A Reference To The Original

The system MUST issue a Nota de Crédito only for the Factura's full amount — v1 has no partial credit notes. Every credit note MUST carry a required reason, the buyer's name and RTN exactly as snapshotted on the Factura being credited, and a reference to that Factura's CAI, correlative (number), and issuance date.

#### Scenario: A full credit note references its original Factura

- GIVEN an issued Factura
- WHEN a Nota de Crédito is issued against it with a reason
- THEN the credit note's amount equals the Factura's full total
- AND the credit note carries the Factura's CAI, number, and issuance date
- AND the credit note carries the same buyer name and RTN as the Factura

#### Scenario: A credit note with no reason is rejected

- GIVEN an issued Factura eligible for a credit note
- WHEN a credit note is requested with no reason
- THEN the response is HTTP 422
- AND no credit note is created

### Requirement: Credit Notes Draw From Their Own CAI Range Of Document Type 06, Enforced Exactly Like Facturas

The system MUST allocate a credit note's correlative from an active CAI range of document type `06`, under the exact same `cai-ranges` rules as a Factura: row-locked allocation, blocked when exhausted, blocked past the fecha límite (inclusive of that day, compared in `America/Tegucigalpa`), and gated by the same data-driven opt-in as any other document type.

#### Scenario: No active document-type-06 range blocks credit note issuance

- GIVEN a workshop with an issued Factura eligible for a credit note, and no CAI range of document type `06`
- WHEN a credit note is requested against that Factura
- THEN the response is HTTP 409 with `detail: "invoicing_not_configured"`
- AND no credit note is created

#### Scenario: An exhausted document-type-06 range blocks issuance

- GIVEN a workshop whose only document-type-`06` range is exhausted
- WHEN a credit note is requested
- THEN the response is HTTP 409 with `detail: "cai_range_exhausted"`
- AND no credit note is created

### Requirement: A Factura Can Be Credited Only Once

The system MUST reject a second credit note against a Factura that already has one, with `detail: "credit_note_already_issued"` (HTTP 409).

#### Scenario: A second credit note against the same Factura is rejected

- GIVEN a Factura that already has an issued credit note
- WHEN another credit note is requested against the same Factura
- THEN the response is HTTP 409 with `detail: "credit_note_already_issued"`
- AND no second credit note is created

### Requirement: Credit Note Issuance Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when issuing a credit note. A request replayed with the exact same id and payload MUST be a no-op that returns the existing credit note (HTTP 200) and MUST NOT allocate another correlative. A request reusing an existing credit note id with a different payload MUST fail with `detail: "credit_note_id_conflict"` (HTTP 409).

#### Scenario: Replaying an identical credit note issuance is a no-op

- GIVEN a credit note was already issued with client-generated id `CN1`
- WHEN the same issuance request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing credit note
- AND no number is consumed by the replay

#### Scenario: Reusing a credit note id with a different payload is a conflict

- GIVEN a credit note already exists with client-generated id `CN1`
- WHEN a request reuses `CN1` against a different Factura
- THEN the response is HTTP 409 with `detail: "credit_note_id_conflict"`
- AND the existing credit note is unchanged

### Requirement: Full Credit Lifts The Invoiced-Order Lock And Enables Re-Invoicing

Once a Factura is fully credited, the work order's invoiced-order line lock (per `work-orders`) MUST lift: if the order is `completed`, its lines become editable again; and the order becomes eligible for a new Factura issuance, subject to the same rules as any other eligible order.

#### Scenario: Lines become editable again after a full credit note

- GIVEN a `completed` work order whose Factura was locking its lines
- WHEN a credit note fully credits that Factura
- THEN a line add, edit, or remove request on that order succeeds

#### Scenario: A new Factura may be issued after a full credit note

- GIVEN a work order whose only Factura has been fully credited
- WHEN a new Factura issuance is requested for that order
- THEN the issuance succeeds, allocating a new correlative

### Requirement: Re-Invoicing A Fully Credited `delivered` Order Allows Only Corrected Buyer Data

A `delivered` order's lines remain locked by the existing baseline rule (`work-orders`' delivered-order line lock is unmodified by this capability). Once such an order's Factura is fully credited, the system MUST allow issuing a new Factura for it with corrected buyer name and RTN, but the new Factura's lines and amount MUST still be drawn from the order's current (locked, unchanged) lines — amount corrections on a delivered order are out of scope for v1.

#### Scenario: Re-invoicing a delivered, fully credited order with corrected buyer data

- GIVEN a `delivered` work order whose only Factura has been fully credited
- WHEN a new Factura is issued for it with a different billing name and RTN than the credited one
- THEN the new Factura is issued with the corrected buyer data
- AND its lines and total match the order's current (unchanged) lines

### Requirement: A Credit Note Has No Effect On Payments Or Stock

Issuing a credit note MUST NOT alter the order's recorded payments, paid total, balance due, or any inventory movement. A refund, if the workshop needs one, is recorded by voiding a payment through the existing `payments` flow, unmodified by this capability.

#### Scenario: Issuing a credit note leaves payments and stock untouched

- GIVEN a work order with recorded payments and consumed stock, and an issued Factura eligible for a credit note
- WHEN a credit note is issued against that Factura
- THEN the order's paid total, balance due, and every item's stock are unchanged by the credit note

### Requirement: Credit Notes Are Immutable Snapshots

The system MUST capture, at the moment of issuance, the credit note's own snapshot — issuer data, CAI, range, fecha límite, number, date, buyer, reason, the referenced Factura's CAI/number/date, and the total in numbers and in words — as a single immutable record. A later edit to the fiscal profile or the customer MUST NOT change a previously issued credit note or how it reprints.

#### Scenario: Editing the customer after a credit note leaves it unchanged

- GIVEN an issued credit note carrying a customer's billing name
- WHEN that customer's billing name is edited afterward
- THEN reprinting the credit note still shows the billing name recorded at issuance

### Requirement: Credit Notes Are Isolated Per Workshop

The system MUST scope every credit note read and write by the authenticated user's workshop id (`get_current_workshop_id`). A credit note belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's credit note is invisible

- GIVEN workshop A has an issued credit note and workshop B does not
- WHEN a user authenticated for workshop B requests that credit note by id
- THEN the response reports it as not found

### Requirement: Credit Note Writes Require A Live Connection; Reads Stay Available Offline

The system MUST disable credit note issuance in the UI with a Spanish message when the device is offline. Reading a previously fetched credit note MUST remain available offline from the persisted query cache, using `workshopQueryKey`-prefixed query keys.

#### Scenario: Issuance is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the credit note dialog for an eligible Factura
- THEN the issue action is disabled
- AND a Spanish message explains that issuing a credit note requires a connection

#### Scenario: A previously fetched credit note renders offline

- GIVEN a credit note was fetched while online and is cached
- WHEN the device goes offline and that credit note's detail is revisited
- THEN the previously fetched credit note still renders from the persisted cache
