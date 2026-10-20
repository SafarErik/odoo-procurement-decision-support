# Guided procurement workspace

Date: 2026-10-20. Working-tree increment on `feature/frontend-revamp`.
The owner commits and pushes; this work performs neither.

## Problem

The existing capabilities were complete, but first-time buyers had to infer the
sequence, the meaning of suggested inputs, and the distinction between saving
plans and approving a decision. Long supplier forms and repeated product names
made orientation harder.

## Decision and boundaries

Keep Python/Reflex, Radix and Recharts, the existing module boundaries, and the
green/purple identity. Use progressive disclosure and small common Python
components rather than a separate React application or new dependency. No
backend API, database schema, model, solver or Odoo-write behavior changes.

This implements the owner's approved frontend plan. It supports FR-V2-01/02
(source-attributed preparation), FR-V2-07/09 and AC-V2-09 (explanations and buyer
UI), FR-V2-08 / AC-V2-08 (optional scenarios), and FR-V2-10/11/12 /
AC-V2-10/11/12 (stored cases, deliberate decision, approved PDF). It does not
redefine those requirements or create new statistical/model-accuracy claims.
See [project baseline](../agents/project-baseline.md) for the canonical mappings.

## Implemented behavior

| Buyer capability | Implementation and acceptance outcome |
| --- | --- |
| Start or resume | `/` is Home with independent requests for up to five pending and five recent saved cases. Partial lists never become whole-library statistics. `/cases` keeps search/filter/pagination. Date, status and short ID distinguish repeated products. |
| Inspect quotations | `/rfqs` shows groups beside the selected group's individual offer references, suppliers, unit prices, quantities and states, plus retrieval time and company scope. The next action appears before a long offer list. |
| Prepare deliberately | Quotations → Demand → Terms → Review. Controlled state holds field values across steps, accordion changes and HU/EN switching. Group changes and navigation preserve the existing discard confirmation. No persistent draft storage is added. |
| Understand provenance | Odoo facts, unchanged suggestions and buyer edits have distinct labels. Review lists values still equal to suggestions. Generated-data disclosure remains. Keeping a suggested value is not represented as independently verified supplier evidence. |
| Find and correct input errors | Demand errors stay on Demand; supplier errors open the affected terms sections and focus the field. Supplier sections keep their controls mounted while collapsed so submission includes all suppliers. |
| Save without approving | The final preparation action explicitly creates and saves plans. Read-only review freezes submitted terms; existing idempotency/recovery paths remain. |
| Compare plans | Summary cards show cost, premium, exposure and allocation together. The detailed table and chart remain. Explicit selection is highlighted, including a ring in the chart. The minimum-cost label is placed toward the plot interior. Desktop summary is sticky; mobile summary stays in normal flow. |
| Understand supplier evaluation | KPI help, reference timestamp, historical record counts and existing readable tree paths remain next to actual values. Help distinguishes first-receipt timing, the one-day grace period, quantity fill and tree training support. Exposure is not described as failure probability. |
| Explore optionally | “What if…?” is visibly optional; original/changed assumptions and saved differences remain. Only explicit submission calculates and saves. Original cases and supplier scores remain unchanged. |
| Close deliberately | The UI now requires a rationale even for minimum cost. Backend compatibility retains its existing minimum-cost exception. Existing one-time confirmation, conflict/recovery handling, scenario non-approvability, No-award without PDF and per-language approved PDF remain. |
| Stay oriented | The case header shows the decision status; the Overview “Next step” card shows the next action. The active case tab is revealed inside its own horizontal strip after navigation/bookmark loading/language changes without scrolling the document or moving focus. |

New shared primitives live in `frontend/components/`; business screens stay in
`frontend/planning/`. Translation additions live in `frontend/i18n_revamp.py`.
No custom React wrapper was necessary. The small tab-scroll script handles
presentation only; domain decisions remain in Python/backend layers.

## Verification evidence

Evidence applies to the local working tree, not hosted CI or a released build.
Machine-readable run references are in
[GUIDED_WORKSPACE.json](../evidence/GUIDED_WORKSPACE.json).

| Check actually run | Result and scope |
| --- | --- |
| `python -m tools.dev check` | 516 fast tests passed; formatting, lint, compileall and dependency consistency passed. Existing Starlette/httpx deprecation warning remains. |
| `reflex compile --dry` | Passed during implementation; subsequent production `reflex run --env prod` compiled and built successfully with Reflex 0.9.12. |
| `pytest tests/e2e -m e2e --browser chromium -q -p no:cacheprovider` | All three passed. Real disposable PostgreSQL, FastAPI and Reflex; generated Odoo/model fixtures. Preparation, step/language preservation, one approval, HU/EN PDF, separate No-award and reload, optional price scenario, empty/error states. |
| Responsive browser matrix | Home and case views at 1440/1280/768/390 px; an additional 375 px scenario flow. Screenshots and horizontal-overflow assertions. Reduced-motion No-award flow and Escape cancellation. |
| Database integration run | 27 passed, 21 skipped, one runtime probe failed because the isolated harness intentionally supplies an empty Odoo URL. All three runtime-service probes subsequently passed with explicit local service URLs; this resolves that configuration failure. Database tests used only a fresh disposable database. |
| Live Odoo preparation | Read-only selection/preview of local generated groups with 4, 5 and 10 suppliers; ten-supplier wizard captured at all four target widths. Cancel/discard group switching checked. No owner case or final decision was written. |
| Impeccable detector | `impeccable detect --json frontend` returned `[]`; Python-wrapper coverage is limited, so this is not an accessibility certificate. |

The first browser attempt found duplicate visible review headings; the duplicate
was removed. Render inspection found a supplier disclosure button whose
content-box width extended beyond its card; border-box sizing fixed it.
The independent finish review requested active-tab visibility on mobile and
noncolliding chart labels; both received targeted fixes and browser regression
coverage. The final targeted Chromium regression passed (1 test): both programmatic
navigation and bookmark reload keep the selected Decision tab visible under
reduced motion. The independent reviewer marked both fixes resolved with a
focused `ship` verdict; this is not a whole-surface accessibility certification.
Run details are recorded in the evidence file.

Previous owner modifications to `P4_DEMO_REPORT.json`,
`P4_MILP_EVALUATION.json` and the Reflex lock files were preserved.
No Drive, commit, push or merge operation was performed.

## Limitations and checks not claimed

- Browser E2E uses isolated fixture quotations/model data, not end-to-end writes
  against the owner's live Odoo-backed cases. Live Odoo checks were read-only.
- The 21 skipped integration tests are opt-in live integration contracts; their
  skip is not a pass. Earlier P4 evidence is separate historical evidence.
- Single-plan/no-alternative, infeasible/solver-error, duplicate-request and
  approval-conflict behavior is covered by the existing fast/API/state suites,
  not a new complete browser fault-injection matrix.
- No complete screen-reader audit, physical-phone run, Safari/Firefox run, or
  exhaustive long/unbreakable-name fixture matrix was performed.
- Keyboard checks cover focus management, native controls and confirmation
  cancellation, not an independent full accessibility certification.
- Persistent drafts and multi-user authentication remain outside this increment.
  Session loss/reload can lose unsaved preparation.
- Source badges distinguish value equality to the suggested baseline, not a
  per-field supplier-verification workflow.
- The owner’s unaided walkthrough remains to be performed. Automated correctness
  and screenshots do not establish that real buyers find the system enjoyable.

The implemented visual system is documented in [DESIGN.md](../../DESIGN.md)
and `.impeccable/design.json`; derived tonal ramps are non-normative.

## Documentation and thesis

The Hungarian local guide is outside the repository at
`C:\Users\safar\Documents\ChatGPT\SZAKDOLGOZAT\helyi-utmutatok\beszerzesi-rendszer-hasznalata.md`.
It explains the actual controls, concepts, startup, a short demo, expected
results, troubleshooting and a blank owner test checklist.

Chapter 3 can retain the requirements and responsibility boundaries. Chapter 4
can describe the guided navigation and frontend/backend separation. Chapter 5
retains the same algorithms and model limitations. Chapter 6 should describe
the final Python components, controlled input state and explicit decisions.
Chapter 7 should separate automated tests, visual checks, opt-in skips and the
still-pending owner usability walkthrough.
