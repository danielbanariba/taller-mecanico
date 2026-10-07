# Payments Specification

**Phase:** 3

## Purpose

Recording payments against a work order, in one of four methods, with the order's paid total and balance due derived from its non-voided recorded payments. An order accepts several partial payments (for example, a deposit plus a balance), and a payment recorded in error can be voided rather than deleted. This capability carries no tax computation, consistent with the non-fiscal scope.

## Requirements

### Requirement: A Payment Belongs To Exactly One Work Order Of The Authenticated Workshop

The system MUST associate every payment with exactly one work order belonging to the authenticated workshop.

#### Scenario: Recording a payment against an existing order

- GIVEN a work order belonging to the authenticated workshop
- WHEN a payment is recorded referencing that order's id
- THEN the payment is saved against that order

#### Scenario: Recording a payment against a nonexistent or foreign order

- GIVEN an order id that does not exist, or belongs to another workshop
- WHEN a payment create request references that order id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND no payment is created

### Requirement: Payment Method Wire Values Are English, Limited To Four

The system MUST accept exactly one of four payment methods per payment, using the English wire values `cash`, `transfer`, `card`, and `other` (shown to the user as "Efectivo", "Transferencia", "Tarjeta", and "Otro" respectively, in `copy.ts`). A request whose `method` is outside these four wire values MUST be rejected as a standard request-validation error (HTTP 422), since the method is a closed enum on the request schema.

#### Scenario: A supported method is accepted

- GIVEN a payment create request with method `transfer`
- WHEN the request is processed
- THEN the payment is saved with that method

#### Scenario: An unsupported method is rejected

- GIVEN a payment create request with a method outside the four wire values (for example, the Spanish label `transferencia`, or `check`)
- WHEN the request is processed
- THEN the response is HTTP 422
- AND no payment is created

### Requirement: Payment Creation Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when recording a payment. A create request replayed with the exact same id and payload MUST be a no-op that returns the existing payment (HTTP 200). A create request reusing an existing id with a different payload MUST fail with `payment_id_conflict` (HTTP 409).

#### Scenario: Replaying an identical payment create is a no-op

- GIVEN a payment was already recorded with client-generated id `P1` and a given payload
- WHEN the same create request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing payment
- AND the order's paid total is not increased by the replay

#### Scenario: Reusing a payment id with a different payload is a conflict

- GIVEN a payment already exists with client-generated id `P1`
- WHEN a create request reuses `P1` with a different amount
- THEN the response is HTTP 409 with `detail: "payment_id_conflict"`
- AND the existing payment is unchanged

### Requirement: An Order Only Accepts Payments In Statuses That Allow Them

The system MUST only accept a payment for a work order whose status is `approved`, `in_progress`, `completed`, or `delivered`. A payment request against an order in status `quote` or `cancelled` MUST fail with `work_order_not_payable` (HTTP 409).

#### Scenario: A deposit is accepted while the order is still `approved`

- GIVEN a work order in status `approved`, not yet started
- WHEN a payment is recorded against it
- THEN the payment is saved and counts toward the order's paid total

#### Scenario: A payment against a `quote` is rejected

- GIVEN a work order in status `quote`
- WHEN a payment create request references that order's id
- THEN the response is HTTP 409 with `detail: "work_order_not_payable"`
- AND no payment is created

#### Scenario: A payment against a `cancelled` order is rejected

- GIVEN a work order in status `cancelled`
- WHEN a payment create request references that order's id
- THEN the response is HTTP 409 with `detail: "work_order_not_payable"`
- AND no payment is created

### Requirement: A Payment Cannot Exceed The Order's Balance

The system MUST reject a payment whose amount exceeds the order's current balance due (the order's total minus the sum of its non-voided payments), including when the balance is already zero or negative, with `payment_exceeds_balance` (HTTP 409).

#### Scenario: A payment exceeding the balance is rejected

- GIVEN a work order with a balance due of 300.00
- WHEN a payment of 350.00 is recorded against it
- THEN the response is HTTP 409 with `detail: "payment_exceeds_balance"`
- AND no payment is created

#### Scenario: A payment against an already-settled order is rejected

- GIVEN a work order whose balance due is 0.00
- WHEN a payment of any positive amount is recorded against it
- THEN the response is HTTP 409 with `detail: "payment_exceeds_balance"`
- AND no payment is created

### Requirement: An Order's Paid Total And Balance Due Reflect Only Its Non-Voided Recorded Payments

The system MUST compute an order's paid total as the sum of its non-voided payments' amounts, and its balance due as the order's total minus its paid total. A voided payment MUST NOT contribute to either figure.

#### Scenario: A single full payment zeroes the balance

- GIVEN a work order with total 500.00 and no payments
- WHEN a payment of 500.00 is recorded
- THEN the order's paid total is 500.00
- AND the order's balance due is 0.00

#### Scenario: Multiple partial payments accumulate

- GIVEN a work order with total 500.00 and no payments
- WHEN a payment of 200.00 (deposit) and later a payment of 300.00 (balance) are recorded
- THEN the order's paid total is 500.00
- AND the order's balance due is 0.00

#### Scenario: A voided payment does not count toward the paid total

- GIVEN a work order with one payment of 200.00 that has since been voided
- WHEN the order's paid total and balance due are computed
- THEN the paid total does not include that 200.00
- AND the balance due is as if that payment had never been recorded

### Requirement: Voiding A Payment Requires A Reason And Excludes It From Every Total

The system MUST allow voiding a recorded payment, requiring a reason in the void request. A voided payment's record MUST be kept (never deleted) and MUST be excluded from the order's paid total, its balance due, and the daily cash summary. Voiding MUST be idempotent: voiding an already-voided payment MUST succeed (HTTP 200) and return it unchanged, without requiring a second reason to take effect.

#### Scenario: Voiding a payment requires a reason

- GIVEN a recorded, non-voided payment
- WHEN a void request is sent with no reason
- THEN the response is HTTP 422
- AND the payment remains non-voided

#### Scenario: Voiding a payment excludes it from the order's totals

- GIVEN a work order with a payment of 200.00 toward a total of 500.00
- WHEN that payment is voided with a reason
- THEN the order's paid total no longer includes that 200.00
- AND the order's balance due increases back to 500.00

#### Scenario: Voiding is idempotent

- GIVEN a payment already voided at time `T` with reason "duplicado"
- WHEN a second void request is sent for the same payment, with any reason
- THEN the response is HTTP 200 with the payment unchanged
- AND its voided timestamp remains `T`

#### Scenario: Voiding is isolated per workshop

- GIVEN workshop A has a work order with a payment
- WHEN a user authenticated for workshop B sends a void request using workshop A's order id and payment id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND workshop A's payment remains non-voided

#### Scenario: Voiding requires a live connection

- GIVEN the device has no network connection
- WHEN the user attempts to void a payment
- THEN the action is disabled
- AND a Spanish message explains that voiding a payment requires a connection

### Requirement: Cancelling An Order Counts Only Its Non-Voided Payments

The system MUST reject cancelling a work order that has one or more non-voided payments, with `work_order_has_payments` (HTTP 409). An order whose only payments have all been voided MUST remain cancellable.

#### Scenario: Cancelling an order with a non-voided payment is rejected

- GIVEN a work order in status `in_progress` with one non-voided payment
- WHEN the order is cancelled
- THEN the response is HTTP 409 with `detail: "work_order_has_payments"`
- AND the order's status is unchanged

#### Scenario: Cancelling an order whose only payment was voided is allowed

- GIVEN a work order in status `in_progress` whose only payment has been voided
- WHEN the order is cancelled
- THEN the cancellation succeeds

### Requirement: Payments Require A Live Connection

The system MUST disable the record-payment action in the UI with a Spanish message when the device is offline.

#### Scenario: Recording a payment is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the record-payment form
- THEN the submit action is disabled
- AND a Spanish message explains that recording a payment requires a connection

### Requirement: Payment Data Is Isolated Per Workshop

The system MUST scope every payment query and mutation by the authenticated user's workshop id (`get_current_workshop_id`), transitively through the order it belongs to. A payment on another workshop's order MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's order rejects a payment

- GIVEN workshop A has a work order and workshop B does not
- WHEN a user authenticated for workshop B attempts to record a payment against that order's id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND no payment is created

#### Scenario: Another workshop's payments are invisible

- GIVEN workshop A has recorded payments on its orders
- WHEN a user authenticated for workshop B lists payments for any of their own orders
- THEN none of workshop A's payments appear
