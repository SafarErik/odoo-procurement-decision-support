# Aligned saved comparison and explicit selection — #36

2026-10-12; uncommitted changes against
`a9510d1346e034a39f5a7b0d1ea8adbe902ea213` (#35). Live #36/parent #42,
the approved UX specification/ticket breakdown, project baseline, AGENTS.md,
README and runbooks were refreshed. Older baseline/product documents retain dated
planning statements; README, current implementation and dated handoffs establish
the newer local capability. Prospective issue checklists are not acceptance evidence.
No GitHub/Drive write, commit, push or merge was performed.

## Problem → decision → implemented behavior

Independent cards and a distant label-only selector made saved allocations harder
to compare and the contemplated decision less visible. Reuse the existing saved
mapping and selection state for a full-width editorial comparison and an exact
review strip; retain the existing finalization form until #38 replaces its presentation.

- Desktop/tablet aligns supplier quantities, including zero allocations, across
  saved plan columns. Dates/availability accompany supplier labels. Costs, absolute
  and exact relative premium, demand coverage, exact exposure fractions and saved
  constraint/exclusion explanations remain accessible. Narrow screens use labelled
  plan sections with the same values; extra desktop columns scroll only in their
  named keyboard region. No supplier/result is invented or silently dropped.
- Explicit Select for review buttons expose pressed state and Selected for review
  text plus the purple selected surface. Drafts open with no selection. Selection
  validates the available saved label and performs no POST/finalization; pending
  writes/loading and immutable final decisions prevent changes.
- The in-flow review strip mirrors saved plan index, allocation/promised dates,
  exact cost/premium/exposure and case/product/demand/unit/currency/date/source.
  It persists across case views without a fixed overlay. Review decision focuses
  the existing final-decision form, which remains functional below the case views;
  its original selector stays synchronized. Alternative/reason/acknowledgement and
  separate No-award contracts are unchanged. Child selection remains analytical.
- Loading another case or explicitly retrieving a draft clears its unsaved selection;
  same-case view navigation retains it. Approved retrieval
  derives the read-only selected summary from the immutable recorded choice;
  No-award has no approved allocation/PDF. No draft-selection metadata was added.
- The subordinate expandable cost/exposure chart retains its exact table equivalent,
  now including exposure fractions. Positions/0–100 labels are approximate and
  synthetic proxy limits remain explicit. Single/no-distinct-alternative,
  infeasible and incomplete/technical results retain truthful messages.
- Mapping rejects duplicate/missing/unknown/negative allocation rows and demand
  mismatches before comparison/review. Absolute-premium formatting preserves tiny
  differences even on long decimal costs; stored relative/exposure fractions stay
  exact. These are response validation/formatting, not duplicated MILP algorithms.

No core/solver/ML, backend/application/persistence, API, migration, dependency,
immutable snapshot/hash/decision/PDF or Odoo behavior changed. Reflex stays HTTP-only;
server token and trusted artifacts remain outside browser state.

## Executed evidence

Service/browser checks used the existing Podman machine, uniquely named disposable
helper PostgreSQL and owned FastAPI/Reflex/Chromium. Models were prepared offline;
real inference, bundled CBC, HTTP and PostgreSQL executed. Odoo was unconfigured.
All fixture/preview cleanup records confirm owned processes/tunnel/Compose removal;
owner/application/Odoo storage and browser profiles were untouched.

| Check | Actual result and scope | Retained local evidence |
| --- | --- | --- |
| Required fast suite | 646 PASS, 70 service/browser tests deselected; actual ML training/reload/inference and CBC | `.artifacts/ux36-fast/result.xml` |
| Affected checks | 63 PASS after initial fixes; 69 PASS after comparison heading/feedback corrections, including allocation integrity, exact precision, explicit selection, incomplete-outcome mapping and existing navigation/finalization | `.artifacts/ux36-focus2/result.xml`, `.artifacts/ux36-final-focus/result.xml` |
| New comparison browser | PASS: actual saved 3/5/10-supplier inputs, 1/3 requested epsilon workloads and varying distinct options; no-distinct alternative and genuine infeasibility; long non-Latin identity; exact costs/quantities/chart-table fractions; read-only explicit selection across views and keyboard review focus; separate No-award | `.artifacts/ux36-browser4/result.xml`, `.artifacts/t18-browser-d8a154d0cb9c/` |
| Reflow/native zoom | PASS: 1280/1440/768/390/320 layouts and 200% native Chromium zoom, factor 2 verified with doubled devicePixelRatio/reduced CSS viewport; keyboard selection/review still works | Same new comparison stack, `comparison-*.png`, `comparison-200-percent.png` |
| Existing approval/PDF recovery | PASS: new comparison selection → existing alternative approval; unchanged original snapshot; model-unconfigured stored reopening; rendered/downloaded exact PDF; real API/document outage, route recovery and explicit same-payload/key replay | `.artifacts/ux36-smoke-final/result.xml`, `.artifacts/t18-browser-7c0fe9ce5d4b/` |
| Curated Practice regression | PASS: genuine bases/scenarios, all three tasks, classification, approval/library/PDF and exact pending recovery | One passing test in `.artifacts/ux36-browser3/result.xml`; `.artifacts/t18-browser-046222ed3c54/` |
| Built-in browser | Final desktop comparison against the approved reference; explicit pressed selection/exact summary, labelled 320 plan sections and unobscured review focus. Document 305/320 CSS pixels; final focused heading spans approximately 569–617 within a 900-pixel viewport | `.artifacts/t18-browser-bfbe3f38049d/builtin-comparison-desktop-final.png`, `builtin-review-320-final.png`; cleanup recorded |
| Static/runtime checks | Ruff format/check, compileall, pip check, Odoo Compose config and diff whitespace PASS; actual Reflex startup compiles the changed UI; Impeccable detector `[]` | Executed terminal gates; Compose config started no Odoo services |

Scoped palette calculations for ink/muted/accent text on white/selected surfaces
are 5.16–11.71:1. Pressed state and explicit text convey selection independently
of color. This is scoped color/DOM/keyboard evidence, not whole-app WCAG conformance.
Native zoom uses a temporary test profile/extension and closes it in `finally`;
no CSS/image/PDF scaling is counted as browser text enlargement. See the
[runbook](UX36_COMPARISON_RUNBOOK.md) for reproduction and cleanup.

The browser's cases are genuinely saved synthetic inputs, including the long
identity; no fake comparison-only result is substituted. Incomplete/technical
statuses are mapping fixtures with retained/absent saved plans, not newly induced
live solver failures. Existing fast runtime gates still execute CBC/ML. Stored
browsing is verified with model configuration removed. No old timing workload,
new library benchmark or standalone persistence rerun was warranted.

## Retained failures and corrections

Initial component tests found a missing palette import; corrected focused checks
passed. Early browser fixtures used an unsupported empty epsilon list and a supplier
identity with trailing whitespace; validation correctly rejected both. Supported
zero-allowance input supplies the genuine no-distinct-alternative case; the long
identity now respects the existing input contract. Backend constraints were not relaxed.

Browser/visual checks also caught a comparison heading accidentally placed in a
supplier block, duplicate nested status roles, and old smoke assertions assuming
one status/card-based allocations. The heading is now in Plans; feedback has one
selection live region; the smoke reads actual aligned rows and uses explicit
selection/review. Final presentation keeps trade-off prose subordinate to the table
and the saved No-award summary distinct from an unsaved choice. The final comparison
and smoke runs pass. Earlier `.artifacts/ux36-browser`, `ux36-browser2` and
`ux36-browser3` are retained; browser3 has one Practice PASS and two failures,
**not a suite PASS**. The pre-existing Starlette/httpx deprecation remains.

## Limits → traceability → next capability

Fresh live Odoo, hosted CI, screen-reader speech, physical phones and owner/novice
sessions remain unverified. A selected draft is session-local, not durable saved
approval; Practice still shares application storage and exact pending recovery is
not a closed-session/multi-tab outbox. The review strip is persistently available
across case views in normal flow, not a fixed screen overlay. Finalization's broader
confirmation presentation belongs to #38; human reassessment remains #41.

UX-AC-08/09; FR-V2-06/07/09, AC-V2-05/07/09; NFR-V2-07; UX29-04/05/10 map this
slice to the official allocation/explanation/web-UI obligations. Chapters 4/6 can
explain the frontend/HTTP and explicit-selection decisions; chapter 7 can use the
scoped runtime/browser evidence and retained failures.

Next: #37 original-base disruption comparison, then #38 deliberate final review.
#39 readable supplier/audit explanations is also unblocked. User retains publication
and merge control; final buyer acceptance and T19 thesis closure stay separate.
