# Responsive Decision editorial workspace — #34

2026-10-12; uncommitted changes against
`fc99e57ea1cf46dda24bde7ce1a9536ed6300fb5` (#33). Live issue #34 and parent #42,
the approved UX specification/ticket breakdown, AGENTS.md, README and local
runbooks were refreshed. The parent's prospective checklists remain a contract,
not a claim of hosted or human acceptance. No GitHub issue or Drive document was
edited; commit, push and merge remain user-controlled.

## Problem → decision → implemented behavior

Independent headers and a setup-first cockpit made context and navigation harder
to find. Pending saves were guarded, but unsaved creation/scenario drafts were not.
Reuse the existing planning state for navigation and one small shared frontend
shell; preserve all application/core/infrastructure boundaries and HTTP contracts.

- Cases, Open RFQs and Practice share the green rail, mint ground, purple selection,
  precise sans typography and tabular numbers. `/cases` is the primary workspace
  destination; `/` keeps the compatible read-only RFQ ledger and `/planning` keeps
  the existing comparison entry. The shell adds no arbitrary RFQ conversion.
- A labelled modal drawer replaces the rail below the large breakpoint. Its first
  available destination receives focus; Escape/Close returns to Workspace menu.
  Closed overlays cannot block pointer input, including after reduced-motion changes.
- The product heading, demand/unit/currency, dates, source, original-base identity,
  classification and planning/decision statuses lead the saved comparison. Existing
  open/create controls and help follow it. Plans/What-if/Suppliers/Audit update the
  stored-case URL without recomputation. Invalid IDs/views clear prior case display.
- Prepared creation inputs, creation edits and scenario edits mark drafts. App
  navigation, case/view/input changes and replacement Practice/input preparation
  offer Stay/Discard. Stay retains the draft and original focus; Discard clears it
  before navigating and focuses the destination, avoiding automatic old-tab reselection.
- Pending writes remain non-discardable. Global/view/input/Practice changes are
  guarded; all route entries, including RFQs, return to the original recovery
  context without changing payload/key. Retry remains explicit and session-local.
- Exact audit/chart tables have named keyboard-focusable scroll regions. Chart axis
  numbers remain on one line. Existing API error/status feedback is retained, and
  the RFQ error/loading surfaces now expose alert/status roles.

No backend route, catalog/snapshot/hash/decision/PDF contract, migration, dependency,
model training, solver behavior, Odoo access or persistence implementation changed.

## Executed evidence

All service/browser checks used uniquely named disposable helper PostgreSQL,
offline synthetic assets, owned FastAPI/Reflex/Chromium processes and the existing
Podman machine. Odoo credentials were absent. Fixtures recorded cleanup of their
own processes, tunnel and Compose project; no owner/Odoo database was reset.

| Check | Actual scope and result | Retained local evidence |
| --- | --- | --- |
| Required fast tests | 622 PASS, 68 service/browser tests deselected; actual ML training/reload/inference and bundled CBC exercised | `.artifacts/ux34-fast/result.xml` |
| Affected checks after navigation focus fix | 69 PASS; draft/pending boundaries and existing clients/components | `.artifacts/ux34-final-focus/result.xml` |
| Affected checks after final UI/RFQ adjustments | 47 PASS; navigation, cockpit, decisions and RFQ API contracts | `.artifacts/ux34-final-ui/result.xml` |
| Workspace browser | PASS: Earlier/Practice library → sections → global return; creation/scenario Stay/Discard and focus; 1280/1440/768/390/320 reflow; drawer focus/return; reduced motion; real backend outage, exact route recovery and retry; unavailable library; native browser zoom | `.artifacts/ux34-browser11/result.xml`, `.artifacts/t18-browser-7c5ee103209f/` |
| Curated Practice regression | PASS: all three entries, no selection writes, fresh saves, outage/infeasibility, approval/library reopen, exact PDF and uncertain classified retry | One passing test in `.artifacts/ux34-browser5/result.xml`; `.artifacts/t18-browser-89fa25417e63/` (the other tests in that invocation did not pass) |
| Existing approval/PDF recovery regression | PASS: exact allocations, explicit alternative approval, stored reopening with model unconfigured, document failure/retry/render/download, unavailable GET and exact pending retry | `.artifacts/ux34-regression2/result.xml`, `.artifacts/t18-browser-6382a4cb8e1e/` |
| Built-in browser | Desktop context/Practice/draft dialog focus; final 320 layout and corrected column drawer with focus/return, drawer width/scroll width 288/288 and document 305/320 CSS pixels | Owned previews `.artifacts/t18-browser-324e3f851124/` and `.artifacts/t18-browser-743599388333/`; cleanup recorded |
| Static/runtime gates | Final Ruff format/check, compileall, pip check PASS; Odoo Compose configuration PASS with the documented provider, no services started; diff whitespace check PASS; Impeccable detector `[]` | Executed terminal gates; ignored local artifacts |

Native zoom used an additional owned Chromium profile and a test-only extension
calling `chrome.tabs.setZoom(..., 2)` / `getZoom()`. The recorded factor is **2**;
devicePixelRatio doubled and the 1280-pixel window reflowed to at most 640 CSS
pixels without document overflow. This is actual browser enlargement, not a CSS
transform, screenshot scale or PDF zoom. The extension/profile context closes in
`finally`; the owner's browser is unchanged. See the [runbook](UX34_WORKSPACE_RUNBOOK.md).

The new browser run supplies real HTTP/PostgreSQL workflow evidence; no standalone
persistence rerun or library benchmark was needed for this frontend-only slice.
No hosted check or full WCAG conformance is inferred from local results.

## Retained failures and corrections

Initial sandbox-focused execution stalled and was stopped only after verifying its
exact test process IDs; the required runtime rerun passed. Initial standalone page
checks found generated-setter/event-argument assumptions; explicit drawer state and
explicit Stay binding fixed them. Earlier browser runs are retained under
`.artifacts/ux34-browser` through `ux34-browser10`, plus the first regression run.

They exposed initial-filter timing, missing dialog/drawer focus, row-layout drawer
overflow, old-tab focus undoing Discard, reduced-motion overlay interception and
missing RFQ alert semantics. Each was corrected and rechecked in the passing flow.
Incorrect test label/technical-model-copy assumptions and the relocated collapsed
open/create controls also required test corrections. The conservative generic
uncertain-response client contract was preserved. The combined browser5 invocation
has a Practice PASS, workspace failure and smoke setup error; it is not a suite PASS.

The first Compose gate used no explicit provider and failed; the documented local
provider rerun passed. An accidental CR-only page encoding was normalized and final
format/lint/diff checks passed. Impeccable launcher context loading initially failed;
the existing product context/reference was read directly and the detector ran.
The remaining fast-test warning is the pre-existing Starlette/httpx deprecation.

## Limits → traceability → next capability

Verified scope is Chromium, prepared three-supplier synthetic cases and the named
desktop/tablet/narrow/zoom/keyboard/reduced-motion paths. Live Odoo, hosted CI,
screen-reader speech, physical phones, owner/novice sessions and whole-app WCAG
conformance remain unverified. The new error roles establish DOM semantics, not
speech evidence. Practice still shares persistent application storage. Pending
recovery is session-local; closed-session durability and multi-tab coordination
remain excluded. Draft protection covers the app's explicit navigation; a browser
close or external address-bar/back navigation is not a durable draft/outbox guarantee.

UX-AC-04/06/13/15, FR/AC-V2-09/10, NFR-V2-05/06/07 and UX29-03/04/06/08/10 map this
slice to the official Python web UI/storage obligations. Chapters 4/6 explain the
frontend/HTTP boundary and navigation decision; chapter 7 can use the scoped
browser evidence and retained failures, without claiming final buyer acceptance.

Next: #35 attributed input review, #36 aligned comparison/explicit selection, or
#39 readable explanations are unblocked by this shell. Further UX delivery and
#41 owner/novice reassessment remain separate; T19 remains thesis closure.
