# Attributed creation review — #35

2026-10-12; uncommitted changes against
`ce69d6ef0bb3b2261b2d2703dc4ed480e777d45d` (#34). Live issue #35, parent #42,
the approved UX specification/ticket breakdown, project baseline, AGENTS.md,
README and existing local runbooks were refreshed. Commit, push and merge remain
user-controlled. GitHub and Drive were not edited.

## Problem → decision → implemented behavior

Immediate calculation from editable creation forms made captured quotation facts,
supplied terms and policy harder to review together. Reuse the existing prepared
requests and HTTP state: validate the editable draft, show a read-only attributed
review, then deliberately save its frozen request through the unchanged API.

- Demo, curated Practice and prepared Odoo follow facts → terms → review/calculate.
  Review performs no POST, ERP acquisition, training, inference, solve or save.
  Exact context, capture/cutoff, supplier/offer identity, prices, capacities, MOQ,
  promised dates, availability, applicability ranges and policy are visible.
- Labelled inline errors use `aria-invalid`, linked descriptions and alert roles;
  the first invalid field receives focus. Review heading receives focus on mount.
  A named keyboard-focusable table scroll region contains wide exact columns.
- Odoo remains a local captured preview until FastAPI independently rereads the
  quotations/currency when saving. Explicit demand/capacity/MOQ/dates remain separate
  from quotation price/identity; synthetic ML history is never presented as observed.
  Fixed owner-prepared ranges, availability and policy remain subject to backend
  validation. No arbitrary files, models or quotation discovery were added.
- Edit retains values and invalidates review. Final save uses its private frozen
  payload, with the existing idempotency key and repeated-submit guard. Uncertain
  writes retain exact payload/key and explicit retry; edit/replacement stays blocked.
  A required date expiring before a new save requires edit/review, while recovery
  preserves the original exact intent. Prior saved cases cannot masquerade as a
  successful new creation after a definitive failure.
- Genuine saved synthetic/Practice cases retain Practice classification and curated
  example attribution; prepared Odoo cases remain controlled work. Successful new
  comparisons open their bookmarked saved Plans view with heading focus. Practice
  focuses its saved confirmation and retains its deliberate Open saved case action.

No backend/core/application/persistence behavior, migration, dependency, model
loading policy, immutable snapshot/hash or approval/PDF contract changed. Reflex
remains HTTP-only. Legacy Python event handlers reuse the same request assembly.

## Executed evidence

All browser/preview stacks used the existing Podman machine, uniquely named
disposable helper PostgreSQL and owned FastAPI/Reflex/Chromium processes. Matching
synthetic models were prepared offline; actual inference/CBC/storage executed.
Cleanup records confirm owned processes/tunnels/Compose removal. No application
or Odoo database was migrated/reset.

| Check | Actual result and scope | Retained local evidence |
| --- | --- | --- |
| Required fast suite | 632 PASS, 69 service/browser tests deselected; actual ML training/reload/inference and bundled CBC | `.artifacts/ux35-fast/result.xml` |
| Final affected checks | 42 PASS after supplier-focus and stale-feedback fixes; review, Odoo attribution, classification and draft/pending navigation | `.artifacts/ux35-final-focus3/result.xml` |
| New creation browser | PASS: no rows on review, invalid-field focus, edit retention, repeated-click guard, keyboard final actions, genuine synthetic and controlled saves, exact MOQ/prices/provenance and 1280/768/390/320 reflow | `.artifacts/ux35-browser-review3/result.xml`, `.artifacts/t18-browser-36a48a799b45/` |
| Practice regression | PASS: all three tasks, no selection writes, genuine bases/scenarios, approval/library/PDF and exact pending recovery | One passing test in `.artifacts/ux35-browser-final/result.xml`; `.artifacts/t18-browser-049c294d240d/` |
| Approval/PDF recovery regression | PASS: saved allocations, explicit alternative approval, model-unconfigured reopening, exact rendered/downloaded artifact and backend outage/retry | Another passing test in `.artifacts/ux35-browser-final/result.xml`; `.artifacts/t18-browser-b5a3e6de2e49/` |
| Workspace regression | PASS: guarded navigation/drafts, pending recovery and existing responsive/zoom paths with reviewed Practice creation | One passing test in `.artifacts/ux35-browser/result.xml`; `.artifacts/t18-browser-437f344c56f9/` |
| Built-in browser | Synthetic invalid demand/focus, exact review/focus, desktop visual inspection and 320-pixel keyboard table scrolling; document 305/320 CSS pixels, table region 206/960, Right scrolled 40 pixels | `.artifacts/t18-browser-1c9c5bf8732f/builtin-review-desktop.png`, `builtin-review-320.png`; preview cleanup recorded |
| Static/runtime gates | Ruff format/check, compileall, pip check, Odoo Compose configuration and whitespace check PASS; Impeccable detector `[]` | Executed terminal gates; no Odoo services started |

The new controlled Odoo browser path uses the existing adapter with **mocked
read-only quotation transport**. HTTP, model, CBC and PostgreSQL are real; the
quotation reread is a controlled fixture, not fresh live ERP evidence. Existing
affected fast contracts also test expectation mismatch, provenance and exact replay
without rereading upstream. Compilation is exercised by actual Reflex startup;
no additional export or standalone persistence rerun was needed.

## Retained failures and corrections

Initial browser checks found review/saved focus firing before conditional content
mounted; on-mount focus fixes this. Supplier fields generated by `foreach` lack
static Reflex refs: safe exact DOM-ID focus fixes first-invalid supplier focus.
Stale earlier save feedback is cleared when preparing another comparison; a duplicate
facts heading was removed. Existing browser assertions needed the extra Review
action, current bookmarked recovery URL and a wait for the new scenario identity.

The fixture preparation initially called `asyncio.run` in Playwright's loop thread;
its existing offline preparation now runs in a standard-library worker thread.
A new test initially asserted form-schema MOQ on the stored facts schema; final
assertions use the canonical saved request and verify exact prices/provenance.
These earlier failed runs are retained. `ux35-browser` and `ux35-browser-final`
contain passing regressions alongside failures and are **not suite PASS** claims.
The final focused command first named a nonexistent test file, then lacked a fresh
pytest parent directory; corrected `ux35-final-focus3` passed. The pre-existing
Starlette/httpx deprecation remains; dependencies were not upgraded.

## Limits → traceability → next capability

Fresh live Odoo, hosted CI, screen-reader speech, physical phones and owner/novice
sessions remain unverified. DOM semantics and Chromium evidence do not establish
whole-app WCAG or human acceptance. Practice shares persistent application storage;
review/drafts and pending recovery are session-local, without closed-session
durability or multi-tab coordination. A valid review is not a feasibility guarantee.

UX-AC-07, FR/AC-V2-01/09, NFR-V2-05/07 and UX29-04/06/10 map this slice to the
official attributed-input and Python-web-UI obligations. Chapters 4/6 can explain
the HTTP boundary and frozen-review decision; chapter 7 can use the scoped browser
evidence and corrections. The [runbook](UX35_CREATION_RUNBOOK.md) owns reproduction.

Next: #36 aligned saved allocations and explicit selection. #39 explanation also
remains available; #41 reassessment and T19 thesis closure stay separate.
