# Data Export Specification

**Phase:** 3

## Purpose

A one-tap "Exportar todo" export of the current workshop's data as a ZIP of per-entity CSVs, so a shop owner is never forced to stay on the product to keep access to their own data. This is read-only and introduces no new entity of its own; it composes existing per-feature data scoped exactly like every other inventory query.

## Requirements

### Requirement: The Export Produces A ZIP Of Per-Entity CSVs

The system MUST produce a single ZIP archive containing one CSV file per entity: customers, vehicles, items, inventory movements, work orders, work order lines, and payments.

#### Scenario: The export contains one file per entity

- GIVEN a workshop with data in every entity listed above
- WHEN "Exportar todo" is requested
- THEN the resulting ZIP contains exactly one CSV file for each of: customers, vehicles, items, inventory movements, work orders, work order lines, and payments

#### Scenario: An entity with no rows still produces an (empty-body) CSV

- GIVEN a workshop with no recorded payments
- WHEN "Exportar todo" is requested
- THEN the ZIP still contains a payments CSV with only a header row

### Requirement: Every CSV Is UTF-8 With A BOM For Excel Compatibility

The system MUST encode every CSV in the export using UTF-8 with a byte-order mark (`utf-8-sig`), so that Excel on Windows renders Spanish accented characters correctly instead of mojibake.

#### Scenario: Accented content survives a round trip through Excel

- GIVEN a customer named `José Núñez` exists in the workshop
- WHEN the customers CSV from the export is opened in Excel on Windows
- THEN `José Núñez` renders with its accent and tilde intact, not as mojibake

### Requirement: The Export Is Scoped Only By The Authenticated Workshop

The system MUST scope every row in every CSV by the authenticated user's workshop id (`get_current_workshop_id`), and MUST NOT accept or honor any client-supplied workshop id for scoping the export.

#### Scenario: Export contains only the requesting workshop's data

- GIVEN workshop A and workshop B each have customers, vehicles, items, and orders
- WHEN a user authenticated for workshop A requests "Exportar todo"
- THEN every row in every CSV belongs to workshop A
- AND no row from workshop B appears anywhere in the ZIP

#### Scenario: A client-supplied workshop id is ignored

- GIVEN a user authenticated for workshop A
- WHEN an export request attempts to pass a different workshop id as a parameter
- THEN the export still scopes exclusively to workshop A, the authenticated workshop

### Requirement: The Export Requires A Live Connection

The system MUST require an active connection to generate and download the export; it is not served from the persisted offline query cache or any other client-side store.

#### Scenario: Export is unavailable offline

- GIVEN the device has no network connection
- WHEN the user triggers "Exportar todo"
- THEN a Spanish message explains that exporting requires a connection
- AND no partial or stale export is downloaded

### Requirement: Repeating An Export Is Side-Effect Free

The system MUST treat every export request as a read: requesting "Exportar todo" any number of times MUST produce a fresh read of the workshop's current data and MUST NOT create, modify, or delete any record.

#### Scenario: Two consecutive exports reflect the same state unchanged

- GIVEN no writes occur between two export requests
- WHEN "Exportar todo" is requested twice in a row
- THEN both ZIPs contain the same rows
- AND no database record was created, modified, or deleted by either request

### Requirement: Each CSV Is Internally Consistent; Consistency Across Files Under Concurrent Writes Is Best-Effort

The system MUST produce every CSV in the export as one internally consistent read of its own entity's rows: a CSV MUST NOT contain a partial row, a duplicated row, or a row reflecting two different states of the same record. When no write occurs to any entity while an export is in progress, every CSV in the resulting ZIP MUST reflect that one same moment. When a write does occur to one entity while a different entity's CSV is being produced, the two CSVs MAY reflect slightly different moments; the export MUST NOT be required to hold one transactional snapshot across every entity to satisfy this capability.

#### Scenario: No writes during the export yields one consistent moment across every file

- GIVEN no writes occur to any entity while the export is in progress
- WHEN the export finishes
- THEN every CSV in the ZIP reflects that same moment in time

#### Scenario: A write to one entity during the export does not corrupt another entity's file

- GIVEN a write to the payments table happens while the export is being generated
- WHEN the export finishes
- THEN the payments CSV may or may not include that write
- AND every CSV's own rows remain internally consistent, with no partial or duplicated row
