# Verify report — sar-invoicing, Phase A (PA.S1–PA.S13)

**Change**: `sar-invoicing` — Phase A (PA.S1–PA.S12 + PA.S13 review-fixes slice)
**Store**: openspec · **Branch**: `feat/sar-invoicing` (from `main`) · **Scope**: phase A only, per request

## 1. Executed checks (all re-run live, not read from prior records)

| Command | Result |
|---|---|
| `docker compose up -d db` | container running |
| `cd api && uv run ruff check .` | **All checks passed!** |
| `cd api && uv run ruff format --check .` | **138 files already formatted** |
| `cd api && uv run pytest` | **360 passed** |
| `cd web && npm run lint` | clean, exit 0 |
| `cd web && npm run typecheck` | clean, exit 0 |
| `cd web && npm test -- --run` | **55 test files, 232 tests passed** |
| `cd web && npm run build` | succeeded (`tsc -b && vite build`, PWA precache generated) |

All results match tasks.md's own recorded evidence exactly (same counts: 360 API tests, 232 web tests). No drift between claimed and observed state.

## 2. Task-completion state (observed, not rewritten)

Read `openspec/changes/sar-invoicing/tasks.md` in full (406 lines). Slices **PA.S1–PA.S13 are all checked `[x]`** except three tasks, exactly matching the request's "expected pending items":

- `PA.S12.T7` — deploy phase A to the demo (deferred until after the implementation batch)
- `PA.S12.T8` — real-browser check at 390×844 on the deployed demo (deferred, needs T7)
- `PA.S12.T10` — re-verify after T8 fixes (deferred, needs T8)

No other unchecked box exists in phase A. Phase B (`PB.S1`–`PB.S7`) is entirely unchecked, and I confirmed no phase-B code leaked in: `find` for `*CreditNote*`/`*credit_note*` across both `api/` and `web/` returned nothing.

`git log --oneline main..feat/sar-invoicing` shows **24 commits**, including every work-unit commit tasks.md claims by hash (`262e926`…`911fe02`, `0395ffa`, and PA.S13's `7effa36`/`a6b5d33`/`ea621e1`). Working tree is clean (per the session's git status).

## 3. Spec scenario → test mapping (phase A specs only)

Read all 8 spec files; `data-export` and `credit-notes` are tagged **Phase: B** and correctly out of scope (confirmed via each file's header). Within `fiscal-document-print`, its one Phase-B requirement ("Credit Note Layouts…") is likewise excluded.

Cross-referenced spec scenario titles against actual pytest/vitest function names (not just tasks.md's narrative) for `fiscal-profile`, `cai-ranges`, `fiscal-invoices`, `fiscal-document-print` (phase A), `work-orders` delta, `customers` delta. Coverage is comprehensive — the large majority of scenarios have a test whose name is a near-literal transcription of the scenario title (e.g. `test_a_utc_day_boundary_does_not_cause_an_incorrect_allow_or_block`, `test_registering_a_factura_range_starts_next_correlative_at_range_start`). I deep-dove the print field map specifically, since the task asked for it by name:

- `api/src/taller/invoicing/domain/documents.py`'s `FiscalInvoice` dataclass carries every Art. 10–11 field the research note lists (issuer RTN/razón social/nombre comercial/address/phone/email; CAI/rango/fecha límite; number; buyer-or-CONSUMIDOR-FINAL; date; exento/exonerado/gravado/ISV/descuento; total + total in words).
- `web/src/features/invoicing/print/InvoiceDocument.tsx` renders every one of those fields, and `InvoiceDocument.test.tsx` has a single fixture-driven test asserting every row by content, plus dedicated tests for the CONSUMIDOR FINAL fallback, zero-amount "L 0.00" rendering, and the ORIGINAL/COPIA destination legend.
- Both print routes (`Invoice58Page.tsx`, `InvoiceLetterPage.tsx`) render both copies by default; `InvoiceLetterPage.test.tsx` (added in PA.S13.T7) has a real regression test for the `break-before-page` wrapper and the letter `@page { margin: 12mm; }` rule — I verified this is a genuine test (not an echo) by reading its assertions directly.

**Three genuine coverage gaps found** (diagnostic findings only — SDD verify does not gate archive on these):

1. **WARNING** — `FiscalProfile.is_complete` (`api/src/taller/invoicing/domain/profile.py:43`) has zero test exercising it with a field missing. The fiscal-profile spec's own scenario "A profile missing one field is incomplete" is untested. In practice this is low-risk: `PUT /invoicing/profile` requires every field, so an incomplete row can never actually be saved — but the predicate itself, and the spec's named scenario, have no automated proof.
2. **WARNING** — No test for "a previously fetched fiscal profile renders offline" (fiscal-profile spec). Every invoicing web test file was checked (`rg offline` across all of `src/features/invoicing/`); only write-disabled-while-offline tests exist for the profile forms/settings page. The read-from-persisted-cache behavior itself is asserted for the Factura (`InvoiceDetailPage.test.tsx`) but never for the profile.
3. **WARNING** — No test asserts `GET /invoicing/invoices/{id}` is tenant-isolated (fiscal-invoices spec's "Another workshop's Factura is invisible"). I read `get_invoice_route`/`get_invoice` directly and confirmed the implementation **does** correctly scope by `workshop_id` — risk is low, the pattern matches every other feature in the codebase — but no regression test exists for this specific route (only the issuance-side tenant check, `test_issuing_against_another_workshops_order_is_not_found`, is tested).

**SUGGESTION** — fiscal-document-print's "a previously fetched document prints offline" has no direct test on `Invoice58Page`/`InvoiceLetterPage` (only on `InvoiceDetailPage`, via the same `useInvoice` hook and cache mechanism). Low risk since the mechanism is shared and already proven once, but the print routes themselves are untested for this specific scenario.

No CRITICAL findings. The PA.S13 review-fixes slice's own critical finding (the un-locked range-read race in `update_range`) was independently re-derived from source and confirmed fixed (`api/src/taller/invoicing/application/use_cases.py`'s `update_range` re-reads the range after acquiring the profile lock, before deciding immutability).

## 4. Summary

- **CRITICAL: 0** · **WARNING: 3** · **SUGGESTION: 1**
- All checks green, state matches tasks.md exactly, no undisclosed drift between claimed and actual implementation.
- Phase A is functionally complete pending only the three explicitly deferred closing steps (demo deploy, seed re-run, real-browser/print-preview check).

---

**Status**: success
**Summary**: Verified `sar-invoicing` phase A against its 6 in-scope spec files and tasks.md; re-ran every check live (API 360 passed, web 232 passed + build), confirmed all 24 branch commits exist, and traced spec scenarios to tests — found 3 WARNING-level coverage gaps (profile completeness, profile offline-read, invoice GET tenant isolation) and 1 SUGGESTION, 0 CRITICAL.
**Next**: close the three remaining PA.S12 tasks (closing steps, not implementation gaps; the coverage findings are diagnostic and do not gate archive)
**Risks**: Three untested-but-likely-safe spec scenarios (profile completeness invariant, profile offline cache read, invoice tenant isolation on GET-by-id) — recommend a small follow-up test addition, not a blocker.

## 5. Resolution after verify

- WARNINGs 1–3 (profile completeness, Factura tenant isolation on `GET /invoicing/invoices/{id}`, profile offline read) were all coverage gaps; the behavior was already correct. Tests added in `38a6fdf`, each confirmed RED against a temporarily broken production file.
- SUGGESTION (offline print on the print routes themselves): checked in the real browser instead. Offline, the Factura's detail and both print routes render from the persisted cache. No dedicated test was added, because the routes share `useInvoice` with the already-tested detail screen.
- Test Value Gate over every new phase A test:
  - The two issuance-level concurrency tests could only fail if the fiscal-profile mutex and `allocate`'s guarded `UPDATE` both broke; removing either one alone left them green. They were rewritten to drive `allocate` directly (`2e4faf0`).
  - The letter print test echoed its `@page` literal. It now asserts that no page size is forced (`10c97b1`).
- Real-browser check on the demo (390×844) found four defects the suites could not see, all fixed and re-checked on the redeployed demo:
  - the printed issuance time was the raw UTC ISO string (`557dc00`);
  - the 58 mm line table overflowed the paper width (`15af9b6`);
  - the issue dialog had no "Cancelar" (`c5563cf`);
  - the issuer phone printed unformatted (`596f2dc`).
- Seed rerun reported María Hernández as edited by a tester. Fixed in `95e6064`; two reruns now add nothing.
- Rollback drill on a scratch copy of the demo:
  - The guarded downgrade refuses while Facturas exist, and goes through with `-x discard_fiscal_documents=demo`.
  - The drill also exposed a pre-existing restore bug: `taller_unaccent_lower` resolved `unaccent` through `search_path`, which a `pg_dump` restore empties. Fixed by migration `1a57ba6a8108` (`556fe78`).
- Checks at `556fe78`: pytest 371 passed; ruff check and format clean; eslint, tsc and vitest (237) clean; build succeeded.
- Still open: none for phase A. Real (non-demo) invoicing stays off-limits until phase B ships and a contador reviews a printed sample of both layouts (PA.S12.T9).
