# Fiscal Profile Specification

**Phase:** A

## Purpose

One optional fiscal profile per workshop, holding the issuer data SAR requires on every Factura and Nota de Crédito (Art. 10–11): RTN, razón social, nombre comercial, address, phone, email, establecimiento code, and punto de emisión code. A workshop that never saves a complete profile has no row and sees no invoicing capability anywhere in the product — opting in is driven entirely by data, never by a separate toggle. This capability also owns the in-app SAR registration notice and the shell's entry point to the settings screen; it never contacts SAR itself.

## Requirements

### Requirement: The Fiscal Profile Holds Every Art. 10–11 Issuer Field, Scoped To One Workshop

The system MUST store at most one fiscal profile per workshop, keyed by `workshop_id`, holding: RTN, razón social, nombre comercial, address, phone, email, establecimiento code, and punto de emisión code. When present, the workshop's own RTN MUST be exactly 14 digits after stripping separators, with no check-digit validation in v1 (the same rule as a customer's RTN, per the `customers` delta). A workshop that has never saved a profile MUST have no row in this table, and `identity`'s `Workshop` and `WorkshopRepository` MUST remain unmodified.

#### Scenario: Saving a complete profile for the first time

- GIVEN a workshop with no fiscal profile
- WHEN a profile is saved with every required field, including a 14-digit RTN
- THEN the profile is stored against that workshop's id

#### Scenario: An RTN that is not 14 digits after stripping separators is rejected

- GIVEN a profile save request whose RTN, after stripping hyphens and spaces, has 13 or 15 digits
- WHEN the request is processed
- THEN the response is HTTP 422 with `detail: "invalid_rtn"`
- AND the profile is not saved

#### Scenario: A workshop that never saves a profile has no row

- GIVEN a workshop that has never saved a fiscal profile
- WHEN its fiscal profile is requested
- THEN the response indicates no profile exists
- AND no other area of the product (orders, settings) offers any invoicing action

### Requirement: The Fiscal Profile Is Complete Only When Every Field Is Present

The system MUST consider a fiscal profile "complete" only when RTN, razón social, nombre comercial, address, phone, email, establecimiento code, and punto de emisión code are all present and valid. Profile completeness is one half of the data-driven opt-in gate for invoicing (the other half, an active CAI range, is defined by `cai-ranges`); a profile missing any one of these fields MUST be treated as incomplete, and invoicing MUST stay unavailable.

#### Scenario: A profile missing one field is incomplete

- GIVEN a workshop's saved profile has every field except punto de emisión code
- WHEN invoicing eligibility is evaluated for that workshop
- THEN the profile is reported incomplete
- AND no Factura or Nota de Crédito can be issued, regardless of any CAI range that exists

### Requirement: Saving The Fiscal Profile Is An Idempotent Upsert Per Workshop

The system MUST treat a profile save as an idempotent upsert keyed by the workshop: saving the exact same payload again MUST leave the stored profile unchanged, and saving a payload that differs only in the fields the workshop intends to change MUST update exactly those fields. There is no concept of a conflicting profile id to reject, because the profile's natural key is the workshop itself, not a client-generated id.

#### Scenario: Repeating an identical save changes nothing

- GIVEN a workshop's fiscal profile was already saved with a given payload
- WHEN the exact same save request is sent again
- THEN the response succeeds
- AND the stored profile is unchanged

#### Scenario: A later save updates only the fields that changed

- GIVEN a workshop's fiscal profile is already saved
- WHEN a save request repeats every field except a new phone number
- THEN only the phone number is updated
- AND every other field keeps its previous value

### Requirement: Establecimiento And Punto De Emisión Codes Are Locked While An Unexhausted Range Exists

The system MUST reject an edit to the profile's establecimiento code or punto de emisión code while the workshop has any CAI range, of any document type, that is neither exhausted nor past its fecha límite — because a CAI is authorized per punto de emisión (Art. 59), so changing either code would invalidate every number still available on that range. The response MUST be HTTP 409 with `detail: "fiscal_profile_codes_locked"`. Every other profile field remains editable regardless of range state.

#### Scenario: Editing the codes before any range exists

- GIVEN a workshop with a saved profile and no CAI range yet
- WHEN the profile edit changes the punto de emisión code
- THEN the edit succeeds

#### Scenario: Editing the codes while an active range exists is rejected

- GIVEN a workshop with an active, unexhausted CAI range
- WHEN the profile edit changes the establecimiento code or the punto de emisión code
- THEN the response is HTTP 409 with `detail: "fiscal_profile_codes_locked"`
- AND the profile's codes are unchanged

#### Scenario: Editing the codes once every range is exhausted or expired is allowed

- GIVEN a workshop whose every CAI range is either fully exhausted or past its fecha límite
- WHEN the profile edit changes the punto de emisión code
- THEN the edit succeeds

### Requirement: The Settings Screen Shows The In-App SAR Registration Notice

The system MUST display, on the fiscal settings screen, a notice stating that the workshop must register the system with SAR and file the Declaración Jurada (Art. 47, 53), must confirm the module with its own contador before issuing real documents, and — if it intends to print on 58 mm thermal paper — needs paper certified for at least 5 years of legibility (Art. 38). This notice MUST be shown whether or not the profile is complete.

#### Scenario: The notice is shown before the profile is complete

- GIVEN a workshop with no saved fiscal profile
- WHEN the fiscal settings screen is opened
- THEN the SAR registration, contador, and thermal-paper notices are all visible

#### Scenario: The notice is still shown after the profile is complete

- GIVEN a workshop with a complete fiscal profile
- WHEN the fiscal settings screen is opened
- THEN the same notices are still visible

### Requirement: The Fiscal Settings Screen Is Reached From The Shell's "Más" Menu

The system MUST add an entry to the app shell's "Más" menu that opens the fiscal settings screen, alongside the existing "Caja del día", "Exportar todo", and "Cerrar sesión" entries. This entry MUST be visible regardless of whether the workshop has a fiscal profile yet, since it is also the only way to create the first one.

#### Scenario: The menu entry is visible with no profile yet

- GIVEN a workshop with no fiscal profile
- WHEN the "Más" menu is opened
- THEN an entry for fiscal settings is visible and opens the settings screen

### Requirement: Fiscal Profile Writes Require A Live Connection; Reads Stay Available Offline

The system MUST disable saving or editing the fiscal profile in the UI with a Spanish message when the device is offline. The current profile MUST remain readable offline from the persisted query cache, using a `workshopQueryKey`-prefixed query key.

#### Scenario: Saving the profile is disabled while offline

- GIVEN the device has no network connection
- WHEN the user opens the fiscal settings screen and attempts to save
- THEN the save action is disabled
- AND a Spanish message explains that saving the fiscal profile requires a connection

#### Scenario: A previously fetched profile renders offline

- GIVEN a workshop's fiscal profile was fetched while online and is cached
- WHEN the device goes offline and the settings screen is revisited
- THEN the previously fetched profile still renders from the persisted cache

### Requirement: The Fiscal Profile Is Isolated Per Workshop

The system MUST scope every fiscal profile read and write by the authenticated user's workshop id (`get_current_workshop_id`). A fiscal profile belonging to another workshop MUST be indistinguishable from a nonexistent one.

#### Scenario: Another workshop's profile is invisible

- GIVEN workshop A has a fiscal profile and workshop B does not
- WHEN a user authenticated for workshop B requests the fiscal profile
- THEN the response reports no profile for workshop B
- AND none of workshop A's data is returned
