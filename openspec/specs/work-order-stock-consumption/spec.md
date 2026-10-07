# Work Order Stock Consumption Specification

**Phase:** 2

## Purpose

This capability carries the inventory ledger's behavior change for this proposal, because no `inventory` baseline spec exists to delta against. It defines when and how an inventory part line on a work order posts movements through the existing `record_movement` use case, how edits and cancellation after consumption are reflected, how movement ids stay deterministic for safe retries, and how `inventory_movements` exposes the order that caused a movement.

## Requirements

### Requirement: Inventory Part Lines Consume Stock When The Order Transitions From `approved` To `in_progress`

The system MUST post an `out` movement through the existing `record_movement` use case for each inventory part line when the order's status transitions from `approved` to `in_progress`, the single consuming transition in the `work-orders` lifecycle. The system MUST NOT post a movement for a labor or external part line, since neither references an `Item`.

#### Scenario: Entering `in_progress` posts movements for every inventory part line

- GIVEN a work order in status `approved`, with two inventory part lines and one labor line
- WHEN the order transitions to `in_progress`
- THEN an `out` movement is posted for each of the two inventory part lines
- AND no movement is posted for the labor line

#### Scenario: Negative stock is flagged, never blocked

- GIVEN an inventory part line whose quantity exceeds the linked item's current stock, on a work order in status `approved`
- WHEN the order transitions to `in_progress`
- THEN the movement is posted and the item's stock goes negative
- AND the item is flagged `needs_review`/`is_low`
- AND the transition is not blocked or rejected because of the resulting negative stock

### Requirement: Editing A Line's Quantity After Consumption Posts Only The Delta

The system MUST post a delta movement (`in` or `out`, whose quantity is the absolute difference) when an inventory part line's quantity is edited after its line has already consumed stock. The system MUST NOT re-post the line's full original quantity.

#### Scenario: Increasing quantity after consumption posts an additional `out`

- GIVEN an inventory part line already consumed 2 units of an item
- WHEN the line's quantity is edited to 5
- THEN an additional `out` movement for 3 units is posted
- AND the item's stock reflects a cumulative consumption of 5 units for that line

#### Scenario: Decreasing quantity after consumption posts an `in`

- GIVEN an inventory part line already consumed 5 units of an item
- WHEN the line's quantity is edited to 2
- THEN an `in` movement for 3 units is posted
- AND the item's stock reflects a cumulative consumption of 2 units for that line

### Requirement: Cancellation After Consumption Reverses Every Consumed Line

The system MUST post a reversal movement restoring the full quantity consumed by each of the order's inventory part lines when the order is cancelled after the stock-consuming transition. The system MUST NOT reverse lines that never consumed stock (the order was cancelled before reaching the stock-consuming state).

#### Scenario: Cancelling after consumption restores stock

- GIVEN an order with an inventory part line that consumed 5 units
- WHEN the order is cancelled
- THEN an `in` reversal movement for 5 units is posted
- AND the item's stock returns to what it was before that line's consumption

#### Scenario: Cancelling before consumption posts no reversal

- GIVEN an order with an inventory part line that has never consumed stock (the order never reached the stock-consuming state)
- WHEN the order is cancelled
- THEN no movement is posted for that line

### Requirement: Every Movement Id Is Deterministic, Composed Of The Order, Line, And A Per-Line Revision Counter

The system MUST derive each stock-consumption movement's id deterministically as `order_id:line_id:revision` (the same `uuid5` idiom already used for `_initial_movement_id`), where `revision` is that line's own counter, starting at 1 for its initial consumption and incremented by one for every later event that changes its posted quantity (a quantity edit, a line removal, or the order's cancellation reversal). Retrying any of consumption, an edit, or a cancellation with the same inputs MUST NOT post a second movement, because the retry resolves to the same `revision` and therefore the same id.

#### Scenario: Revision increments once per posting event on the same line

- GIVEN an inventory part line whose initial consumption posted at revision 1
- WHEN its quantity is edited twice, each edit changing the line's posted quantity
- THEN the first edit posts at revision 2 and the second at revision 3
- AND the three movements have three distinct, deterministic ids

#### Scenario: Retrying the stock-consuming transition does not double-apply

- GIVEN a work order's `approved → in_progress` transition has already posted its movements
- WHEN the same transition request is retried (e.g., a client retry after a dropped response)
- THEN no additional movement is posted
- AND the item's stock is unchanged by the retry

#### Scenario: Retrying an edit does not double-apply

- GIVEN a line-quantity edit has already posted its delta movement
- WHEN the same edit request is retried with identical inputs
- THEN no additional movement is posted

#### Scenario: Retrying a cancellation does not double-apply

- GIVEN a cancellation has already posted its reversal movement
- WHEN the same cancellation request is retried
- THEN no additional reversal movement is posted

### Requirement: Movements Record Which Order And Line Caused Them

The system MUST add nullable `order_id` and `order_line_id` columns to `inventory_movements`, populated for every movement caused by a work order line and left `null` for movements unrelated to any order (manual adjustments, physical counts, offline-queued movements). An item's movement history MUST expose the order each movement belongs to, when present.

#### Scenario: An order-caused movement is linked

- GIVEN a work order line consumes stock
- WHEN the resulting movement is fetched as part of the item's history
- THEN the movement's `order_id` and `order_line_id` identify that order and line

#### Scenario: A manual movement is unlinked

- GIVEN a manual stock adjustment unrelated to any work order
- WHEN the resulting movement is fetched as part of the item's history
- THEN its `order_id` and `order_line_id` are `null`

### Requirement: Existing Movement Idempotency Behavior Is Preserved For Non-Order Movements

The existing `record_movement` idempotency comparison (matching on `{item_id, kind, quantity, note}` for a replayed client-generated movement id) MUST continue to work unchanged for movements that carry no order link, including offline-queued movements from the outbox. Adding the nullable order-link fields MUST NOT change the replay-matching behavior for movements where those fields are absent on both the original and the replay.

#### Scenario: Offline-queued movement replay is unaffected

- GIVEN a movement was recorded via the outbox with no order link
- WHEN the same client-generated movement id is replayed with the same `{item_id, kind, quantity, note}` and still no order link
- THEN the replay is a no-op exactly as it is today
- AND the absence of order-link fields does not cause a false conflict

### Requirement: The Order's Status Change And Its Movements Commit In One Transaction

The system MUST commit a stock-consuming, edit-delta, or reversal status/line change together with its resulting movement(s) in a single database transaction, so that a failure partway through never leaves the order's status changed without its corresponding movement, or vice versa.

#### Scenario: A failure during movement posting rolls back the status change

- GIVEN a work order transition that would post an inventory movement
- WHEN posting the movement fails for any reason
- THEN the order's status is not changed
- AND no partial movement is left posted

### Requirement: Concurrent Stock-Affecting Transitions On Overlapping Items Do Not Deadlock

The system MUST allow two concurrent order transitions that each consume stock from overlapping sets of items to both complete successfully, without a database deadlock error.

#### Scenario: Two orders consuming the same item concurrently both succeed

- GIVEN two different work orders, each with an inventory part line referencing the same item
- WHEN both orders transition into the stock-consuming state concurrently
- THEN both transitions complete successfully
- AND the item's final stock reflects both lines' consumption
