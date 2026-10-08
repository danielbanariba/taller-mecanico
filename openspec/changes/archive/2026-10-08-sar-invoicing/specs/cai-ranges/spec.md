# CAI Ranges Specification

**Phase:** A

## Purpose

A CAI range authorizes a bounded, gap-free run of document numbers of one SAR document type (`01` Factura in Phase A, `06` Nota de Crédito from Phase B) for one workshop: the CAI itself, the range's start and end correlatives, and its fecha límite de emisión. Allocation happens under a per-range row lock so concurrent issuance never skips or duplicates a number, and the range enforces its own boundaries — exhaustion and the fecha límite (Art. 62) — without ever contacting SAR. The workshop obtains its own CAI from SAR and types it in; this capability only enforces the bounds it is told.

## Requirements

### Requirement: A CAI Range Is Registered Per Document Type With Its CAI, Bounds, And Fecha Límite

The system MUST allow a workshop to register a CAI range holding: a document type, the CAI string, a range start and end correlative, and a fecha límite de emisión (a calendar date). A range's `next_correlative` MUST start at its `range_start`. In Phase A the only accepted document type is `01`; a `06` range MUST be rejected with HTTP 422 `detail: "unsupported_document_type"`. From Phase B, `06` is accepted as well. The schema allows both from the start, so Phase B needs no schema change.

#### Scenario: Registering a Factura range

- GIVEN a workshop with a complete fiscal profile
- WHEN a CAI range of document type `01` is registered with a CAI, bounds `00000001`–`00000100`, and a fecha límite
- THEN the range is stored with `next_correlative` at `00000001`

#### Scenario: A credit-note range is rejected before Phase B

- GIVEN Phase A is deployed and Phase B is not
- WHEN a CAI range of document type `06` is registered
- THEN the response is HTTP 422 with `detail: "unsupported_document_type"`
- AND no range is stored

### Requirement: CAI Range Registration Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when registering a range. A registration request replayed with the exact same id and payload MUST be a no-op that returns the existing range (HTTP 200). A request reusing an existing range id with a different payload MUST fail with `detail: "cai_range_id_conflict"` (HTTP 409).

#### Scenario: Replaying an identical registration is a no-op

- GIVEN a range was already registered with client-generated id `R1`
- WHEN the same registration request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing range
- AND no second range row is created

#### Scenario: Reusing a range id with a different payload is a conflict

- GIVEN a range already exists with client-generated id `R1`
- WHEN a registration request reuses `R1` with a different CAI
- THEN the response is HTTP 409 with `detail: "cai_range_id_conflict"`
- AND the existing range is unchanged

### Requirement: Overlapping Ranges Of The Same Document Type Are Rejected

The system MUST reject registering a new range whose `[range_start, range_end]` interval overlaps an existing range of the same document type for that workshop, with `detail: "cai_range_overlap"` (HTTP 409). Ranges of different document types MAY share the same numeric bounds, since each document type's numbering is independent.

#### Scenario: An overlapping range of the same type is rejected

- GIVEN a workshop with a Factura range covering `00000001`–`00000100`
- WHEN a new Factura range covering `00000050`–`00000150` is registered
- THEN the response is HTTP 409 with `detail: "cai_range_overlap"`
- AND no new range is created

#### Scenario: Identical bounds on a different document type are allowed

- GIVEN a workshop with a Factura range covering `00000001`–`00000100`
- WHEN a Nota de Crédito range covering `00000001`–`00000100` is registered
- THEN the new range is created

### Requirement: A Range Becomes Immutable Once A Number Has Been Taken From It

The system MUST allow editing or deleting a range only while no number has ever been allocated from it (`next_correlative` still equals `range_start`). Once at least one number has been taken, an edit or delete request MUST fail with `detail: "cai_range_immutable"` (HTTP 409).

#### Scenario: Editing an untouched range succeeds

- GIVEN a range from which no number has ever been allocated
- WHEN the range's fecha límite is corrected
- THEN the edit succeeds

#### Scenario: Editing a range that has issued a document is rejected

- GIVEN a range from which at least one document has already been issued
- WHEN an edit to that range's CAI or bounds is requested
- THEN the response is HTTP 409 with `detail: "cai_range_immutable"`
- AND the range is unchanged

### Requirement: At Most One Range Is Active For Allocation Per Document Type

The system MUST ensure that, for each document type, at most one of a workshop's registered ranges is the one correlatives are allocated from at any time (the "active" range). Registering a second, later range of the same type while the first is still usable MUST succeed, but MUST NOT make that second range active or draw from it; issuance for that document type MUST always draw its next correlative from the single active range. Exactly which registered range becomes active next, once the current one is exhausted or expired, is left to `sdd-design`.

#### Scenario: A second range does not interfere with the active one

- GIVEN a workshop with an active, unexhausted Factura range, and a second Factura range registered for future use
- WHEN a Factura is issued
- THEN its number is allocated from the first (active) range
- AND the second range's `next_correlative` is unchanged

### Requirement: Issuance Is Blocked When The Active Range Is Exhausted

The system MUST block allocating a correlative once the active range's `next_correlative` would exceed its `range_end`, with `detail: "cai_range_exhausted"` (HTTP 409). No number already allocated is ever reused.

#### Scenario: The last number in a range is allocated normally

- GIVEN an active range whose `next_correlative` is its `range_end`
- WHEN a document is issued
- THEN that last correlative is allocated

#### Scenario: Issuance is blocked once the range is exhausted

- GIVEN an active range whose `range_end` correlative has already been allocated
- WHEN another document of that type is issued
- THEN the response is HTTP 409 with `detail: "cai_range_exhausted"`
- AND no document is created

### Requirement: Issuance Is Blocked After The Fecha Límite, Compared As An America/Tegucigalpa Calendar Date, Inclusive Of That Day

The system MUST block allocating a correlative once the current date, in the `America/Tegucigalpa` time zone and read through the injectable `Clock`, is strictly after the range's fecha límite (Art. 62). Issuance on the fecha límite's own calendar day MUST still succeed. The comparison MUST use the America/Tegucigalpa calendar date, never the server's or the request's UTC date, so a UTC day boundary never causes an incorrect block or an incorrect allow.

#### Scenario: Issuance succeeds on the fecha límite day itself

- GIVEN an active range whose fecha límite is today's date in `America/Tegucigalpa`
- WHEN a document is issued
- THEN the issuance succeeds

#### Scenario: Issuance is blocked the day after the fecha límite

- GIVEN an active range whose fecha límite was yesterday's date in `America/Tegucigalpa`
- WHEN a document is issued
- THEN the response is HTTP 409 with `detail: "cai_range_expired"`
- AND no document is created

#### Scenario: A UTC day boundary does not cause an incorrect allow or block

- GIVEN an active range whose fecha límite is `2026-10-09`, and the current instant is `2026-10-10T02:00:00Z` (which is `2026-10-09T20:00:00` in `America/Tegucigalpa`, UTC-6)
- WHEN a document is issued
- THEN the issuance succeeds, because the America/Tegucigalpa calendar date is still the fecha límite day

### Requirement: Correlative Allocation Is Gap-Free And Row-Locked Under Concurrency

The system MUST allocate each range's correlatives by locking that range's row (`FOR UPDATE`) before reading and incrementing `next_correlative`, so two concurrent issuances against the same range never observe or allocate the same number, and no number is ever skipped. An idempotent replay of an already-issued document (per `fiscal-invoices` and `credit-notes`) MUST NOT allocate another number.

#### Scenario: Concurrent issuance never skips or duplicates a number

- GIVEN an active range with no number yet allocated
- WHEN two issuance requests against that range are submitted concurrently
- THEN both succeed with two distinct, sequential correlatives
- AND neither request observes the other's number

#### Scenario: Replaying an issuance does not consume a number

- GIVEN a document was already issued, allocating correlative `00000005`
- WHEN the exact same issuance request (same client id, same payload) is sent again
- THEN the response returns the existing document, still numbered `00000005`
- AND the range's `next_correlative` is not advanced again

### Requirement: CAI Ranges Are Isolated Per Workshop

The system MUST scope every CAI range read and write by the authenticated user's workshop id (`get_current_workshop_id`). A range belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's range is invisible

- GIVEN workshop A has a CAI range and workshop B does not
- WHEN a user authenticated for workshop B requests that range by id
- THEN the response reports it as not found

### Requirement: Range Warnings Are Shown From 60 Days Before The Fecha Límite And When Few Numbers Remain

**Phase:** B

The system MUST surface a warning on the fiscal settings screen starting 60 days before a range's fecha límite — matching Art. 59's 2-month window for requesting the next range — and MUST surface a separate warning once the range's remaining numbers fall below a threshold fixed by `sdd-design`.

> **Design-dependent:** the exact low-remaining-numbers threshold is fixed by `sdd-design`. The scenario below is written to hold for whatever threshold value design chooses.

#### Scenario: A warning appears exactly 60 days before the fecha límite

- GIVEN an active range whose fecha límite is exactly 60 days from the current America/Tegucigalpa date
- WHEN the fiscal settings screen is viewed
- THEN a fecha-límite warning is shown for that range

#### Scenario: No fecha-límite warning appears more than 60 days out

- GIVEN an active range whose fecha límite is 61 days from the current America/Tegucigalpa date
- WHEN the fiscal settings screen is viewed
- THEN no fecha-límite warning is shown for that range yet

#### Scenario: A low-remaining-numbers warning appears once remaining numbers fall below the design-fixed threshold

- GIVEN an active range whose remaining numbers have fallen at or below the threshold `sdd-design` fixes
- WHEN the fiscal settings screen is viewed
- THEN a low-remaining-numbers warning is shown for that range
