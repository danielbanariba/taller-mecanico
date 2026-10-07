# Vehicles Specification

**Phase:** 1

## Purpose

Vehicles belong to exactly one customer within a workshop. A vehicle's plate is optional, normalized, and unique per workshop among active (non-archived) vehicles. This capability follows the same tenancy, idempotency, and online-only-write conventions already established by the inventory feature's `Item`.

## Requirements

### Requirement: A Vehicle Belongs To Exactly One Customer

The system MUST associate every vehicle with exactly one customer of the authenticated workshop at creation time.

#### Scenario: Creating a vehicle for an existing customer

- GIVEN an active customer belonging to the authenticated workshop
- WHEN a vehicle is created referencing that customer's id
- THEN the vehicle is saved with that customer as its owner

#### Scenario: Creating a vehicle for a nonexistent or foreign customer

- GIVEN a customer id that does not exist, or belongs to another workshop
- WHEN a vehicle create request references that customer id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`
- AND no vehicle is created

#### Scenario: Creating a vehicle for an archived customer is rejected

- GIVEN a customer that has been archived
- WHEN a vehicle create request references that customer's id
- THEN the response is HTTP 404 with `detail: "customer_not_found"`
- AND no vehicle is created

### Requirement: A Vehicle's Owning Customer Never Changes After Creation

The system MUST NOT expose `customer_id` as an editable field. Once a vehicle is created, its owning customer MUST remain fixed for the lifetime of the vehicle; the only way to change a vehicle's owner is to archive it and register a new vehicle for the correct customer.

#### Scenario: An edit request cannot reassign a vehicle to a different customer

- GIVEN an active vehicle belonging to customer `C1`
- WHEN an edit request is sent for that vehicle, with or without a different customer id in the payload
- THEN the vehicle's owner remains `C1`
- AND the edit endpoint does not accept `customer_id` as part of the editable payload

### Requirement: Archiving A Customer Cascades To Archive Its Active Vehicles

The system MUST archive every active vehicle owned by a customer, stamped with the same `archived_at` timestamp as the customer, when that customer is archived. This frees each of those vehicles' plates for reuse under the usual per-workshop active-plate uniqueness rule. Existing work orders referencing a vehicle archived this way keep working; only new links to that vehicle are refused afterward.

#### Scenario: Archiving a customer archives its active vehicles

- GIVEN a customer with two active vehicles, one of them plated `HAB1234`
- WHEN the customer is archived
- THEN both vehicles are archived with the same `archived_at` timestamp as the customer
- AND plate `HAB1234` becomes available for a new active vehicle in the workshop

#### Scenario: An already-archived vehicle is unaffected by the cascade

- GIVEN a customer has one vehicle already archived at time `T0`, before the customer itself is archived
- WHEN the customer is archived
- THEN that vehicle's `archived_at` remains `T0`

### Requirement: Vehicle Creation Is Idempotent By Client-Generated Id

The system MUST accept a client-generated id when creating a vehicle. A create request replayed with the exact same id and payload MUST be a no-op that returns the existing vehicle (HTTP 200). A create request reusing an existing id with a different payload MUST fail with `vehicle_id_conflict` (HTTP 409).

#### Scenario: Replaying an identical create is a no-op

- GIVEN a vehicle was already created with client-generated id `V1` and a given payload
- WHEN the same create request (same id, same payload) is sent again
- THEN the response is HTTP 200 with the existing vehicle
- AND no second vehicle row is created

#### Scenario: Reusing an id with a different payload is a conflict

- GIVEN a vehicle already exists with client-generated id `V1`
- WHEN a create request reuses `V1` with a different plate
- THEN the response is HTTP 409 with `detail: "vehicle_id_conflict"`
- AND the existing vehicle is unchanged

### Requirement: Plate Is Optional, Normalized, And Unique Per Workshop Among Active Vehicles

The plate MUST be optional: a vehicle with no plate MUST always be allowed, and the system MUST allow any number of unplated vehicles in the same workshop. When a plate is provided, the system MUST normalize it (uppercase, separators removed) and store only the normalized form. The normalized plate MUST be unique among a workshop's active (non-archived) vehicles; archiving a vehicle MUST free its plate for reuse.

#### Scenario: A plate is normalized on save

- GIVEN a create or edit request with plate `hab-1234`
- WHEN the request is processed
- THEN the stored plate is `HAB1234`

#### Scenario: A duplicate active plate is rejected

- GIVEN an active vehicle in the workshop already has normalized plate `HAB1234`
- WHEN a second active vehicle in the same workshop is created or edited with plate `HAB 1234`
- THEN the response is HTTP 409 with `detail: "plate_taken"`
- AND no second vehicle with that plate is created

#### Scenario: Several unplated vehicles are allowed

- GIVEN a workshop with one or more vehicles that have no plate
- WHEN another vehicle is created with no plate
- THEN the creation succeeds
- AND no uniqueness conflict is raised

#### Scenario: A plate freed by archiving can be reused

- GIVEN an active vehicle with plate `HAB1234` is archived
- WHEN a new vehicle is created in the same workshop with plate `HAB1234`
- THEN the creation succeeds

#### Scenario: A plate unique to one workshop does not block another workshop

- GIVEN workshop A has an active vehicle with plate `HAB1234`
- WHEN workshop B creates a vehicle with plate `HAB1234`
- THEN workshop B's creation succeeds

### Requirement: Vehicle Edit

The system MUST allow updating a vehicle's editable fields (at minimum, plate and any free-text attributes such as make, model, or year) for a vehicle belonging to the authenticated workshop. The plate follows the same normalization and uniqueness rules as creation.

#### Scenario: Editing a vehicle's plate

- GIVEN an active, unplated vehicle belonging to the authenticated workshop
- WHEN an edit request sets plate `XYZ9999`
- THEN the stored plate becomes `XYZ9999`

#### Scenario: Editing a nonexistent or foreign vehicle

- GIVEN a vehicle id that does not exist, or belongs to another workshop
- WHEN an edit request targets that id
- THEN the response is HTTP 404 with `detail: "vehicle_not_found"`

### Requirement: Vehicle Archive Is Soft And Idempotent

The system MUST archive a vehicle by setting an `archived_at` timestamp rather than deleting the row. Archiving an already-archived vehicle MUST be a no-op that succeeds without changing `archived_at` again.

#### Scenario: Archiving an active vehicle

- GIVEN an active vehicle belonging to the authenticated workshop
- WHEN an archive request is sent
- THEN the vehicle's `archived_at` is set
- AND the vehicle no longer appears in the default (active-only) listing for its customer

#### Scenario: Archiving an already-archived vehicle is idempotent

- GIVEN a vehicle already archived at time `T`
- WHEN another archive request is sent for the same vehicle
- THEN the response succeeds
- AND `archived_at` remains `T`

### Requirement: Vehicle Listing Per Customer And Vehicle Detail

The system MUST list a customer's vehicles scoped to the authenticated workshop, and MUST expose a vehicle detail view showing that single vehicle's attributes.

#### Scenario: Listing a customer's vehicles

- GIVEN a customer with two active vehicles and one archived vehicle
- WHEN the vehicle list for that customer is requested without `include_archived`
- THEN only the two active vehicles are returned

#### Scenario: Vehicle detail for a nonexistent or foreign vehicle

- GIVEN a vehicle id that does not exist, or belongs to another workshop
- WHEN the vehicle detail endpoint is called with that id
- THEN the response is HTTP 404 with `detail: "vehicle_not_found"`

### Requirement: Vehicle Writes Require A Live Connection; Reads Stay Available Offline

The system MUST disable vehicle create, edit, and archive actions in the UI with a Spanish message when the device is offline. Vehicle list and detail reads MUST remain available offline from the persisted query cache, using `workshopQueryKey`-prefixed query keys.

#### Scenario: Create is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the new-vehicle form
- THEN the submit action is disabled
- AND a Spanish message explains that creating a vehicle requires a connection

#### Scenario: A previously visited vehicle detail renders offline

- GIVEN a vehicle's detail was fetched while online and is cached
- WHEN the device goes offline and the user revisits that vehicle's detail
- THEN the previously fetched vehicle still renders from the persisted cache

### Requirement: Vehicle Data Is Isolated Per Workshop

The system MUST scope every vehicle query and mutation by the authenticated user's workshop id (`get_current_workshop_id`). A vehicle belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's vehicle is invisible

- GIVEN workshop A has a vehicle and workshop B does not
- WHEN a user authenticated for workshop B requests that vehicle by id
- THEN the response is HTTP 404 with `detail: "vehicle_not_found"`

#### Scenario: Another workshop's vehicle cannot be mutated

- GIVEN workshop A has a vehicle
- WHEN a user authenticated for workshop B sends an edit or archive request for that vehicle's id
- THEN the response is HTTP 404 with `detail: "vehicle_not_found"`
- AND workshop A's vehicle is unchanged
