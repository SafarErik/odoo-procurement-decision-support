# Buyer workspace delivery tickets — approved and published

Prepared 2026-10-12 from the user-confirmed brief and
[local specification](UX_UI_INCREMENT_SPEC.md).
Status: **APPROVED AND PUBLISHED — parent #42 and delivery #32–#41; implementation pending**.
Ticket numbers below are local delivery identifiers, not GitHub issue numbers.
Current delivery evidence: [#32 implementation handoff](UX32_LIBRARY_HANDOFF.md).
The approved criteria below remain the contract; later tickets are not implemented
by the saved-case library.
The selected direction is Decision editorial; T19 remains thesis closure after
development and reassessment. No existing T18 issue or parent is modified.

## Delivery graph and sizing

The six specification areas are refined into ten bounded tickets. Guided creation
and comparison are distinct complete buyer tasks. Scenarios and irreversible
approval deserve separate implementation/review contexts. Supplier explanation can
proceed independently of these tasks after the shared shell exists. Recovery and
document work reuse the existing safe backend/immutable artifact, without changing
the renderer. Every implementation ticket includes meaningful checks; ticket 10
consolidates and reassesses, not postpones testing.

| Ticket | Complete buyer-visible outcome | Blocked by |
| --- | --- | --- |
| 1. Find and reopen saved procurement cases | Browse scoped/paged history, distinguish originals/children and open a saved result without a UUID | None |
| 2. Enter curated Practice and preserve case classification | Choose an example, explicitly save it, reopen it in Practice and keep Odoo/legacy work distinct | 1 |
| 3. Navigate a responsive Decision editorial workspace | Use Cases/Open RFQs/Practice and the four case views across desktop/narrow layouts with guarded navigation | 2 |
| 4. Review attributed inputs before creating a comparison | Review captured facts, explicit terms and policy, then save through the existing real API | 3 |
| 5. Compare and explicitly select saved allocations | Read aligned quantities/cost/premium/exposure and select a plan with a persistent review summary | 3 |
| 6. Test disruptions against the original base | Run all five types and understand feasible/infeasible results without losing original facts | 5 |
| 7. Deliberately approve a plan or record No-award | Review an exact selection, provide required attribution/reason and finalize once with purposeful focus | 5 |
| 8. Understand supplier assessments and exact audit evidence | Read accessible supplier explanations and inspect saved inputs/tree/provenance without recalculation | 3 |
| 9. Recover safely and reopen approved documents | Preserve exact pending intent through errors/navigation; reopen approval, navigate PDF and download exact bytes | 7 |
| 10. Reassess the complete buyer experience | Consolidate real-stack/visual/accessibility/query evidence and owner/novice tasks with remaining limits explicit | 4, 6, 8, 9 |

After 3, the ready frontier is 4/5/8. After 5, scenarios (6) and approval (7) are
independent: new scenario controls do not gate approval of an already saved base.
After 7, document/recovery work (9) can use the final review workflow. Ticket 10's
four blockers cover all other tickets transitively; redundant edges are omitted.
This graph permits independent work; it does not authorize parallel agents or
require a particular branch strategy.

Recommended sequential demonstration order is 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
→ 10. Existing APIs/forms/results continue working between slices. No placeholder
navigation or missing follow-up is counted as a completed ticket.

No prefactoring ticket is justified by the inspected modular frontend and existing
API/persistence seams. Necessary small changes belong to their complete slice.
No framework replacement, wide rename or speculative abstraction is introduced.

## Shared contract for all approved tickets

- Follow the specification's bounded company/query/classification contract and
  canonical V2 definitions. Local UX-AC identifiers are verification references,
  not new official requirements. Repository artifacts and UI remain English.
- Preserve Decision editorial and the repository's selected static reference.
  Reflow content rather than reproducing its fixed desktop dimensions. Keep exact
  saved values and semantic selection/state; no invented KPI or model-validity claim.
- Keep Odoo read-only, source-attributed explicit terms, offline synthetic ML,
  original-base scenarios, immutable decisions and backend PDFs. Frontend uses
  HTTP only; token/artifact configuration remain server-side. Practice is not
  isolated storage, and actor attribution is not authenticated identity.
- Preserve old creation fingerprints when catalog context is omitted, stored-only
  GET/replay, V1 readability and old immutable hashes. Do not mass-classify, delete
  evaluation cases, reset owner/Odoo data or change the PDF-content contract.
- Focused checks accompany each slice, with required fast gates before its handoff
  and affected real API/database/browser evidence. Use owned disposable helper
  persistence for reset checks. Keep Quality required and hosted browser CI deferred.
- Loading/errors, keyboard/focus, narrow layout, long labels and feedback semantics
  are implementation acceptance, not work left for ticket 10. Do not weaken exact
  uncertain-request recovery while improving its wording or navigation.
- Handoffs state buyer-visible changes, checks, remaining scope/limits and the next
  capability. Preserve user control of commit/push/merge. Drive writes require their
  own explicit instruction; do not renumber T19 or edit existing issues here.

## 1 — Find and reopen saved procurement cases

**What to build:** A buyer browses recognizable, company-scoped stored original
cases, filters/pages them, expands their stored scenarios and opens the intended
saved result in the existing cockpit. Minimal functioning browser entry is part
of this ticket; it is not an API-only foundation.

**Blocked by:** None (can start immediately).

- [ ] Implement the bounded base/child list contracts: protected server-owned
  company scope, defaults/limits, status/product/ID filters, stable continuation
  and explicit invalid/unavailable/corrupt-data outcomes. No Odoo/model/solver work.
- [ ] Show meaningful product/context/Q/unit/currency/date/decision labels, paged
  base rows and lazy grouped children. Distinguish empty/no matches from backend
  failure. Open the selected saved case without requiring a supplied UUID.
- [ ] Include the compatible empty catalog schema/query join required by discovery.
  Until ticket 2 adds creation classification, cases remain explicitly unclassified
  and browsable through Earlier cases. Never infer Practice from synthetic ML.
  Do not expose all test cases as normal controlled buyer work.
- [ ] Preserve hashes/old snapshots/V1 and UUID retrieval; demonstrate stored-only
  list/open with Odoo/model configuration unavailable. Invalid opening cannot display
  a previous result as the requested case. Supply compatible bookmarkable retrieval.
- [ ] Verify HTTP scope/cursor/filter failures, real PostgreSQL ordering/readback
  and a browser find → expand → reopen task. Measure the specified 1,000-base
  disposable-history/20-row base and child queries with retained raw timings and
  the approved p95 gate; never use owner history for reset/load fixtures.
- [ ] Record library scope configuration/migration prerequisites, run/cleanup and
  any performance/integrity limitation. Keyboard and narrow history remain usable.

**Traceability:** UX-AC-01/03; FR/AC-V2-09/10; NFR-V2-04/05/06/07/08; UX29-03.

## 2 — Enter curated Practice and preserve case classification

**What to build:** A buyer enters a clearly labelled curated exercise, explicitly
creates/saves a fresh synthetic base, runs the chosen supported task and finds it
again in Practice. New prepared Odoo comparisons appear as controlled work, while
legacy cases remain truthfully unclassified.

**Blocked by:** 1 — stored discovery and its compatible catalog storage/query.

- [ ] Provide compare, outage and infeasibility exercise entries using existing
  offline prepared synthetic inputs/scenario APIs. Entry/task selection performs
  no POST; calculation/save is explicit and uses genuine results.
- [ ] Add validated optional creation catalog context and atomically save it with
  a new case. Practice is allowed only on the fully synthetic path; controlled
  only on the prepared Odoo path; reject unsupported example/source combinations.
- [ ] Include supplied context in new intent fingerprints and retain old omitted-
  context fingerprints. Exact replay performs no metadata repair/write; changed
  context under the same key conflicts. Scenarios inherit base classification.
- [ ] Expose source and workspace separately on new/opened cases and history.
  Practice persists only through explicit actions, carries labels into decision/
  document context and promises neither isolation nor reset. No shared finalized
  case is silently reused as a fresh editable exercise.
- [ ] Verify atomic rollback/replay/conflict/inheritance with real PostgreSQL and
  HTTP tests, plus browser enter → save → scenario → library reopen. Confirm old
  hashes and V1/legacy retrieval remain unchanged; keep uncertain intent exact.

**Traceability:** UX-AC-02/03/05; FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03/10.

## 3 — Navigate a responsive Decision editorial workspace

**What to build:** A buyer can enter Cases, Open RFQs or Practice, open work and
move among Plans/What-if/Suppliers/Audit in the chosen visual system. Desktop and
narrow layouts keep case context and next action visible with safe navigation.

**Blocked by:** 2 — real Practice and classified/library destinations must exist.

- [ ] Apply the selected editorial shell, typography, semantic palette and case
  hierarchy across functioning destinations; preserve compatible old entries
  and the RFQ ledger without implying arbitrary RFQ-to-planning conversion.
- [ ] Reflow global navigation to a labelled drawer when necessary. Keep product,
  demand/unit/currency, source, recorded dates, base/child identity and status ahead
  of help paragraphs. No inert placeholders count as delivered destinations.
- [ ] Guard explicit navigation against dirty creation/scenario drafts with Stay/
  Discard. Pending writes cannot be discarded or replaced by case/view/Practice
  changes; route handlers preserve the original recovery context/key/payload.
  Invalid IDs/views fail safely. Do not promise durable closed-session recovery.
- [ ] Preserve status/alert roles, labels, visible focus, dialog/drawer focus return
  and non-colour state. Verify desktop/tablet/390/320 layouts, keyboard navigation,
  real browser 200% text zoom and reduced motion; retain exact-table accessibility.
- [ ] Recheck entry → classified/earlier case → case sections → global return in
  a real browser with backend unavailable and pending-save navigation attempts.
  Document unrun speech/physical-phone gates rather than inferring them from DOM.

**Traceability:** UX-AC-04/06/13/15; FR/AC-V2-09/10; NFR-V2-05/06/07; UX29-03/04/06/08/10.

## 4 — Review attributed inputs before creating a comparison

**What to build:** A buyer reviews prepared facts, supplies explicit business
terms, checks policy/validity and deliberately saves a comparison through the
existing API, with readable validation and a clear saved-result transition.

**Blocked by:** 3 — functioning shell/context/draft navigation.

- [ ] Provide facts → terms → review/calculate guidance without a compulsory
  onboarding tour. Preserve supported quantity/date/capacity/availability/MOQ
  absence/applicability/policy validation and accessible field errors.
- [ ] Distinguish captured Odoo preview from the new backend reread, supplied
  terms from quotation facts, and synthetic ML from observed evidence. Preserve
  offline preparation/trusted artifacts; no arbitrary model/file/quote discovery.
- [ ] Submit genuine synthetic/controlled requests with ticket 2 classification;
  preserve exact intent on uncertain outcomes and guard repeat submission.
  On success, show the correct saved result and move focus purposefully.
- [ ] Verify creation/validation/recovery through HTTP/browser seams and affected
  existing Odoo expectation/provenance tests. Exercise narrow forms and keyboard
  review; document real live checks separately from synthetic fixtures.

**Traceability:** UX-AC-07; FR/AC-V2-01/09; NFR-V2-05/07; UX29-04/06/10.

## 5 — Compare and explicitly select saved allocations

**What to build:** From any saved case, a buyer reads an aligned comparison of
quantities, costs, premiums and exposure, explicitly selects a valid plan and
sees its exact identity/allocations in the persistent review summary.

**Blocked by:** 3 — shared workspace. The redesigned creation form is not required;
existing creation and library fixtures already provide saved plans.

- [ ] Match the selected editorial comparison arrangement and selected-state
  grammar. Keep exact quantities/cost/absolute and relative premium/exposure,
  delivery/constraint explanations and source limits accessible.
- [ ] Require explicit plan selection; never preselect approval or finalize on
  selection. The review strip mirrors the saved selected plan. Keep existing final
  review functional until ticket 7 replaces its presentation; no placeholder action.
- [ ] Retain subordinate cost/exposure chart and exact table equivalent; distinguish
  synthetic proxy from probability. Handle no-distinct-alternative, single-plan,
  infeasible/partial/technical outcomes without invented results.
- [ ] Reflow comparison and review context at narrow widths/200% text zoom without
  covering focus/content. Test 3/5/10 suppliers, variable alternative counts and
  long/non-Latin labels; displayed exact values match actual saved results.
- [ ] Add/adjust meaningful browser and mapping checks for selection/comparison
  without duplicating MILP algorithms or measuring old HTTP workloads again.

**Traceability:** UX-AC-08/09; FR-V2-06/07/09, AC-V2-05/07/09; NFR-V2-07; UX29-04/05/10.

## 6 — Test disruptions against the original base

**What to build:** A buyer reviews explicit changed assumptions, creates one of
the five supported scenarios and compares its saved result with the original
base, including honest infeasibility without losing original quantities/cost.

**Blocked by:** 5 — the aligned saved-plan comparison and exact baseline display.

- [ ] Retain outage, capacity reduction, demand increase, price increase and the
  existing bounded combined change, with readable drafts and original-base targeting
  even when entered from a child. Use the existing backend MILP/scenario API.
- [ ] Show original and saved-child status/allocations/cost/exposure with meaningful
  differences. In infeasibility retain original facts and show missing child metrics
  as unavailable; never zero, invented plans or silently relaxed constraints.
- [ ] Explain changed-demand totals and simulated-price provenance. Keep scenario
  source/classification and grouped history intact; return to the base is explicit.
  Preserve existing child-approval prohibition without waiting for ticket 7.
- [ ] Verify every type, combined limits, infeasible result and lineage through
  real API/browser tasks. Preserve draft/pending navigation, purposeful focus and
  narrow/keyboard comparison; reuse immutable/constraint coverage.

**Traceability:** UX-AC-10; FR/AC-V2-08, AC-V2-07/09; NFR-V2-06/07; UX29-04/06/07.

## 7 — Deliberately approve a plan or record No-award

**What to build:** A buyer reviews the exact selected original-base allocation,
cost/context and attribution, then knowingly finalizes it once or records a
separate reasoned No-award, with the immutable saved outcome clear on reopening.

**Blocked by:** 5 — explicit selection and its exact review summary. Redesigned
scenario controls do not gate finalization of an existing saved base.

- [ ] Present selected identity/quantities/cost/exposure/dates plus actor and reason
  before deliberate confirmation. Alternative and No-award retain required reasons;
  separate No-award from approval. Cancel performs no write; selection is not approval.
- [ ] Preserve backend finalization/idempotency/conflict rules and child ineligibility.
  Guard duplicate clicks, retain exact pending intent and focus/announce the saved
  outcome; show immutable choice/time/reason instead of editable approval controls.
- [ ] Explain Practice/source limits, attribution versus authenticated identity and
  no Odoo order creation. Keep existing document access working until ticket 9;
  No-award has no approved-plan PDF.
- [ ] Verify alternative/reason validation, deliberate confirmation/cancel, separate
  No-award, stored reopening and child rejection in browser/API checks; retain real
  PostgreSQL conflict/rollback/content integrity evidence where affected.

**Traceability:** UX-AC-11; FR/AC-V2-11, AC-V2-09/10/12; NFR-V2-06/07; UX29-05/06.

## 8 — Understand supplier assessments and exact audit evidence

**What to build:** A buyer understands saved supplier classes/constraints and
their evidence limits, then inspects exact inputs, tree paths, provenance and
versions without developer prose dominating the ordinary task.

**Blocked by:** 3 — shared case navigation/layout. New comparison/scenario/approval
presentation is not required to inspect an existing saved case.

- [ ] Lead with readable classes, exclusions/binding constraints, sample/reference
  time and synthetic evidence limits; do not invent calibrated probability or
  observed-history/model promotion.
- [ ] Retain exact saved inputs/policy, paths, model/solver versions, provenance and
  lineage in Audit. Use progressive disclosure without hiding critical source or
  authority limits; move execution scripts to contextual help/Practice/runbooks.
- [ ] Keep fully stored-only reads and exact value serialization; no retraining,
  upstream refresh, executable artifact selection or business rules in Reflex.
- [ ] Verify buyer explanation → exact evidence tasks, long/missing labels, keyboard
  disclosure/scoped scrolling and narrow/zoom layouts against real saved values;
  preserve feedback roles and readable focus.

**Traceability:** UX-AC-12; FR-V2-02/03/07/09, AC-V2-02/03/07/09; NFR-V2-03/07; UX29-04/10.

## 9 — Recover safely and reopen approved documents

**What to build:** A buyer understands uncertain saves and safely resends the same
intent; after approval they can reopen its saved summary, navigate PDF pages and
download the exact artifact even when document access fails and recovers.

**Blocked by:** 7 — the completed deliberate review/approved-state workflow.

- [ ] Improve distinct error/conflict/pending recovery copy and actionable support
  detail across create/scenario/decision. Keep ticket 3 navigation guards intact;
  resend exactly the original payload/key, never automatic POST/new intent/false
  “not saved”. State session-loss limits without adding a durable outbox.
- [ ] Show saved approved summary, page indicator/previous/next, zoom/fit and exact
  download using the existing PDF renderer/viewer. Preserve exact content/hash/bytes,
  Practice labels in access context and existing eligibility; no watermark rewrite.
- [ ] A real PDF/backend failure keeps approval/selection/audit visible and retries
  document access only. Finalized conflicts never suggest another approval attempt.
- [ ] Exercise genuine GET/create/finalize/PDF faults and explicit recovery in the
  real-stack browser, including navigation while pending, unchanged intent and
  no duplicate decision. Verify reopen/render/byte-identical download and keyboard/
  narrow/zoom PDF navigation; PDF zoom does not replace browser text-zoom evidence.
- [ ] Retain existing immutable document/decision tests. Stop scope at presentation,
  state and recovery: no renderer redesign, PDF-content migration or new service.

**Traceability:** UX-AC-13/14; FR/AC-V2-09/10/11/12; NFR-V2-05/06/07; UX29-06/08/09.

## 10 — Reassess the complete buyer experience

**What to build:** An evaluator/owner can reproduce the complete redesigned task
flow and see defensible technical, visual/accessibility and human-usability outcomes,
with any failed, pending or unassessed gate stated accurately before final acceptance.

**Blocked by:** 4, 6, 8, 9 — the completed creation, disruption, explanation and
decision/recovery/document paths; all other tickets are covered transitively.

- [ ] Consolidate affected real-stack Chromium flow: Practice → create → exact
  comparison → scenario → explicit alternative decision → library reopen → PDF;
  separate No-award and actual backend recovery. Preserve raw evidence/SHA/versions
  and strict integrity; compilation is not a hosted browser pass.
- [ ] Reconcile all UX-AC-01–16 with canonical FR/AC/NFR and UX29-03–10. Confirm
  selected design consistency, keyboard, tablet/narrow widths, actual 200% browser
  text zoom, reduced motion, long/non-Latin/missing data and the new list-query gate.
  Retain slice evidence rather than rerunning unchanged workloads without reason.
- [ ] Run the owner task sheet and freeze the protocol before 3–5 unfamiliar
  participants: find/open without UUID, explain sources/persistence, compare,
  feasible/infeasible disruptions, deliberate approve/decline, recover, reopen/PDF.
  Record independent completion, assistance, mistakes, human time and comprehension.
- [ ] Apply the approved ≥80% independent completion per essential task
  with 3–5 unfamiliar participants (round required successes up) and zero
  unintended finalizations or unresolved critical source/decision misunderstandings.
  Fix critical findings and repeat affected
  tasks, retaining failures; no post-observation threshold relaxation.
- [ ] Separate technical delivery, owner/visual approval and novice validation.
  Missing participants remain NOT ASSESSED; screen-reader/physical-phone/zoom gaps
  retain their named gate. Pending human evidence cannot pass final buyer acceptance.
- [ ] Produce a dated handoff/assessment: problem → decision → behavior → evidence
  → limitation → thesis relevance. State remaining blockers and next work; no T19,
  tracker closure, merge or Drive update is implied by a passing technical subset.

**Traceability:** UX-AC-15/16 and consolidation of 01–14; AC-V2-09/13;
NFR-V2-04/08; UX29-03–10; thesis chapters 4/6/7.

## Approval and publication record — 2026-10-12

The user approved all ten delivery tickets, their dependencies and a new
specification parent (eleven new issues), plus the library and buyer-reassessment
gates. These are prospective scoped acceptance contracts, not measured facts or
changes to canonical V2 requirements.

Parent: [#42 — Buyer workspace UX/UI: find, compare and decide](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42).

| Delivery | GitHub issue | Blocked by |
| --- | --- | --- |
| 1 | [#32: Find and reopen saved procurement cases](https://github.com/SafarErik/odoo-procurement-decision-support/issues/32) | None |
| 2 | [#33: Enter curated Practice and preserve case classification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/33) | [#32](https://github.com/SafarErik/odoo-procurement-decision-support/issues/32) |
| 3 | [#34: Navigate a responsive Decision editorial workspace](https://github.com/SafarErik/odoo-procurement-decision-support/issues/34) | [#33](https://github.com/SafarErik/odoo-procurement-decision-support/issues/33) |
| 4 | [#35: Review attributed inputs before creating a comparison](https://github.com/SafarErik/odoo-procurement-decision-support/issues/35) | [#34](https://github.com/SafarErik/odoo-procurement-decision-support/issues/34) |
| 5 | [#36: Compare and explicitly select saved allocations](https://github.com/SafarErik/odoo-procurement-decision-support/issues/36) | [#34](https://github.com/SafarErik/odoo-procurement-decision-support/issues/34) |
| 6 | [#37: Test disruptions against the original base](https://github.com/SafarErik/odoo-procurement-decision-support/issues/37) | [#36](https://github.com/SafarErik/odoo-procurement-decision-support/issues/36) |
| 7 | [#38: Deliberately approve a plan or record No-award](https://github.com/SafarErik/odoo-procurement-decision-support/issues/38) | [#36](https://github.com/SafarErik/odoo-procurement-decision-support/issues/36) |
| 8 | [#39: Understand supplier assessments and exact audit evidence](https://github.com/SafarErik/odoo-procurement-decision-support/issues/39) | [#34](https://github.com/SafarErik/odoo-procurement-decision-support/issues/34) |
| 9 | [#40: Recover safely and reopen approved documents](https://github.com/SafarErik/odoo-procurement-decision-support/issues/40) | [#38](https://github.com/SafarErik/odoo-procurement-decision-support/issues/38) |
| 10 | [#41: Reassess the complete buyer experience](https://github.com/SafarErik/odoo-procurement-decision-support/issues/41) | [#35](https://github.com/SafarErik/odoo-procurement-decision-support/issues/35), [#37](https://github.com/SafarErik/odoo-procurement-decision-support/issues/37), [#39](https://github.com/SafarErik/odoo-procurement-decision-support/issues/39), [#40](https://github.com/SafarErik/odoo-procurement-decision-support/issues/40) |

All eleven issue bodies, titles, open states and `ready-for-agent` labels were
read back and verified. All 48 delivery acceptance checkboxes remain unchecked.
The parent lists all children; each child links its parent and actual blockers.
Native sub-issue/dependency tools are unavailable, so these are explicit Markdown
relationships, not claimed native edges. The publication preserved existing issues
and parents. Two temporary automatic-review rate limits resolved through the same
approval process; no uncertain creation was blindly retried.

Only #32 is initially unblocked. After #34, #35/#36/#39 can proceed independently;
after #36, #37 and #38 are independent; #40 follows #38. Final reassessment #41
requires #35/#37/#39/#40 and covers all earlier tickets transitively.

Library acceptance: 1,000 disposable bases plus children, two warm-ups and 30
measurements per selected 20-row query, observed local p95 ≤1 second; preserve raw
timings/failures. Buyer gate: 3–5 unfamiliar participants, ≥80% independent
completion per essential task (round up), zero unintended finalizations or
unresolved critical source/decision misunderstandings. Missing participants remain
NOT ASSESSED and cannot establish final buyer-experience acceptance.

This index records GitHub publication, not a competing local tracker. Implementation,
benchmarks, browser/participant reassessment and Drive writes remain pending.
No services or application tests were run for publication; local document checks
and GitHub readback verify only the planning artifacts. Commit/push/merge remain
user-controlled. Next capability: find and reopen saved procurement cases (#32).
