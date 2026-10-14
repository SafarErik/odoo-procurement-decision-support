# Original-base disruption comparison — #37

2026-10-12; uncommitted changes against
`ca97aee9f2b42e6086258bd5b1559603e602b600` (#36). Live #37/parent #42, approved
UX specification/ticket breakdown, project baseline, AGENTS.md, README and runbooks
were refreshed. Older planning statements remain dated history; current source and
handoffs establish local capability. Issue checklists are prospective requirements.
No commit, push, merge, GitHub write or Drive write was performed.

## Problem → decision → implemented behavior

An infeasible child has no minimum plan or comparison deltas, so reconstructing the
original from those deltas erased the useful baseline. Retrieve and retain the
actual immutable original through the existing HTTP GET; compare its proven minimum
with the child's saved minimum. Reuse the existing five-type draft and MILP API.

- What-if now starts with original/scenario/change columns for feasibility, demand,
  exact minimum cost, exact synthetic exposure fraction and every supplier quantity.
  Real zero allocations remain zero; absent plans/cells say **Unavailable**. Original
  evidence stays visible on infeasible or incomplete children, without invented
  feasibility or relaxed constraints. Decimal cost differences and exposure differences
  retain precision; this is presentation arithmetic, not a second optimizer.
- Fresh child bookmarks read the original once; same-base navigation reuses retained
  immutable data. Original ID, context, demand, dates, class/Practice group and supplier identity
  must match before comparison. Original GET failure preserves the child and offers
  explicit read-only retry, preserving entered draft terms and performing no new POST.
- All five existing types target the original UUID even when entered from a child.
  Original capacities/prices remain the validation reference; demand/capacity bounds,
  decimal-price rules and one-supplier/two-change combined limits remain unchanged.
  Draft assumptions, original UUID, changed-demand and simulated-price caveats appear
  before save. Saving uses the unchanged scenario API/MILP and saved assessments.
- A successful save or exact recovery bookmarks the child in What-if and focuses
  its comparison; definitive failure keeps the original without success navigation.
  Validation focuses the alert. The platform's immediate submit throttle suppresses
  rapid duplicate submits; loading/pending guards and exact payload/key replay remain.
  Explicit **Return to original base** uses the existing Stay/Discard guard. Pending
  requests retain their original URL/payload/key and cannot be discarded.
- Source/class/parent history remains in the case header and existing grouped library.
  Changed demand totals are not like-for-like savings; simulated prices are not fresh
  quotations; synthetic exposure is not calibrated failure probability. Children
  remain analytical; approval and immutable decision/PDF continue on the original.

No backend/application/persistence/core/solver/ML, route, migration or dependency
change. Reflex remains HTTP-only. Original GET/replay does not optimize; each **new**
scenario POST runs the existing MILP on stored inputs/assessments, without Odoo
acquisition, retraining or rescoring. Service tokens/artifacts stay server-side.

## Executed evidence

The existing Podman machine hosted uniquely named disposable helper PostgreSQL;
fixtures owned FastAPI/Reflex/Chromium and any forwarding tunnel. Trusted synthetic
models were prepared offline and actual inference/CBC/HTTP/storage ran. Scenario
tests then removed model configuration before all five submissions. Odoo remained
unconfigured; no owner/application/Odoo database reset was performed.

| Check | Actual scope/result | Retained evidence |
| --- | --- | --- |
| Required full fast suite | 656 PASS, 71 service/browser tests deselected; real mandatory ML/CBC execution | `.artifacts/ux37-fast-final/result.xml` |
| Final affected tests | 97 PASS after final immediate-submit guard and exact +4 EUR assertion; includes original retrieval/join rejection, infeasibility, draft retention, five-type validation, stored/replay, controlled Odoo adapter contracts, navigation and final decisions | `.artifacts/ux37-final-focus/result.xml` |
| New final scenario browser | PASS: five actual saves from base/preceding children; one row for rapid outage double-click; bounded combined rejection/focused alert/Stay-preserved draft; exact original/child supplier quantities and costs; class/group inheritance; unchanged original facts/assessments; genuine infeasible demand | `.artifacts/ux37-scenario-final/result.xml`, `.artifacts/t18-browser-1b813e1aeeb1/` |
| Recovery and reflow | Same final test PASS: fresh infeasible child at 320, original-only controlled GET 503, explicit GET retry with no new child; real stopped API causes uncertain POST, guarded route retains exact original URL/payload/key, explicit retry saves one additional child; 1280/1440/768/390/320 have no document overflow | Same stack, `scenario-comparison-*.png`, `infeasible-original-retained-320.png`, request/server logs |
| Existing Practice and approval/PDF regressions | Two tests PASS against final immediate-submit source: all three Practice tasks/classification, genuine child saves, immutable alternative approval/PDF, model-unconfigured retrieval and real outage/exact recovery | Two passing tests in `.artifacts/ux37-browser-final/result.xml`; `.artifacts/t18-browser-7123a0b4cdc0/`, `t18-browser-c5eb61ff19a8/`. The combined run has one earlier recovery-locator failure, not an overall suite PASS; the separately rerun scenario test above resolves it. |
| Built-in browser | Desktop original 102 EUR/exact exposure/0–4–6 allocations beside child Unavailable; at 320 document width 305, named region width 239 and keyboard horizontal scroll 40; focused combined alert unobscured, Stay retains demand 12 | `.artifacts/t18-browser-463372239515/builtin-scenario-comparison-final.png`, `builtin-scenario-320.png`, `builtin-scenario-error-320.png` |
| Static/runtime checks | Ruff format/check, compileall, pip check, Odoo Compose config, diff whitespace PASS; actual Reflex startup compiles changed UI; Impeccable detector `[]` | Executed terminal gates; Compose config started no Odoo services |

The full fast run preceded the final change from delayed to immediate submit
suppression; the final 97 affected checks and browser test verify that refinement.
The built-in screenshots verify the unchanged final layout, not submit timing.
Keyboard/DOM/viewport checks do not establish whole-app WCAG acceptance or physical
phone/screen-reader speech results. Existing #36 native-zoom evidence is retained
historically; this increment did not rerun its independent comparison workloads.
Owned stack evidence records process/tunnel/Compose cleanup; preview tab and viewport
override were closed/reset. Artifact folders remain for inspection.

## Retained failures and corrections

Initial focused checks caught computed comparison fields being evaluated without a
loaded case, and older test helpers treating post-save navigation effects as loading
updates. Empty-case getters now return empty rows; helpers still assert loading on
request-phase yields and completion afterward. Required fast checks initially had
655 PASS and one affected Odoo-contract helper failure; its focused 15 tests passed
after correction. The later full fast run passed.

Browser checks caught a real duplicate outage save on a rapid double-click. Submit
throttling now permits the first event immediately and suppresses rapid repeats,
with existing server-side loading/pending guards retained. A briefly tried delayed
submit was replaced to avoid delaying the first action. Early new browser fixtures
also used an incorrect price label, assumed a visible textbox inside collapsed
recovery details, and looked for a nonexistent recovery summary. Final locators use
the established labels and route-guard pattern. These failed runs remain in
`.artifacts/ux37-browser*`; their overall failures are not suite passes.

One focused retry without a workspace basetemp failed sandbox temporary-directory
creation before running tests; the documented workspace-owned artifact procedure
then passed. An early owned preview used the wrong fixture `as_of` location and
cleaned up after its setup error; the corrected preview completed. No backend
validation, fixture constraints or accepted architecture was relaxed. The existing
Starlette/httpx deprecation remains.

## Limits → traceability → next

Fresh live Odoo, hosted CI, screen-reader speech, physical phones and owner/novice
sessions remain unverified. This is local controlled synthetic evidence. Original
read failure uses a controlled HTTP middleware fault; uncertain POST recovery uses
a real stopped API process. Neither proves an arbitrary production outage. Practice
shares storage, and drafts/pending recovery remain session-local rather than a
closed-session/multi-tab outbox. No new timing workload, library benchmark or
standalone persistence rerun was needed for this presentation increment.

UX-AC-10; FR/AC-V2-08, AC-V2-07/09; NFR-V2-06/07; UX29-04/06/07 map the slice to
the official disruption, unchanged MILP, stored comparison and recovery obligations.
Chapters 4/6 can explain the original/child HTTP boundary and truthful comparison;
chapter 7 can use the scoped browser/runtime evidence and retained failures.

Next: #38 deliberate approval/No-award review. #39 readable explanations is also
unblocked; #41 human reassessment and T19 thesis closure remain separate. Commit,
publication and merge remain user-controlled. See the [runbook](UX37_SCENARIO_RUNBOOK.md)
for prerequisites, expected outcomes and owned-service cleanup.
