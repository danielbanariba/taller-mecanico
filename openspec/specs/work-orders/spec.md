# Work Orders Specification

**Phase:** 2

## Purpose

A work order records labor and parts for one of a customer's vehicles, with a human-readable per-workshop number, three kinds of quote line, totals in Lempiras, and a six-state status lifecycle: `quote`, `approved`, `in_progress`, `completed`, `delivered`, and `cancelled`. This spec defines what MUST be true about order identity, numbering, line composition, totals, the fixed transition table, and when lines and the order itself may be edited.

## Requirements

### Requirement: A Work Order Belongs To Exactly One Vehicle Of The Workshop's Customers

The system MUST associate every work order with exactly one vehicle belonging to a customer of the authenticated workshop. A work order without a vehicle (counter sale) MUST NOT be supported.

#### Scenario: Creating an order for an existing vehicle

- GIVEN an active vehicle belonging to a customer of the authenticated workshop
- WHEN a work order is created referencing that vehicle's id
- THEN the order is saved with that vehicle

#### Scenario: Creating an order for a nonexistent or foreign vehicle

- GIVEN a vehicle id that does not exist, or belongs to another workshop
- WHEN a work order create request references that vehicle id
- THEN the response is HTTP 404 with `detail: "vehicle_not_found"`
- AND no work order is created

### Requirement: Work Order Numbers Are Assigned Atomically Per Workshop And Never Skipped Or Duplicated By A Replay

The system MUST assign each new work order the next number from a per-workshop counter, incremented by a single atomic update that returns the new value. A create request replayed with the same client-generated order id and the same payload MUST NOT consume an additional number.

#### Scenario: Sequential numbering within a workshop

- GIVEN a workshop whose last assigned order number is `42`
- WHEN a new work order is created for that workshop
- THEN the new order's number is `43`

#### Scenario: Concurrent creates never assign the same number

- GIVEN a workshop with no in-flight orders
- WHEN two work order create requests for that workshop are submitted concurrently
- THEN both succeed with two distinct, sequential numbers
- AND neither request observes the other's number

#### Scenario: Replaying an identical create does not consume a second number

- GIVEN a work order was already created with client-generated id `O1`, assigned number `43`
- WHEN the same create request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing order, still numbered `43`
- AND the workshop's counter is not incremented again

#### Scenario: Reusing an order id with a different payload is a conflict

- GIVEN a work order already exists with client-generated id `O1`
- WHEN a create request reuses `O1` with a different vehicle id
- THEN the response is HTTP 409 with `detail: "work_order_id_conflict"`
- AND the existing order is unchanged

### Requirement: A Work Order Has Quote Lines Of Three Kinds

The system MUST support three kinds of quote line on a work order: labor (a description, quantity, and unit price, with no stock effect), inventory part (linked to an existing `Item` of the workshop, with a quantity and unit price; these lines consume stock per the `work-order-stock-consumption` capability), and external part (free-text description, quantity, and unit price, bought outside the shop, with no stock effect).

#### Scenario: Adding a labor line

- GIVEN a work order in a state that allows line edits
- WHEN a labor line with quantity and unit price is added
- THEN the line is saved with no reference to any `Item`
- AND no inventory movement is posted

#### Scenario: Adding an inventory part line references an existing item

- GIVEN a work order in a state that allows line edits, and an active item of the workshop
- WHEN an inventory part line is added referencing that item's id
- THEN the line is saved with that item reference
- AND no inventory movement is posted yet (movements post per `work-order-stock-consumption`)

#### Scenario: Adding an inventory part line referencing a nonexistent or foreign item

- GIVEN a work order in a state that allows line edits
- WHEN an inventory part line is added referencing an item id that does not exist, or belongs to another workshop
- THEN the response is HTTP 404 with `detail: "item_not_found"`
- AND no line is added

#### Scenario: Adding an external part line

- GIVEN a work order in a state that allows line edits
- WHEN an external part line with a free-text description, quantity, and unit price is added
- THEN the line is saved with no `Item` reference
- AND no inventory movement is posted

### Requirement: Order And Line Totals Are Computed In Lempiras From Final Line Prices

The system MUST compute each line's subtotal as quantity times unit price, and the order's total as the sum of its line subtotals, with no tax computation or breakdown (line prices are final amounts).

#### Scenario: Total reflects all three line kinds

- GIVEN a work order with one labor line, one inventory part line, and one external part line, each with a quantity and unit price
- WHEN the order is fetched
- THEN its total equals the sum of the three lines' quantity-times-price subtotals
- AND no tax amount is present anywhere in the response

### Requirement: The Status Lifecycle Is A Fixed, Acyclic Table Of Six States

The system MUST implement exactly these six statuses and this transition table, with no transition outside it:

| From | Allowed next statuses |
|---|---|
| `quote` | `approved`, `cancelled` |
| `approved` | `in_progress`, `cancelled` |
| `in_progress` | `completed`, `cancelled` |
| `completed` | `delivered` |
| `delivered` | none (terminal) |
| `cancelled` | none (terminal) |

`approved → in_progress` is the only transition in the table that triggers stock consumption for inventory part lines (per `work-order-stock-consumption`). `in_progress → cancelled` is the only transition that reverses stock already consumed. `completed` and `delivered` orders cannot be cancelled: by the time an order reaches `completed`, its parts are already installed, so correcting it means editing its lines (allowed in `completed`; see the line-lock requirement below), not cancelling the order. The table has no back edge, so no status can ever be re-entered.

A status request is handled as:
- if the order is already in the requested status, the response is HTTP 200 with the order unchanged (no-op);
- if the requested status is reachable per the table above, the transition is applied and the response is HTTP 200;
- otherwise the response is HTTP 409 with `detail: "invalid_status_transition"`.

#### Scenario: A disallowed transition is rejected

- GIVEN a work order in a status that does not allow a given next status per the table above
- WHEN that status is requested
- THEN the response is HTTP 409 with `detail: "invalid_status_transition"`
- AND the order's status is unchanged

#### Scenario: Exactly one transition consumes stock

- GIVEN a work order with an inventory part line, currently in status `approved`
- WHEN the status is set to `in_progress`
- THEN the linked item's stock decreases by the line's quantity
- AND no other transition in the order's lifecycle posts an inventory movement for that line

#### Scenario: Cancelling after consumption reverses it

- GIVEN a work order in status `in_progress` that already consumed stock for an inventory part line
- WHEN the order is cancelled
- THEN a reversal movement restores the item's stock to what it was before that line's consumption

#### Scenario: `completed` cannot be cancelled

- GIVEN a work order in status `completed`
- WHEN the status is set to `cancelled`
- THEN the response is HTTP 409 with `detail: "invalid_status_transition"`
- AND the order remains `completed`

#### Scenario: `delivered` cannot be cancelled

- GIVEN a work order in status `delivered`
- WHEN the status is set to `cancelled`
- THEN the response is HTTP 409 with `detail: "invalid_status_transition"`
- AND the order remains `delivered`

#### Scenario: Repeating a transition returns the unchanged order

- GIVEN a work order already in status `in_progress`, reached via a prior `approved → in_progress` transition
- WHEN the same status request (`in_progress`) is sent again
- THEN the response is HTTP 200 with the order unchanged
- AND no additional movement is posted and no status timestamp is updated

### Requirement: Order And Line Edits Are Rejected Once The Order Is Delivered Or Cancelled

The system MUST reject edits to a work order's own fields (`PATCH`) and to its lines (add, edit, remove) once the order's status is `delivered` or `cancelled`, returning HTTP 409 with `detail: "work_order_locked"`. Lines and the order remain editable in every other status, including `completed`.

#### Scenario: Editing lines in `completed` is allowed

- GIVEN a work order in status `completed`
- WHEN a line is added, edited, or removed
- THEN the request succeeds

#### Scenario: Editing a delivered order's lines is rejected

- GIVEN a work order in status `delivered`
- WHEN a line add, edit, or remove request is sent
- THEN the response is HTTP 409 with `detail: "work_order_locked"`
- AND no line is changed

#### Scenario: Editing a cancelled order's lines is rejected

- GIVEN a work order in status `cancelled`
- WHEN a line add, edit, or remove request is sent
- THEN the response is HTTP 409 with `detail: "work_order_locked"`
- AND no line is changed

#### Scenario: Editing the order's own fields once delivered is rejected

- GIVEN a work order in status `delivered`
- WHEN a `PATCH` request changes the order's `complaint`, `odometer_km`, or `notes`
- THEN the response is HTTP 409 with `detail: "work_order_locked"`
- AND the order's fields are unchanged

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

### Requirement: Work Order Creation And Line Edits Are Idempotent By Client-Generated Id

The system MUST accept client-generated ids for work orders and their lines. A create or edit request replayed with the exact same id and payload MUST be a no-op. A request reusing an existing line id with a different payload MUST fail with `work_order_line_id_conflict` (HTTP 409). A request targeting a line id that does not exist on the order, or belongs to another order, MUST fail with `work_order_line_not_found` (HTTP 404).

#### Scenario: Replaying an identical line add is a no-op

- GIVEN a work order line was already added with client-generated id `L1` and a given payload
- WHEN the same add-line request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing line
- AND no second line row is created

#### Scenario: Reusing a line id with a different payload is a conflict

- GIVEN a work order line already exists with client-generated id `L1`
- WHEN a line-add request reuses `L1` with a different payload (for example, a different `quantity`)
- THEN the response is HTTP 409 with `detail: "work_order_line_id_conflict"`
- AND the existing line is unchanged

#### Scenario: Editing or removing a line that does not exist on the order

- GIVEN a line id that does not exist on the order, or belongs to another order
- WHEN an edit or remove request targets that id
- THEN the response is HTTP 404 with `detail: "work_order_line_not_found"`

### Requirement: Work Order Reads Stay Available Offline; Writes Require A Live Connection

The system MUST disable work order create, edit, line, and status-transition actions in the UI with a Spanish message when the device is offline. Work order list and detail reads MUST remain available offline from the persisted query cache, using `workshopQueryKey`-prefixed query keys.

#### Scenario: Status transition is disabled while offline

- GIVEN the device has no network connection
- WHEN the user attempts to move a work order to its next status
- THEN the action is disabled
- AND a Spanish message explains that the transition requires a connection

#### Scenario: A previously visited order detail renders offline

- GIVEN a work order's detail was fetched while online and is cached
- WHEN the device goes offline and the user revisits that order's detail
- THEN the previously fetched order still renders from the persisted cache

### Requirement: Vehicle And Customer Detail Show Their Work Orders

The system MUST list a vehicle's work orders on its detail screen, and a customer's work orders (across all their vehicles) on the customer's detail screen, making the vehicle's service history visible.

#### Scenario: Vehicle history shows its orders

- GIVEN a vehicle with two work orders
- WHEN the vehicle detail screen is requested
- THEN both work orders are listed, most recent first

### Requirement: Work Order Data Is Isolated Per Workshop

The system MUST scope every work order query and mutation by the authenticated user's workshop id (`get_current_workshop_id`). A work order belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's work order is invisible

- GIVEN workshop A has a work order and workshop B does not
- WHEN a user authenticated for workshop B requests that order by id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`

#### Scenario: Another workshop's work order cannot be mutated

- GIVEN workshop A has a work order
- WHEN a user authenticated for workshop B sends an edit, line, or status-transition request for that order's id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND workshop A's order is unchanged
