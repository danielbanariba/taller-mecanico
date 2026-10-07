# Daily Cash Summary Specification

**Phase:** 3

## Purpose

A per-day summary of the current workshop's recorded payments, broken down by payment method, so the owner can reconcile the physical cash drawer against cash payments and see totals for other methods. The day boundary is a fixed `America/Tegucigalpa` calendar day; there is no per-workshop timezone setting.

## Requirements

### Requirement: The Summary Is Scoped To The Authenticated Workshop And A Single Calendar Day

The system MUST compute the daily cash summary only from payments belonging to the authenticated workshop (`get_current_workshop_id`), for a single calendar day.

#### Scenario: Only the current workshop's payments are included

- GIVEN workshop A and workshop B each recorded payments today
- WHEN a user authenticated for workshop A requests today's summary
- THEN only workshop A's payments contribute to the totals

### Requirement: The Day Boundary Is The America/Tegucigalpa Calendar Day

The system MUST determine which calendar day a payment belongs to using the `America/Tegucigalpa` time zone (UTC-6), regardless of the server's own time zone or any client time zone.

#### Scenario: A payment near midnight local time is bucketed correctly

- GIVEN a payment recorded at `2026-10-07T05:59:00Z` (23:59 on October 6 in `America/Tegucigalpa`)
- WHEN the summary for October 6 (Honduras local) is requested
- THEN that payment is included in October 6's totals, not October 7's

#### Scenario: A payment just after local midnight is bucketed correctly

- GIVEN a payment recorded at `2026-10-07T06:01:00Z` (00:01 on October 7 in `America/Tegucigalpa`)
- WHEN the summary for October 7 (Honduras local) is requested
- THEN that payment is included in October 7's totals, not October 6's

### Requirement: Totals Are Broken Down By Payment Method

The system MUST report, for the requested day, a total for each of the four payment methods (cash, transfer, card, other) and a grand total.

#### Scenario: Mixed-method totals

- GIVEN today's payments for the workshop are 300.00 cash, 150.00 transfer, and 50.00 card
- WHEN today's summary is requested
- THEN the cash total is 300.00, the transfer total is 150.00, the card total is 50.00, the other total is 0.00
- AND the grand total is 500.00

### Requirement: Voided Payments Are Excluded From The Summary

The system MUST exclude every voided payment from the daily cash summary, both from its per-method totals and from its grand total, as though the voided payment had never been recorded.

#### Scenario: A voided payment does not contribute to its method's total

- GIVEN a payment of 200.00 cash recorded today was later voided with a reason
- WHEN today's summary is requested
- THEN the cash total and the grand total do not include that 200.00
- AND that voided payment does not appear in the day's listed payments

### Requirement: The Summary Requires A Live Connection

The system MUST fetch the daily cash summary from the API when requested; it is not served from the persisted offline query cache, since it must reflect the authoritative, current server-side state of the day's payments.

#### Scenario: Summary is unavailable offline

- GIVEN the device has no network connection
- WHEN the user opens the daily cash summary screen
- THEN a Spanish message explains that the summary requires a connection
- AND no stale totals are shown as if they were current
