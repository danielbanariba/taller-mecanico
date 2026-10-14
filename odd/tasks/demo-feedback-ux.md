# demo-feedback-ux

## Objective

Fix the eight cheap UX problems a developer found while testing the public demo (a screen recording dated 2026-10-10), so the next demo shown to mechanics feels clear and polished.

## Problem

The feedback was checked against the code and the recording's frames before any work started:

- The "Sincronizando... / N cambios por enviar" banner pushes the whole page down and up about 30px on every stock tap, so the page flickers.
- The header's "Más" button stretches to about three times the workshop name. This is a bug: `Button` always applies `w-full`, `AppShell` adds `w-auto` on top, and no class merging decides between them.
- The bottom navigation shows the active tab only by text color, so a user can't tell which section they are in.
- Payments:
  - A cash payment larger than the balance is rejected ("El monto supera el saldo pendiente."). The mechanic expects to enter what the customer handed over and see the change ("vuelto").
  - With the balance at 0 the payment form stays active, and submitting it shows two errors at once.
- The new-order flow can only pick an existing customer. A new customer means leaving the flow for Clientes.
- A work order's status reads as plain bold text, with no visual badge.
- The shared `Dialog` is a centered modal. On a phone, a bottom sheet is the expected pattern.
- An item's category and unit are free-text fields with a native datalist, and nothing visual says the user can pick a used value or type a new one.

## Why

The app is shown to mechanics as a demo, and first impressions decide adoption. Every item above is something a first-time user hits in their first minutes.

## Scope

Web only (`web/`). No API, schema or migration change. Out of scope, for later: inventory import from Excel, pagination, cost price and margin, suppliers, a desktop layout, multi-user, and merging stock taps in the outbox.

## Constraints

- UI copy in Spanish (usted), in each feature's `copy.ts`. Code, identifiers and comments in English.
- No new runtime dependency unless the task says so; icons are inline SVG.
- The offline guarantees in `CLAUDE.md` stay intact: the outbox, the flush lock and the folded reads.
- Every printed page keeps `print:hidden` on non-printing chrome.
- Test Value Gate: every new test names the defect it catches, and pure styling gets no class-echo test.

## Delivery

- Branch `feat/demo-feedback-ux`, one PR at the end (`single-pr`), with one work-unit commit per task.
- Forecast: about 700 authored changed lines, tests included.
- Receipt-driven development is off for this clone (`gentle-ai review mode status`: off, clone_local), so ordinary checks apply. Each task gets an independent verifier pass.

## Tasks

Each task is delegated to a single writer inside the workflow, followed by an independent verifier.

- [x] **T1** Make `Button`/`LinkButton` width controllable without conflicting classes (a `fullWidth` prop, default `true`), drop every `w-full`+`w-auto` conflict, and make the header's "Más" trigger compact.
  - Acceptance: the "Más" button is only as wide as its label plus padding, and no Button/LinkButton call site renders both `w-full` and `w-auto`.
- [ ] **T2** Bottom navigation with an inline SVG icon per tab and an unmistakable active state (filled pill or indicator plus bold label), keeping `aria-current="page"`.
  - Acceptance: the active tab is distinguishable without relying on color alone.
- [ ] **T3** Sync status banner without layout shift: render it as a fixed overlay (toast-like) that never moves page content, and show "Sincronizando..." only when a flush is still running after a short delay (about 600 ms), so a fast sync shows nothing.
  - Acceptance: a flush that finishes inside the delay never shows the banner, a longer one does, and the offline and pending messages still appear.
- [ ] **T4** Shared `Dialog` as a bottom sheet on small screens (anchored to the bottom, full width, rounded top) and a centered modal from `sm` up, keeping its accessibility behavior (focus, Escape, labelled title).
  - Acceptance: every existing dialog test still passes.
- [ ] **T5** A shared work-order status badge (a colored chip per status: draft, approved, in_progress, completed, delivered, cancelled), used wherever an order's status is shown.
  - Acceptance: every status renders its Spanish label inside the badge in the list and the detail screens.
- [ ] **T6** Payments:
  - for cash, accept the amount received; when it is larger than the balance, show "Vuelto" and record only the balance;
  - non-cash methods keep rejecting an amount over the balance;
  - once the balance is 0, replace the payment form with a "paid in full" note;
  - never show two errors at once.
  - Acceptance: cash 500 on a balance of 300 posts 30000 cents and shows a change of L 200.00; card 500 on 300 is still rejected; a balance of 0 renders no submit button.
- [ ] **T7** New-order flow:
  - create a new customer from the customer step;
  - create a vehicle from the vehicle step when the customer has none or the right one is missing;
  - the new records are then selected and the flow continues to confirm.
  - Acceptance: a brand-new customer and vehicle can reach the confirm step without leaving `/ordenes/nueva`.
- [ ] **T8** Item form category and unit:
  - show the workshop's already-used values as tappable chips that fill the field, plus a one-line hint that a new value can be typed;
  - keep the field as free text.
  - Acceptance: tapping a chip fills the field, and typing a new value still saves it.

## Checks

- Per task: `cd web && npm run lint && npm run typecheck && npm test -- --run`.
- At closure:
  - the same checks plus `npm run build`;
  - a local browser check at phone width (375px) and desktop width;
  - the Test Value Gate pass 3 list for the PR.

## Progress

| Task | Route | Commit | Evidence |
| --- | --- | --- | --- |
| T1 | delegated (workflow writer) | (this commit) | lint, typecheck and 62 files / 265 tests pass; no `w-auto` left outside doc comments, verified via compiled CSS that `fullWidth`/`!min-h-10`/`!text-base` resolve the Tailwind cascade conflict |

## Next step

Run the workflow (T1 to T8 in order), then the closure checks.
