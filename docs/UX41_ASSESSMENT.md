# Complete buyer experience — #41 assessment and handoff

Date: 2026-10-13. Parent [#42](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42),
task [#41](https://github.com/SafarErik/odoo-procurement-decision-support/issues/41).
Baseline/current HEAD: `6535b0ef4e829acd36ba2284d9e1e3658987b95d`.

**Technical consolidation: PASS. Owner first attempt: critical B08 failure. Final buyer acceptance: NOT ACCEPTED; novice gate NOT ASSESSED. #41 remains open.**
The owner pilot has partial B01/B03 evidence and owner-reported assisted B02
completion from 2026-10-14. The owner requests clearer hierarchy, terminology
and recognizable references; overall visual approval has not been given. B08 now establishes a critical recovery/
approval misunderstanding with one task-unintended additional finalization; the
first attempt stops before B09. Owner
visual approval and 3–5 unfamiliar-participant acceptance remain unassessed.
Do not turn partial or absent evidence into success or failure rates.
The [frozen protocol](UX41_BUYER_PROTOCOL.md), [blank template](UX41_OBSERVATIONS_TEMPLATE.csv)
and [runbook](UX41_REASSESSMENT_RUNBOOK.md) are ready for those sessions.
The [machine-readable evidence](UX41_EVIDENCE.json) retains raw identities/hashes,
scoped results, the inconsistent CI step snapshot and separate partial owner observations.

## Problem → decision → behavior

Nine implemented slices need a defensible end-to-end assessment instead of an
inference from screenshots or green CI. Extend the existing real Practice browser
test rather than add a parallel product/runtime. The same original now traverses
curated creation, exact 102/109 EUR supplier quantities, a saved feasible outage,
return to original, deliberate alternative approval, product/status library
reopening without a UUID, genuine document access failure and exact PDF download.
The test also exercises separate feasible/infeasible Practice cases, reasoned
No-award on a separate original, and real uncertain creation with guarded same-intent
replay. Reduced-motion preference is enabled throughout. Snapshot/approval identity
and binary SHA-256 remain strict checks.

The owned harness now records Git HEAD and the hashes of the actual copied frontend
sources, alongside existing test hashes/versions/logs/trace and verified cleanup.
No production frontend/backend/core/application/ML/solver/Odoo/persistence/document
code, dependency, migration, service or CI workflow changed. The source-informed
agent is an evaluator, not an unfamiliar buyer. The dated baseline guide's prospective
T17 text is historical; current README/#38–#40 establish existing approval/PDF scope.

## New executed evidence

Python 3.11.16; Reflex 0.9.12; Playwright 1.63.0/pytest-playwright 0.10.0;
PuLP 3.3.0 with actual CBC; scikit-learn 1.8.0 with real offline training/reload/inference.
The browser used disposable helper PostgreSQL and real FastAPI/Reflex/Chromium,
with model configuration removed for stored library/document work. No live Odoo
or owner-data reset was part of this consolidation.

| Check | Executed result and scope | Evidence |
| --- | --- | --- |
| Consolidated real flow | 1 PASS in 95.37s; complete original chain, exact quantities, two additional curated scenarios, separate No-award, real PDF/create faults, guarded exact replay and reduced motion | `.artifacts/ux41-browser/result.xml`; `.artifacts/t18-browser-07523263a6bc/` |
| Required fast suite | 675 PASS, 74 service/browser tests deselected, in 127.77s; required actual CBC/ML and retained immutable contracts | `.artifacts/ux41-fast/result.xml` |
| Static/runtime | Ruff format/check (263 Python files), compileall, pip check, Odoo Compose configuration and diff whitespace PASS; final actual Reflex startup/compilation | Executed local gates; configuration starts no Odoo |
| Current built-in inspection | Approved direction/reference unchanged; full aligned comparison/semantic selection at 1440, labelled reflow at 320; document 1425/1440 and 305/320 in captured views; drawer 288/288 with focus on Cases and Escape return to menu; menu target 44px high | `.artifacts/t18-browser-01a648b254dc/builtin-final-desktop.png`, `builtin-final-320.png`, `builtin-metrics.json` |
| Scoped contrast | Measured ink/muted/selection foregrounds match current tokens. Calculated ink/white 11.71, muted/white 5.88, muted/mint 5.32, white/selection 9.94, white/rail 11.56; focus purple/white 9.94 | `.artifacts/ux41-browser/contrast.json`; current source tokens and built-in samples. This is not an exhaustive control/state audit |
| Retained list-query gate | Recomputed all 192 raw observations: six queries, two warm-ups +30 measurements, all HTTP 200. Query parsing and SQL statement ASTs unchanged from `5f09e91`; no new timing workload run | [Raw timings/plans](UX32_LIBRARY_MEASUREMENTS.json), `.artifacts/ux41-browser/reused-library-gate.json` |

Approved case `bc8a7fc9-f3c3-49be-9ba0-85dba1b81682`, approved-content hash
`1376c8f3b73f86bd172a8bf80d2862e461b767d7954fba2b43be569b1656506c`, PDF SHA-256
`f52c6fbb6b13cab4ccc93ddbdf7b41c57c8ccc35ec82c22dc227ed3bf96b8d76`.
Separate No-award `f743e510-b5a4-43cf-903d-def92d37cd02` has no approved content/PDF.
Durations above are test-run times, not human task times or new latency claims.

The selected [Decision editorial reference](design/decision-editorial.html) retains
SHA-256 `bf25f3bdacaf45c9614d96a49a418a1f841f65e9019ffc91e3901f62193c7a4e`.
The current rail/mint ground/purple selection/opaque surfaces/tabular comparison
and responsive hierarchy preserve that direction; the static 1440px sketch is not
a fixed production dimension. This agent review is not owner visual approval.

## Hosted CI reconciliation

For the exact baseline SHA, GitHub's workflow and job overviews report success:

- [Quality, run 38464973082](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38464973082), job `quality` 115529167377.
- [Container/API, run 38464973113](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38464973113), job `container-api-integration` 115529167287.

Container step details from the connector are internally inconsistent with its
successful overview: step 7 remained `in_progress` and subsequent steps `pending`
on direct step readback. Preserve the reported successful conclusion, but do not
claim independently verified per-step completion from that partial snapshot.
The workflows themselves confirm Quality covers fast/static checks and Container/API
covers integration/frontend compilation, not browser E2E. No hosted browser pass is
claimed, and baseline CI does not cover the new uncommitted assessment/test changes.
Quality remains the only intended required check; no protection or workflow change.

## UX-AC-01–16 and canonical traceability

“Retained PASS” means dated slice evidence reused for unchanged implementation,
not a fresh execution or human acceptance. Each linked handoff preserves failed
attempts, corrections and its own scope. Current fast contracts accompany the new
consolidated browser evidence. Local UX identifiers do not replace canonical V2 ACs.

| UX criterion | Technical outcome/evidence | Canonical mapping; original friction |
| --- | --- | --- |
| 01 Bounded library/company/query | Retained PASS: scoped bounds/cursors/filters/order, unavailable/corruption handling and selected query gate; [#32](UX32_LIBRARY_HANDOFF.md) | FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03 |
| 02 Catalog compatibility | Retained PASS: atomic validated context, old key/hash compatibility and child inheritance; [#33](UX33_PRACTICE_HANDOFF.md) | FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03 |
| 03 Truthful legacy access | Retained PASS: Earlier/unclassified remains distinct, no mass relabelling; #32/#33 | FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03 |
| 04 Recognizable find/open | Current PASS: product/status filter reopening without supplying UUID; retained bounded history coverage | FR/AC-V2-09/10; NFR-V2-07; UX29-03 |
| 05 Curated Practice | Current PASS: entry writes nothing, fresh explicit saves/classification/persistence labels; #33 | FR/AC-V2-09/10; NFR-V2-07; UX29-03/10 |
| 06 Responsive navigation | Current inspection plus retained PASS: Cases/RFQ/Practice, four views, dirty/pending guards, drawer/focus/compatibility; [#34](UX34_WORKSPACE_HANDOFF.md) | FR/AC-V2-09/10; NFR-V2-07; UX29-04/10 |
| 07 Attributed creation | Current Practice review/save; retained PASS for controlled-reader Odoo fixture/explicit terms/field errors; [#35](UX35_CREATION_HANDOFF.md). No new live Odoo acceptance | FR-V2-01/06/07/09; AC-V2-01/05/07/09; UX29-04/10 |
| 08 Exact comparison/selection | Current exact costs/allocations and no implicit selection; retained selected summary, premium/fractions and 3/5/10 ×1–3-epsilon distinct outcomes; [#36](UX36_COMPARISON_HANDOFF.md) | FR-V2-06/07/09; AC-V2-05/07/09; UX29-04/05 |
| 09 Honest solver/alternatives/chart | Retained PASS: single/no-distinct/incomplete/infeasible outcomes and chart/table equivalence; #36 | FR-V2-06/07/09; AC-V2-05/07/09; UX29-04/10 |
| 10 Original-base disruptions | Current feasible/infeasible chain; retained all five types, original facts, simulated-price/demand semantics and exact recovery; [#37](UX37_SCENARIO_HANDOFF.md) | FR/AC-V2-08; NFR-V2-06; UX29-05/07 |
| 11 Deliberate immutable decision | Current alternative review/confirm and separate reasoned No-award; retained cancel/dialog focus, replay/conflict/contention/child denial; owner B08 exposes finalization-purpose misunderstanding; [#38](UX38_DECISION_HANDOFF.md) | FR/AC-V2-11; NFR-V2-06; UX29-05/06 |
| 12 Readable/exact evidence | Retained PASS: source/sample/reference/applicability, exclusions vs zero, exact tree/model/solver/provenance/JSON, keyboard/narrow/zoom; [#39](UX39_EVIDENCE_HANDOFF.md) | FR/AC-V2-07/09/10; NFR-V2-05/06/07; UX29-04/10 |
| 13 Safe recovery | Current create fault/route guard/exact key replay; retained genuine GET/scenario/finalize/PDF faults, conflict GET-only reopening and fresh-session limit; owner B08 comprehension fails despite technical recovery PASS; [#40](UX40_RECOVERY_HANDOFF.md) | FR/AC-V2-09/10/11; NFR-V2-05/06/07; UX29-06/08 |
| 14 Approved document | Current saved approval through PDF outage and byte-identical download; retained page/keyboard/end/fit/zoom and eligibility; #40 | FR/AC-V2-12; NFR-V2-05/06/07; UX29-09 |
| 15 Visual/accessibility/query consolidation | Scoped technical evidence PASS: selected reference, desktop/tablet/narrow, keyboard/focus, actual 200% browser zoom, reduced motion, long/non-Latin/missing labels and query gate. Speech/physical devices unverified | AC-V2-09/13; NFR-V2-04/08; UX29-03–10 |
| 16 Owner/novice outcomes | Owner first-attempt FAIL; novice gate NOT ASSESSED. Frozen protocol retained; Owner B08 first attempt FAIL: critical recovery/approval misunderstanding and 1 task-unintended finalization; B09 skipped after unclear facilitator instructions; 0 novice observations; no novice rates | AC-V2-09/13; NFR-V2-04/08; UX29-03–10 |

All UX29-03–10 interventions now have named technical evidence and corresponding
human tasks. Their original friction is addressed in implementation; improved
human comprehension/completion is still a hypothesis until B01–B09 observations.
In particular, narrow pages still require scrolling, and simulation/authority
information remains necessary. Neither overflow-free screenshots nor green CI prove
that buyers find or understand the right action.

## Accessibility and performance evidence limits

The target follows relevant [WCAG 2.2](https://www.w3.org/TR/WCAG22/) A/AA criteria:
text/non-text contrast, resize/reflow, keyboard access, focus visibility/order/not
obscured, labels/errors/status and target size. This assessment is scoped evidence,
not whole-app conformance. Current body/foreground samples and source surface tokens
were used for contrast calculations; all control/state/border combinations were not
exhaustively measured. Relevant non-colour state is retained in explicit status text,
pressed/disabled selection, labels and error/status roles.

[#34](UX34_WORKSPACE_HANDOFF.md), #36, #39 and #40 preserve actual native Chromium
200% zoom (`chrome.tabs.setZoom`, verified factor 2 and CSS viewport change), keyboard
and 1280/1440/768/390/320 evidence. #36 preserves variable supplier/alternative coverage;
#39 preserves long/non-Latin/missing business labels and local exact-table/JSON scroll;
#38 preserves modal focus/return; #40 preserves PDF navigation/faults. The new chain
executes the reduced-motion preference, rather than inferring it from CSS names.
PDF zoom is distinct from browser text zoom. Screen-reader speech, physical-phone
interaction and owner visual judgment remain NOT ASSESSED/unverified.

Retained list p95 seconds: first/continued base 0.171/0.170, product 0.244, draft
0.201, first/continued child 0.190/0.184. The raw workload has 1,000 company-scoped
bases plus 60 children and a cross-company/concurrent-arrival check. Every selected
20-row query used two warm-ups and 30 observations, nearest-rank p95 observation 29.
All meet ≤1s locally; this is historical PoC evidence, not a fresh benchmark or SLA.
No unaffected transaction/live/ML-workload timing rerun was required.

## Human gate, cleanup and next work

Protocol UX41-v1 SHA-256:
`7e4fbd3d5c750da0a1d99385c18f2784308d3856036c33a0323667bd3e1f61c4`.
The blank template has nine essential tasks and no filled outcomes/time/comprehension.
For each task, required independent novice successes are 3/3, 4/4 or 4/5, plus zero
unintended finalizations/unresolved critical source/decision misunderstandings.
No threshold was relaxed. The 2026-10-14 owner report verifies the demo-save
substep and records a failed saved-UUID lookup and incomplete storage/source
understanding. Exact source corrections were supplied after the report; acknowledgement,
measured time and the full task outcome remain pending; the owner subsequently
reported no help needed for creation and described it as really fast. See
[owner observations](UX41_OWNER_OBSERVATIONS.csv). Agent and owner results do not
enter the novice denominator. O01 remains in progress; novice sessions remain
unarranged/unassessed.

Owned automated/preview evidence confirms process/tunnel/Compose cleanup; the preview
tab was explicitly closed and viewport reset before stopping its frontend. Owner
services/data and the existing browser tab were untouched; shared Podman remains
running. New changes remain unstaged/uncommitted; commit/push/merge and tracker/Drive
publication remain user-controlled. New-HEAD hosted checks remain user-dependent.

The official Python UI/integrated demonstration obligations map to AC-V2-09/13,
NFR-V2-04/08 and thesis chapters 4/6/7. Retained slice evidence supports the remaining
FR/AC/NFR mappings above. This improves reproducibility and honest acceptance reporting;
it does not close T19 thesis work or establish observed-model/production validity.
Next action: owner pilot/visual approval, then the frozen 3–5 unfamiliar-person
sessions, critical-finding fixes and affected retests. Missing humans/speech/devices
are the named remaining gates, not reasons to fabricate final acceptance.

## Owner pilot observation — 2026-10-14

Problem: a missing saved UUID led the owner to infer that Odoo integration is
still wholly future work. Decision: preserve the raw first report and explain
the established boundary before continuing. Implemented behavior: application
UUID generation and helper PostgreSQL persistence; existing controlled read-only
Odoo quotation input; synthetic demo inputs/history. Evidence: owner screenshots
and a stored-only export verify an optimal Practice original awaiting decision
(`ab95c843-c2d3-4441-8fe5-ba71ef878dfc`). The attempted missing UUID is absent from
this session Practice export; its origin is unknown. Follow-up: the owner described
creation as really fast and needing no help, then requested clarification of the
source question. A further reply identifies backend delivery and the no-PO boundary,
but asks whether training and all inputs will come from Odoo. The facilitator
clarified current synthetic offline training versus existing controlled Odoo quotations
and explicit terms. The owner acknowledged this explanation and requested B02;
independent first-attempt demo-source understanding remains unassessed.
Limitation: no measured elapsed human time, overall task independence,
complete source explanation or visual approval was supplied;
B01 is partial and no novice success is inferred. Chapter relevance: 4/6/7,
AC-V2-09/13 and UX-AC-16. No production source was changed for this observation.

### B02 assistance — 2026-10-14

The owner asked where to open a case by product or quantity/date. This exposes
ambiguity in the task wording and difficulty discovering the library: product is
searchable, while quantity/date/save time identify rows rather than separate filters.
The facilitator supplied Workspace menu → Cases, Practice selection, product search
and Refresh, row identification and Open case instructions. B02 is an assisted
first attempt (`independent=no`). The owner subsequently reported successful reopening
and described retrieval through the backend from the database. A stored-only export
confirms the referenced Practice original exists and awaits decision. Its identity
differs from the initial B01 screenshot after another creation; the intended target
and library click path were not directly observed. Human duration remains unknown
(“quite fast” is qualitative). Preserve the frozen prompt, first help request and
follow-up completion report. No product
filter or navigation change is inferred from this one owner observation.

### B03 and broader owner feedback — 2026-10-14

Problem: the owner reports better appearance but too much data/metadata, unclear
No-award terminology, raw UUID source references and an incomplete real-Odoo
buyer workflow. Decision: retain the raw owner report and screenshot, discuss
information hierarchy and intended Odoo discovery before choosing a redesign.
The quantity-weighted saved-score explanation is consistent with the implemented
exposure definition; exact allocations, premium, selected plan and human duration
remain unreported, so B03 is partial. No overall owner visual approval was given.

Proposed direction, not an accepted requirement: buyer context and decision summary
first; related comparisons/charts beside each other on desktop; readable business
references, with UUIDs, exact fractions and detailed provenance available for audit.
Clarify whether the next Odoo entry means selecting open RFQ/quotation groups or
browsing confirmed POs/history. Existing controlled read-only quotation integration
does not establish arbitrary buyer selection or observed-history model promotion.
No ERP writes, new discovery API or replacement visual design is authorized by
this discussion alone. The No-award definition was explained at the owner’s request
before B07; that pre-task assistance is retained in the observation CSV.

Evidence: [owner observations](UX41_OWNER_OBSERVATIONS.csv), session
`owner-B03-report.json` and `owner-B03-density-feedback.png`. Limitations: owner
feedback only, not a novice denominator, timed outcome or completed design brief.
Chapter relevance: 4/6/7; AC-V2-09/13, UX-AC-06/07/11/16. The frozen protocol
and existing product implementation are unchanged.

### Confirmed case workspace direction — 2026-10-14

The owner answered both direction questions explicitly. This confirms the product/UX
brief below, not implementation completion or approval of the current screens.

- **Primary workspace:** one selected procurement case, with supplier evaluation,
  saved MILP allocation alternatives, original-base scenario analysis, explanations
  and deliberate human approval. Preserve the existing Plans/What-if/Suppliers/Audit
  separation while making the active task and next action clearer.
- **Overview:** a separate lightweight entry for open RFQs/supplier quotations and
  saved procurement cases. RFQs are the primary starting point for preparing a new
  comparison; stored cases open without source reread or recomputation.
- **Historical context:** confirmed POs and receipts support supplier evaluation,
  assessment and explanation rather than leading the entry workflow. Observed
  training requires its own validated data/promotion contract; the current model
  remains synthetic and trained offline.
- **Information hierarchy:** spacious, with related information side by side on
  desktop and usable narrow reflow; tabs, progressive disclosure and contextual
  detail panels keep only the active task’s charts/tables/controls visible. Show
  readable business references; retain UUIDs, exact values and provenance in details.
- **Boundaries and delivery:** reuse the current Python/API/adapter architecture and
  immutable stored-result semantics. No Odoo writes or browser-selected model/data
  artifacts. Buyer-selected quotation discovery and historical-context integration
  are separate capabilities from reorganising existing saved-case information.

Evidence: `owner-direction-response.json` preserves the complete replies. Apply this
brief to a bounded revision after the remaining owner findings are collected; do not
silently rewrite the frozen novice protocol. The later B03 selection report and screenshot verify Alternative 1 and its exact
allocation/premium; measured duration and independence remain unreported. Final buyer
acceptance and overall owner visual approval remain open.

### B03 selection follow-up — 2026-10-14

The owner explicitly chose Alternative 1. The screenshot shows Selected for review,
S161 8 units, S184 2, S226 0, total 109 EUR and 7 EUR above the 102 EUR minimum.
These values match the current stored-only export, which still has no final
decision. B03 selection/comparison is demonstrated in the owner pilot; exact human
time, independence and independent calibration interpretation remain unassessed.
No novice rate or overall visual approval is inferred. The original stored record
is retained as `owner-B04-original-before.json` before the neutral B04 prompt.

### B04 scenario follow-up — 2026-10-14

The owner made S161 unavailable and reached the saved comparison fairly fast
(no measured duration). A stored-only export verifies the feasible child, original
parent linkage and exact unchanged original response. The compared minimum plan
remains 102 EUR with S161/S184/S226 quantities 0/4/6: S161 had no minimum-plan
allocation. The previously selected original alternative used 8 S161 units and
would not satisfy the outage assumption. The owner has not yet reported returning
to the original, so B04 remains partial.

Owner question: why must a simulation be saved? Retain this as a comprehension/UX
finding, alongside the need to identify the minimum-cost comparison reference
explicitly. The facilitator explained separate immutable assumption/result storage
for exact reopening, comparison and audit; no approval or ERP order results from
scenario saving. No optional-preview endpoint or persistence-policy change was
implemented or authorized. Evidence: `owner-B04-report.json`,
`owner-B04-outage.png`, `owner-B04-original-before.json` and the session export.
These are owner observations relevant to UX-AC-08/16 and AC-V2-08/13, not novice
success or timed task completion.

### B04 plan-context clarification — 2026-10-14

The owner reports “alternative 1 changed” and supplies the scenario Plans screen.
Its 104 EUR/0-8-2 alternative differs from the original 109 EUR/8-2-0 alternative;
a fresh stored-only export confirms the original response remains exactly unchanged.
Alternative numbering is local to each case. The owner has not explicitly claimed
original mutation, but the returned screenshot does not demonstrate the requested
return step. The facilitator explained the distinction and supplied What-if →
Return to original base → Plans navigation. B04 is now assisted, still awaiting
the actual return interaction.

Retain a UI finding: identify original versus scenario and the scenario assumption
at the plan comparison, and make return navigation discoverable from Plans. This
is an owner finding/proposed revision, not a product-code change or novice result.

### B04 return completed — 2026-10-14

The owner’s follow-up screenshot demonstrates original Plans after the supplied
return instructions: S161 is available, the alternative is 109 EUR with quantities
8/2/0, and the minimum is 102 EUR. These match the retained original response.
B04 is completed with assistance (`completed=yes`, `independent=no`); measured
duration remains absent. Earlier partial reports and persistence/context/navigation
findings are retained. B05’s neutral demand-beyond-capacity prompt is next; the
facilitator retained the unchanged original and supplied no scenario value or result.

### B05 infeasible demand screenshot — 2026-10-14

The owner supplied a 1000-unit demand comparison showing No feasible plan and
Unavailable scenario cost/exposure/allocations, while original quantities and
102 EUR minimum remain visible. A stored-only export verifies the original-base
demand-increase child, infeasible result, absent plan/alternatives and unchanged
original response. No demand value was supplied by the facilitator.

The screenshot demonstrates creation/result presentation, not the owner’s
interpretation of infeasibility, missing values or the preserved original. Ask
those questions neutrally before explaining the semantics. B05 remains partial;
no measured duration or independence report exists. Evidence: `owner-B05-report.json`,
`owner-B05-infeasible-demand.png`, `owner-B05-original-before.json` and the session
export. No novice rate, final buyer acceptance or production-code change is inferred.

### B05 interpretation follow-up — 2026-10-14

The owner identifies inadequate capacity as the reason for infeasibility; the saved
request confirms total supplier capacity is below 1000. The owner links Unavailable
to that shortage. The facilitator clarifies that the cells represent absent valid-plan
cost/exposure/allocations, not zero or supplier-capacity status. Retain this post-report
assistance (`independent=no`). Original-preservation comprehension is still missing
although stored immutability is verified; B05 remains partial and timing unreported.

### B05 completed with clarification — 2026-10-14

Asked about the original quantities/cost, the owner replies Nothing and supplies
the original Plans screenshot: demand 10, costs 102/109 EUR, alternative quantities
8/2/0. This demonstrates original-preservation understanding alongside the previously
reported capacity explanation and technical immutability check. B05 is completed
with the retained result-semantics clarification (`independent=no`); elapsed human
time remains absent. The unfinalized original is retained before the neutral B06
deliberate-approval prompt; no facilitator selection or finalization is performed.

### B06 approval screenshots — 2026-10-14

The owner supplies draft/review-confirmation/approved-state screenshots and says
the premium is preferred. Stored-only export verifies the intended original Practice
case approved Alternative 1 at 109 EUR, quantities 8/2/0, actor reference Practice
buyer, reason “we prefer the premium right now.” and demonstration acknowledgement.
The planning snapshot/hash are unchanged; final-decision/approved-content records
are separate. The decision time is 2026-10-14T13:04:01.222714Z.

Approval is demonstrated; the owner has not explained what becomes permanent or
reported help/confusion or measured duration. B06 remains partial pending that
neutral question. Preserve the entered rationale without inferring an unspoken
benefit or calibrated-risk justification. `owner-B06-approved-case.json` retains
the approved record for later stored/PDF checks; no facilitator PDF access or
finalization was performed. No novice outcome or overall buyer acceptance is inferred.

### B06 permanence clarification and B07 transition — 2026-10-14

The owner says “the saved case became permanent I think.” This tentatively
recognizes permanence without distinguishing the already immutable planning
snapshot from the newly frozen final decision and approved terms. The facilitator
explains that distinction. B06 actions are completed with clarification
(`completed=yes`, `independent=no`); detailed independent finalization understanding
and measured duration remain unassessed. Preserve the first reply, not a fabricated
post-explanation comprehension pass.

B07 next uses a separate fresh demo original for reasoned No-award. The approved
B06 record remains the protected baseline; the facilitator creates/finalizes nothing.
The earlier No-award definition from B03 is retained as pre-task assistance. No novice
completion or final buyer acceptance is inferred from the owner-pilot progression.

### B07 decline discoverability — 2026-10-14

The owner asks where to decline on a separate fresh Practice original. A stored-only
export verifies that original is unfinalized and was created after B06; the B06
approved record remains exactly unchanged. The facilitator supplies the current
Record the final decision / Record No-award location, required audit fields and
Review/Confirm No-award sequence. No selected plan is needed. B07 is assisted
(`independent=no`), with outcome/comprehension/time still pending.

This reinforces the earlier terminology finding: the buyer asks for decline, while
the control says No-award and is below the comparison. Retain a proposed clearer
Decline these plans action and discoverable decision area for the agreed revision.
Evidence: `owner-B07-report.json`, `owner-B07-original-before.json`, the protected
B06 approved record and session export. No facilitator finalization or novice success
is inferred.

### B07 saved No-award and fixture deviation — 2026-10-14

The owner screenshot and stored-only export confirm No-award on the separate
Practice original, actor Practice buyer, reason asd, no selected plan and no
approved content/hash. The planning snapshot stays unchanged and the B06 approved
record is preserved. The No-award time is 2026-10-14T13:17:50.220398Z.

This original has demand 20 and an infeasible solver result. Retain the deviation
from the frozen 10-unit feasible fixture; this does not demonstrate deliberately
declining feasible offered plans. The placeholder reason is valid nonempty test
input, not evidence of meaningful buyer rationale. Ask the owner’s interpretation
of outcome/document access neutrally; B07 remains partial with assistance and
no measured duration. Evidence: `owner-B07-report.json`, `owner-B07-no-award.png`,
`owner-B07-no-award-case.json` and protected B06 record. No PDF call, fixture repair,
facilitator finalization or novice success was performed/inferred.

### B07 interpretation and B08 setup — 2026-10-14

The owner says no case approval/no award and tentatively read-only for now. This
recognizes the no-approval/read-only outcome; the facilitator clarifies permanent
finalization and no approved-plan PDF. The 20-unit infeasible/placeholder-reason
variant actions are demonstrated, but the fixed 10-unit feasible-offer decline
task is not completed. Do not silently count that variant as full B07 success.
Independent precise comprehension and measured duration remain unassessed.

B08 begins with a fresh standard 10-unit demo review. The owner must report Ready
before saving; only then will the facilitator stage the owned API interruption.
The API stays running, eight pre-test records are retained in
`owner-B08-cases-before.json`, and approved B06/No-award B07 records remain unchanged.
No fault, new save or participant outcome is inferred from this preparation.

### B08 outage staged after review — 2026-10-14

The owner confirms Ready. A read-only built-in browser inspection shows the exact
10-unit Practice review and available Create and save plan action; the facilitator
does not click or alter the draft. The controller stops only owned API 57174.
Port/HTTP checks confirm Reflex 57175 and frontend 57176 remain available (HTTP 200).
The eight-case pre-test baseline is retained; save/recovery outcomes are not yet
observed. Restore only after the owner’s failure report, then observe recovery.

The agent also observes prior Final decision saved feedback above the new review;
retain this possible stale-success finding separately from owner feedback. It is
not evidence that the new draft was saved. Readiness/fault timestamps and browser
evidence are in `owner-B08-report.json`; human duration remains blank.

### B08 failure observed and access restored — 2026-10-14

The owner supplies the pending-save warning screenshot. The facilitator retains
AX evidence and reads the DOM recovery JSON without expanding/copying/retrying
controls. The exact URL, payload/key and validated canonical request fingerprint
are retained. Only the owned API is restored; the controller confirms health-ready
and a stored-only snapshot verifies all eight pre-test records unchanged before
owner recovery. No facilitator POST, retry, pending-intent modification or new case
was performed. Owner recovery, uncertainty/session-loss comprehension and human
duration remain pending.

### B08 recovered case and extra approval — 2026-10-14

The owner supplies an approved-state screenshot and says I approved it. Stored-only
export shows exactly one new original; all eight pre-test records are unchanged.
A read-only transaction inside the identity-verified disposable helper PostgreSQL
container compares the new creation mapping with the earlier DOM recovery record:
key and canonical input fingerprint both match. This is facilitator test verification,
not frontend database access, an Odoo read or a facilitator retry/POST.

The recovered case also has Alternative 1 approved at 109 EUR with reason asdasd.
Approval exceeds B08’s save/recovery task. Do not infer whether this was deliberate
extra work or mistaken belief that recovery required approval; ask the owner and
retain the answer before classifying unintended finalizations. First-save uncertainty
and session-loss comprehension, measured human duration and independence remain
unreported, so full B08 remains unassessed. Evidence: pending request,
`owner-B08-recovery-verification.json`, `owner-B08-recovered-case.json` and
`owner-B08-recovered-and-approved.png`. No PDF test or novice outcome is inferred.

### B08 critical first-attempt finding — 2026-10-14

Asked whether approval was extra or thought necessary for recovery, the owner
answers “yes it was needed I think.” Asked about uncertain save/session loss, the
owner reports not knowing and supposes database consistency requires preventing
a save. Record this before explanation: B08 first attempt fails comprehension,
with one task-unintended additional finalization. Confirmation was deliberate
under a mistaken recovery purpose, not an accidental click. The technical recovery
check still passes; it does not establish human acceptance.

The frozen protocol requires stopping promptly on unintended finalization or
critical decision misunderstanding. B09 is not attempted. Saved cases and the
additional approval remain as evidence; no rollback, deletion or ERP mutation is
performed. The API stays running. Clarification: saving/recovering a comparison
does not require approval; a missing response can leave a save unconfirmed; losing
a Reflex session can lose pending recovery details without deleting a saved case.

The [focused correction brief](UX41_RECOVERY_CLARITY_BRIEF.md) proposes clearer
draft/saved/final-decision states, recovery/session copy and clearing stale success
feedback. It is not implemented or retested. Keep this attempt, repair the UI, then
record a fresh source-bound retest before B09. No novice rate/zero mistake count or
full buyer acceptance is inferred; the novice cohort remains absent.

### Owner-requested assisted B09 continuation — 2026-10-14

After the recorded B08 stop, the owner explicitly requests a quick B09 walkthrough.
Continue as assisted exploration on the existing source/runtime, with guided
library navigation to the earlier B06 approval. This is a user-authorized deviation
from the frozen stop sequence, not closure or a retest of the failed B08 attempt.
B09 is not yet attempted and no PDF interruption is staged. Keep the critical
finding, extra finalization and missing novice evidence unchanged. Drive updates
and visual references are topics for subsequent discussion, not edits performed.

### B09 skipped at owner request — 2026-10-14

The owner explicitly skips B09 and moves to Drive updates. No PDF fault was
staged; document reopening, navigation and download remain unverified by this
owner task. Preserve the B08 critical finding and missing unfamiliar-participant
evidence. Ambient navigation to the original case does not establish task success.

Owner clarification: “For b09 Ididn't really got what you mean, write this there”.
The owner did not understand the facilitator instruction. Record this as a task/
facilitation clarity finding; the unattempted product PDF workflow is not assessed
as failed or successful. Keep owner evidence separate from novice acceptance.
