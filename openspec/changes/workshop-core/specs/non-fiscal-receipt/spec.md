# Non-Fiscal Receipt Specification

**Phase:** 3

## Purpose

A printable receipt for a completed or delivered work order, in two layouts (58 mm thermal and full page), both of which must be unmistakable as non-fiscal documents. SAR/CAI fiscal invoicing is out of scope for this entire change; the receipt exists to hand the customer a clear summary of the work and payment, never a tax document.

## Requirements

### Requirement: A Receipt Is Only Available For Completed Or Delivered Orders

The system MUST only render a receipt, in either layout, for a work order whose status is `completed` or `delivered`. A receipt request for an order in any other status (`quote`, `approved`, `in_progress`, or `cancelled`) MUST NOT render the order's data.

#### Scenario: A completed order's receipt renders

- GIVEN a work order in status `completed`
- WHEN either receipt route is opened
- THEN the receipt renders with that order's content

#### Scenario: A delivered order's receipt renders

- GIVEN a work order in status `delivered`
- WHEN either receipt route is opened
- THEN the receipt renders with that order's content

#### Scenario: An order not yet completed cannot be rendered as a receipt

- GIVEN a work order in status `quote`, `approved`, `in_progress`, or `cancelled`
- WHEN either receipt route is opened for that order
- THEN the order's content is not rendered
- AND a message explains that a receipt is only available once the order is completed or delivered

### Requirement: Two Independent Printable Layouts Are Available

The system MUST provide two independently rendered printable layouts for an eligible work order's receipt: a 58 mm thermal layout and a full-page layout, each its own route.

#### Scenario: 58 mm layout renders in print preview

- GIVEN a work order in status `completed` or `delivered`
- WHEN the 58 mm receipt route is opened and print preview is invoked
- THEN the page renders at 58 mm width with the order's content legible

#### Scenario: Full-page layout renders in print preview

- GIVEN a work order in status `completed` or `delivered`
- WHEN the full-page receipt route is opened and print preview is invoked
- THEN the page renders in a standard page size with the order's content legible

### Requirement: The 58 mm Layout's Printed Page Height Matches Its Content

The system MUST size the 58 mm layout's print page to the actual rendered height of its content, measured at render time, rather than an unmeasured fixed height. Until that measurement completes, the layout MUST fall back to a reasonable default page height, so the page is always valid to print.

#### Scenario: The printed page height matches the content

- GIVEN a work order eligible for a receipt, rendered on the 58 mm layout
- WHEN the content has finished rendering and print preview is invoked
- THEN the printed page's height matches the rendered content's height, with no large trailing blank area

#### Scenario: Printing before measurement still produces a valid page

- GIVEN the 58 mm layout has just mounted and its content height has not yet been measured
- WHEN print preview is invoked at that instant
- THEN the page still renders at a valid 58 mm width with a fallback page height

### Requirement: Both Layouts MUST Carry The Mandatory Non-Fiscal Label

Both the 58 mm and full-page layouts MUST display the visible text "DOCUMENTO NO FISCAL — No válido como factura", positioned so it is visible without scrolling in print preview.

#### Scenario: Non-fiscal label is visible on the thermal layout

- GIVEN the 58 mm receipt route is rendered
- WHEN the rendered output is inspected
- THEN "DOCUMENTO NO FISCAL — No válido como factura" is present and visible

#### Scenario: Non-fiscal label is visible on the full-page layout

- GIVEN the full-page receipt route is rendered
- WHEN the rendered output is inspected
- THEN "DOCUMENTO NO FISCAL — No válido como factura" is present and visible

### Requirement: Receipt Content Reflects The Order's Lines, Total, Payments, And Balance

The system MUST render, on both layouts, the work order's number, vehicle, customer name, each quote line with its quantity and subtotal, the order total, the sum of its non-voided recorded payments, and the resulting balance due.

#### Scenario: Receipt shows a fully paid order with zero balance

- GIVEN a work order with lines totaling 500.00 and payments totaling 500.00
- WHEN either receipt layout is rendered
- THEN the total shown is 500.00, the paid total shown is 500.00, and the balance due shown is 0.00

#### Scenario: Receipt shows a partially paid order with its balance due

- GIVEN a work order with lines totaling 500.00 and payments totaling 200.00
- WHEN either receipt layout is rendered
- THEN the balance due shown is 300.00

### Requirement: Receipt Data Is Isolated Per Workshop

The system MUST only render a receipt for a work order belonging to the authenticated workshop. A receipt request for another workshop's order MUST be treated as not found.

#### Scenario: Another workshop's order cannot be rendered

- GIVEN workshop A has a work order and workshop B does not
- WHEN a user authenticated for workshop B opens a receipt route for that order's id
- THEN the response is HTTP 404 with `detail: "work_order_not_found"`
- AND no order data from workshop A is rendered
