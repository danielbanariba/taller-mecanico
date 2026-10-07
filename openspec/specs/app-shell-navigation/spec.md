# App Shell Navigation Specification

**Phase:** 1

## Purpose

A mobile bottom-navigation shell wraps every protected route with three destinations (`Inventario`, `Clientes`, `Órdenes`), replacing the per-page header and logout button `InventoryPage` currently renders on its own. The shell is purely a web client-side concern: it renders no tenant data of its own and introduces no new API surface. Every screen it wraps keeps enforcing tenancy, idempotency, and the offline/online boundary exactly as its own capability spec defines.

## Requirements

### Requirement: Bottom Navigation Shell Wraps Every Protected Route

The system MUST render a bottom-navigation shell with exactly three destinations — `Inventario`, `Clientes`, `Órdenes` — around every route nested under the authenticated session guard (`RequireSession`'s outlet).

#### Scenario: Shell renders on every protected screen

- GIVEN an authenticated user navigates to any protected route (inventory list, item detail, customer list, etc.)
- WHEN the route renders
- THEN the bottom nav with `Inventario`, `Clientes`, `Órdenes` is visible
- AND the route's own content renders above the nav, not replaced by it

#### Scenario: Unauthenticated user never sees the shell

- GIVEN no active session
- WHEN the user is redirected to `/login`
- THEN the bottom-navigation shell is not rendered

### Requirement: Active Tab Reflects The Current Route

The system MUST visually mark the destination matching the current route as active, and MUST update that marking when the route changes.

#### Scenario: Navigating updates the active tab

- GIVEN the user is on `Inventario` with that tab marked active
- WHEN the user taps `Clientes`
- THEN the app navigates to the Clientes screen
- AND `Clientes` is now marked active while `Inventario` is not

### Requirement: Logout Is Available From The Shell

The system MUST offer the logout action from the navigation shell rather than from any individual page.

#### Scenario: Logout from the shell ends the session

- GIVEN an authenticated user viewing any protected screen
- WHEN the user triggers logout from the shell
- THEN the session is cleared
- AND the user is redirected to `/login`
- AND every cached query for the previous workshop is removed, consistent with the existing logout behavior

#### Scenario: Inventory no longer renders its own logout control

(Previously: `InventoryPage` rendered its own header with a logout button.)

- GIVEN the Inventario screen renders
- WHEN the page is inspected
- THEN no page-level logout control is present outside the shell

### Requirement: Órdenes Tab Shows A Placeholder Until Phase 2

The system MUST show the `Órdenes` destination in phase 1, but MUST render a "Próximamente" empty state instead of functional content until work orders ship.

#### Scenario: Órdenes placeholder in phase 1

- GIVEN phase 1 is deployed and phase 2 has not shipped
- WHEN the user taps `Órdenes`
- THEN a "Próximamente" empty state renders
- AND no request to a work-orders endpoint is made

### Requirement: Existing Inventory Flows Are Unaffected By The Shell

The system MUST preserve every existing inventory flow (list, detail, movement recording, physical count, offline-queued taps) unchanged after the shell wraps it.

#### Scenario: Inventory flows still work under the shell

- GIVEN the shell wraps the Inventario route
- WHEN the user lists items, opens an item's detail, records a movement, and performs a physical count
- THEN every action behaves exactly as it did before the shell was introduced

### Requirement: The Shell Itself Requires No Network Access

The system MUST render the navigation shell and allow tab switching entirely from client-side routing, independent of connectivity.

#### Scenario: Navigating between tabs while offline

- GIVEN the device is offline and a previously visited screen is cached
- WHEN the user switches tabs
- THEN the shell renders and the destination's cached content (if any) renders per that destination's own offline-read rules
- AND switching tabs itself makes no network request
