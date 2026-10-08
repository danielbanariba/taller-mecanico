# Delta for Work Orders

**Phase:** A

## ADDED Requirements

### Requirement: Line Edits Are Rejected While The Order Has A Non-Credited Factura

The system MUST reject a work order line add, edit, or remove request with HTTP 409 and `detail: "work_order_invoiced"` while the order has a non-credited Factura issued against it (per `fiscal-invoices`), in addition to the existing lock that applies once the order is `delivered` or `cancelled`. `WorkOrderOut.lines_editable` MUST report `false` while this invoicing lock is active, even for an order whose status would otherwise allow line edits (`completed`). This lock MUST NOT prevent a status transition (including `completed` → `delivered`) or an edit to the order's own fields (`complaint`, `odometer_km`, `notes`); cancellation of a `completed` or `delivered` order remains impossible under the existing status-transition table, unchanged by this requirement. Once the Factura is fully credited by a Nota de Crédito (per `credit-notes`), this lock lifts and line edits are evaluated under the existing rules again.

#### Scenario: Adding a line to an invoiced, completed order is rejected

- GIVEN a `completed` work order with a non-credited Factura
- WHEN a line add request is sent
- THEN the response is HTTP 409 with `detail: "work_order_invoiced"`
- AND no line is added

#### Scenario: `lines_editable` reports `false` while invoiced, even though the status allows edits

- GIVEN a `completed` work order with a non-credited Factura
- WHEN the order is fetched
- THEN `lines_editable` is `false`

#### Scenario: Moving an invoiced order to `delivered` is still allowed

- GIVEN a `completed` work order with a non-credited Factura
- WHEN the status is set to `delivered`
- THEN the transition succeeds

#### Scenario: Editing the order's own fields is still allowed while invoiced

- GIVEN a `completed` work order with a non-credited Factura
- WHEN a `PATCH` request changes the order's `notes`
- THEN the edit succeeds

#### Scenario: Line edits are allowed again once the Factura is fully credited

- GIVEN a `completed` work order whose only Factura was locking its lines, now fully credited by a Nota de Crédito
- WHEN a line add request is sent
- THEN the request succeeds, evaluated under the existing (non-invoicing) line-lock rules
