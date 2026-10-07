# Customers Specification

**Phase:** 1

## Purpose

Customer records belonging to one workshop: creation, editing, soft archiving, listing, and accent-insensitive search. A customer's phone is optional and, when present, is normalized and classified as mobile or landline so later phases (WhatsApp sharing) can offer mobile-only actions. This capability follows the same tenancy, idempotency, and online-only-write conventions already established by the inventory feature's `Item`.

## Requirements

### Requirement: Customer Creation Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when creating a customer. A create request replayed with the exact same id and payload MUST be a no-op that returns the existing customer (HTTP 200). A create request reusing an existing id with a different payload MUST fail with `customer_id_conflict` (HTTP 409).

#### Scenario: Replaying an identical create is a no-op

- GIVEN a customer was already created with client-generated id `C1` and a given payload
- WHEN the same create request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing customer
- AND no second customer row is created

#### Scenario: Reusing an id with a different payload is a conflict

- GIVEN a customer already exists with client-generated id `C1`
- WHEN a create request reuses `C1` with a different `full_name`
- THEN the response is HTTP 409 with `detail: "customer_id_conflict"`
- AND the existing customer is unchanged

### Requirement: Customer Phone Is Optional And Normalized When Present

The customer's phone MUST be optional. When provided, it MUST be validated and normalized by the identity feature's existing `PhoneNumber` value object, unchanged. `PhoneNumber` strips separators and an optional `+504` prefix, requires 8 digits, and accepts a first digit from `2` to `9` (`_FIRST_DIGITS = "23456789"`). The system MUST derive and expose `phone_is_mobile` as `first_digit != "2"` (`null` when no phone is recorded): a phone whose normalized first digit is `2` is a landline, and any other accepted first digit is a mobile. A phone that fails `PhoneNumber` validation MUST be rejected with HTTP 422 and `detail: "invalid_phone"` (the same code identity already uses for an invalid phone, so the web shows one Spanish message for both). The identity feature's `PhoneNumber` and its login validation rules MUST NOT be modified by this capability.

#### Scenario: A landline is accepted and normalized

- GIVEN a create or edit request with phone `+504 2234-5678`
- WHEN the request is processed
- THEN the stored phone is `22345678`
- AND `phone_is_mobile` is `false`

#### Scenario: A mobile number is accepted and classified

- GIVEN a create or edit request with phone `9876-5432`
- WHEN the request is processed
- THEN the stored phone is `98765432`
- AND `phone_is_mobile` is `true`

#### Scenario: An empty phone is accepted

- GIVEN a create or edit request with no phone value
- WHEN the request is processed
- THEN the customer is saved with no phone
- AND `phone_is_mobile` is `null`

#### Scenario: An invalid phone is rejected

- GIVEN a create or edit request with a 7-digit phone, or a phone starting with `1`
- WHEN the request is processed
- THEN the response is HTTP 422 with `detail: "invalid_phone"`
- AND no customer is created or modified

### Requirement: Customer Edit

The system MUST allow updating a customer's editable fields (at minimum, name and phone) for a customer belonging to the authenticated workshop. Omitted fields MUST remain unchanged; the phone field follows the same normalization and validation as creation.

#### Scenario: Editing a customer's name

- GIVEN an active customer belonging to the authenticated workshop
- WHEN an edit request changes only the name
- THEN the name is updated
- AND the phone and mobile/landline flag are unchanged

#### Scenario: Editing a nonexistent or foreign customer

- GIVEN a customer id that does not exist, or belongs to another workshop
- WHEN an edit request targets that id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`

### Requirement: Customer Archive Is Soft And Idempotent

The system MUST archive a customer by setting an `archived_at` timestamp rather than deleting the row. Archiving an already-archived customer MUST be a no-op that succeeds without changing `archived_at` again.

#### Scenario: Archiving an active customer

- GIVEN an active customer belonging to the authenticated workshop
- WHEN an archive request is sent
- THEN the customer's `archived_at` is set
- AND the customer no longer appears in the default (active-only) listing

#### Scenario: Archiving an already-archived customer is idempotent

- GIVEN a customer already archived at time `T`
- WHEN another archive request is sent for the same customer
- THEN the response succeeds
- AND `archived_at` remains `T`

#### Scenario: Archiving a customer from another workshop

- GIVEN a customer id belonging to another workshop
- WHEN an archive request targets that id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`
- AND the other workshop's customer is unaffected

### Requirement: Customer Listing And Accent-Insensitive Search

The system MUST list customers scoped to the authenticated workshop, and MUST support an accent-insensitive, case-insensitive search by name or by phone, consistent with the existing `taller_unaccent_lower` search idiom used for items.

#### Scenario: Searching without accents finds an accented name

- GIVEN a customer named `María` exists in the workshop
- WHEN the list endpoint is called with search query `maria`
- THEN the result includes that customer

#### Scenario: Searching by phone fragment

- GIVEN a customer with phone `98765432` exists
- WHEN the list endpoint is called with search query `9876`
- THEN the result includes that customer

### Requirement: Customer Search Also Matches The Normalized Plates Of Their Active Vehicles

The search query MUST also match a customer through the normalized plates of that customer's active (non-archived) vehicles, in addition to matching by name or phone. A plate on an archived vehicle MUST NOT be searchable through this match.

#### Scenario: Searching by a vehicle's plate finds its owner

- GIVEN a customer owns an active vehicle with normalized plate `HAB1234`
- WHEN the list endpoint is called with search query `hab1234`
- THEN the result includes that customer

#### Scenario: Searching by a partial plate finds the owner

- GIVEN a customer owns an active vehicle with normalized plate `HAB1234`
- WHEN the list endpoint is called with search query `hab12`
- THEN the result includes that customer

#### Scenario: A plate on an archived vehicle is not searchable

- GIVEN a customer's only vehicle with plate `HAB1234` has been archived
- WHEN the list endpoint is called with search query `hab1234`
- THEN that customer is not included in the result on the basis of the plate match alone

### Requirement: Customer Writes Require A Live Connection; Reads Stay Available Offline

The system MUST disable customer create, edit, and archive actions in the UI with a Spanish message when the device is offline, the same treatment item create/edit already receives. Customer list and detail reads MUST remain available offline from the persisted query cache, using `workshopQueryKey`-prefixed query keys.

#### Scenario: Create is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the new-customer form
- THEN the submit action is disabled
- AND a Spanish message explains that creating a customer requires a connection

#### Scenario: A previously visited customer list renders offline

- GIVEN the customer list was fetched while online and is cached
- WHEN the device goes offline and the user revisits the customer list
- THEN the previously fetched customers still render from the persisted cache

### Requirement: Customer Data Is Isolated Per Workshop

The system MUST scope every customer query and mutation by the authenticated user's workshop id (`get_current_workshop_id`). A customer belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's customer is invisible

- GIVEN workshop A has a customer and workshop B does not
- WHEN a user authenticated for workshop B requests that customer by id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`

#### Scenario: Another workshop's customer cannot be mutated

- GIVEN workshop A has a customer
- WHEN a user authenticated for workshop B sends an edit or archive request for that customer's id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`
- AND workshop A's customer is unchanged
