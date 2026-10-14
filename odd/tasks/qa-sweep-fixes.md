# QA sweep fixes

## Objective

Fix what the parallel QA sweep of 2026-10-13 confirmed against a local
production build of `main` (584b919). All 3 high and 14 medium items are
fixed, plus the 6 low ones, which are cheap enough to ride along.

## Problem

The sweep used 9 testers and 9 independent verifiers through the Playwright
MCP and confirmed 23 items. The most serious is a regression from
`demo-feedback-ux` T3: the offline/sync toast covers the header's "Más"
button, so Caja del día, Facturación, Exportar todo and Cerrar sesión are
unreachable while it shows. The other two high items are invoicing writes that
stay enabled offline on a cold load, and a 3000-item inventory list that
blocks the main thread while scrolling. The full report, with reproduction
steps, is in the session scratchpad (`qa/report.md`). The sweep journal
(`wf_95e51a97-8bd`) holds the raw findings.

## Why

The demo is in front of mechanics now. A menu they cannot reach, a Factura
form that pretends to work offline, and a list that freezes on a real-size
inventory undercut trust more than any missing feature.

## Scope

In scope: the 23 confirmed items, grouped by area into seven tasks.
Out of scope:
- pagination and server-side search;
- an Excel import;
- cost price and margin;
- merging outbox taps.
Those wait for mechanic feedback.

## Constraints

- One branch (`fix/qa-sweep-findings`), one PR. The user chose a single PR
  ("un solo PR") on 2026-10-13. Delivery strategy: `single-pr`.
- Forecast: about 2000 authored changed lines. That is over the 400-line
  heuristic; the user accepted it, and each task stays a separate set of
  atomic commits.
- One work-unit commit per coherent fix, in Gitmoji + Conventional Commits.
  No AI attribution.
- Test-first where a deterministic test exists (RED, then GREEN). Test Value
  Gate passes 1-3.
- RDD is off for this clone (`clone_local`). Each task gets an independent
  verifier instead.
- New dependency authorized: `@tanstack/react-virtual` (T3), the same TanStack
  family already in use. No other new dependency.
- Behavior changes that a baseline spec covers update that spec in
  `openspec/specs/` (customers, app-shell-navigation, fiscal-invoices).
  Inventory has no baseline spec.

## Tasks

Route per task: delegated direct, one writer per task. The writer trigger
fires because each task touches 2+ non-trivial files. Each task also gets an
independent verifier, and at most one bounded fix.

- [x] **T1 App shell and navigation** (web)
  - [high] The offline/sync toast never covers the header or intercepts a tap
    on "Más".
  - [medium] "Más" is at least 44 px tall.
  - [medium] The bottom nav lines up with the centered content column on
    tablet and desktop.
  - [medium] "Cerrar sesión" is disabled offline with a message, and a failed
    logout shows an error.
  - [low] A "Saltar al contenido" skip link is the first focusable element.
- [x] **T2 Offline guards** (web)
  - [high] Invoicing writes (issue Factura, CAI range, fiscal profile, credit
    note) are disabled with the offline message on a cold load while
    offline. Find the real cause first.
  - [medium] The new-order customer search shows the offline message instead
    of an endless spinner.
- [x] **T3 Inventory list at scale** (web)
  - [high] The inventory list is virtualized, so scrolling 3000 items does
    not block the main thread.
  - [medium] A "+" tap re-renders only the tapped row.
- [x] **T4 Inventory details** (API + web)
  - [medium] Movement history tells the initial stock apart from a physical
    count.
  - [medium] Archived items can be listed and unarchived (UI and API).
  - [low] "Archivar" is no wider than "Editar".
  - [low] Stock quantities use a thousands separator.
- [x] **T5 Customers** (API + web)
  - [medium] An archived customer shows an indicator. Edits and new vehicles
    are blocked in the web and rejected by the API.
  - [low] The customer and vehicle create/edit screens have a back link.
- [x] **T6 Work orders** (web)
  - [medium] The 58 mm receipt's "Saldo pendiente" row keeps a readable gap
    between label and amount.
  - [medium] Removing a line asks for confirmation.
  - [medium] Voiding the blocking payment clears the stale "cannot cancel"
    alert.
  - [low] The Abiertas/Historial tabs support arrow keys (roving tabindex).
- [x] **T7 Contracts and errors** (API + web)
  - [medium] `buyer_identification_required` returns 409, per the
    fiscal-invoices spec.
  - [low] An identical fiscal profile replay does not bump `updated_at`.
  - [medium] An unknown route shows a Spanish not-found screen with a way
    back.
  - [medium] A malformed phone on login/register shows a specific Spanish
    error.

## Acceptance criteria

- Every item above is fixed and covered by a test that fails without the fix,
  where a deterministic test is possible.
- The geometry items get a real-browser recheck at closure, through the
  Playwright MCP on the local production build at 375 px and 1280 px. Those
  items are:
  - the toast and "Más";
  - the bottom nav;
  - the 58 mm receipt;
  - virtualized scrolling.

## Checks

- web: `npm run lint`, `npm run typecheck`, `npm test -- --run`,
  `npm run build`.
- api (when touched): `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run pytest`.

## Progress

| Task | Status | Commits | Verification |
| ---- | ------ | ------- | ------------ |
| T1 | done | 4268280, f4718d3, 8384da1, 9a51f7f, a79b4e4 | verifier pass; browser S1-S5 pass |
| T2 | done | b462d1d, 6e72b60 | verifier: 2 minor, 1 fix; 2 later corrections; browser O1-O6 pass |
| T3 | done | 0f978f6 | verifier pass; browser P1-P6 pass |
| T4 | done | cbd96be, b1ecbe4, da8354b, 4dbd445 | verifier pass; browser C1-C4 pass |
| T5 | done | ee5da42 | verifier fail (back link missing on the form), then 1 fix; browser C5-C6 pass |
| T6 | done | fd060e5, 0890c17, 14dfab5, ed931de | verifier pass; browser C7-C10 pass |
| T7 | done | 2bdebf4, abdd8dd, 5b1cd7d, 5c91040 | verifier pass; browser S6-S7 pass |
| follow-up | done | 9db13db, 5310924 | offline empty-state fix on sibling screens |

Route per task: delegated direct. The writer trigger fired every time (2+
non-trivial files). Workflows: `wf_bc99b00b-e41` (7 writers, 7 verifiers,
2 fixes) and `wf_12eb255d-d71` (4 browser checkers).

## Corrections after the workflow

- **T2 regression.**
  - The first fix marked `onlineManager` offline on any `network_error` and
    never set it back.
  - The browser never fires `online` when `navigator.onLine` stayed true, so
    an API restart would have left the app paused until a reload.
  - Fix: `web/src/shared/offline/reachability.ts` probes `/api/health` every
    10 s, and on focus or visibility, while offline. It restores the state
    on the first ok response. The outbox flush also reacts to
    `onlineManager` going online.
- **Test Value Gate fixes.**
  - The NotFound test now goes through the real route config.
  - The arrow-key test also covers ArrowLeft.
  - Each unarchive collision guard (the pre-check, and the DB index mapped
    to 409) has its own test at its own seam.
- **Browser recheck, two failures.**
  - The toast covered 18-40 px of the last row's stepper at the bottom of
    the list, and its offset assumed a 3rem nav (the real one is 54.7 px).
    The nav and the toast now publish their measured heights as CSS
    variables (`useCssHeightVariable`).
  - The new-order steps offline showed "Todavía no hay clientes" because a
    first fetch settles into `network_error`, not a paused state. Now no
    data plus offline or `network_error` shows the offline message. The
    same fix went to the customers, work orders, inventory and archived
    lists.
- **Virtualizer estimate.** The row estimate is 132 px (measured), not 96.
- **Commit hygiene.**
  - Six titles were reworded to 72 characters or fewer (counting the
    shortcode).
  - One gitmoji was fixed (`:sparkles:` on a `fix`).

## Verification evidence

- web: `npm run lint` clean, `npm run typecheck` clean, `npm test -- --run`
  72 files and 351 tests passed, `npm run build` ok.
- api: `uv run ruff check .` clean, `uv run ruff format --check .` clean,
  `uv run pytest` 408 passed. There are no schema changes and no migrations.
- Real browser, local production build at 4173 with the API at 8010:
  - The toast-to-nav gap is 12 px at 375 and 1280.
  - The last row clears a two-line toast by 24 px.
  - "Más" is 44 px tall.
  - The nav lines up with the content column (0 px off at 768 and 1280).
  - With 3000 items:
    - DOM nodes went from 27,653 to 176;
    - scroll long tasks went from 3037 ms (~99%) to 122 ms (12.9%);
    - a "+" tap went from 142-468 ms to a 53 ms median;
    - search settles in 340 ms, 300 ms of which is the debounce.
  - With the API blocked while the browser stayed online, the app recovers
    in about 8.5 s with no focus event, and the queued tap flushes once.

## Follow-ups (not in this PR)

- `RequireSession` can rehydrate a persisted `session: null`. A session made
  outside the app's login form, in the same tab, is then bounced to /login
  on reload. Through the UI login this cannot happen, because login clears
  stale queries.

## Next step

Push the branch and open the PR. Merging needs the user's OK; then redeploy
the demo.
