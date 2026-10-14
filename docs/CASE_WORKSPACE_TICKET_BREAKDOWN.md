# Selected-case workspace — proposed delivery tickets

Date: 2026-10-14. Status: local proposed breakdown; no GitHub numbers assigned.
Parent: proposed next case workspace increment (unpublished).
Authority: [implementation specification](CASE_WORKSPACE_INCREMENT_SPEC.md),
[confirmed structure/design brief](CASE_WORKSPACE_DESIGN_BRIEF.md), existing canonical
V2 requirements/ADRs. All criteria below are prospective, not measured PASS.

## Dependency map and publication approach

| Slice | Buyer-visible capability | Blocks on | Proposed readiness |
| --- | --- | --- | --- |
| S1 | Understand comparison saving, recovery and separate finalization | None | ready-for-agent |
| S2 | Open a compact case Overview and navigate focused case views | S1 | ready-for-agent after blocker |
| S3 | Inspect one supplier beside its saved explanation | S2 | ready-for-agent after blocker |
| S4 | Compare plans beside the chosen allocation | S2 | ready-for-agent after blocker |
| S5 | Test a disruption beside the original result | S4 | ready-for-agent after blocker |
| S6 | Review the decision and access the approved PDF in one place | S4 | ready-for-agent after blocker |
| S7 | Browse RFQ summaries and saved cases in a lightweight overview | S2 | ready-for-agent after blocker |
| S8 | Verify the integrated workspace and resolve human acceptance findings | S3, S5, S6, S7 | agent technical checks; ready-for-human participant stage |

S1's technical fix enables downstream implementation; its owner retest is required
before resolving the critical human finding, not a reason to invent a technical
blocker for every UI task. S8 carries the remaining owner/novice gate.

Publish only after the local detailed contracts have been reviewed. Use a new
parent rather than redefine #42. At publication, reuse existing #41 for the human
reassessment obligation instead of creating a duplicate novice-validation issue;
S8 defines the changed-source technical consolidation and linkage into that record.
Do not close #41/#42 or earlier issues as a side effect. Parent dependencies and
evidence links must name actual published IDs; do not guess the next issue number.

## Shared constraints for every slice

- Keep the confirmed green/mint/purple palette, desktop horizontal task/detail
  arrangement, readable narrow reflow and supported API-only Reflex baseline.
- Preserve exact saved values and source/workspace/lineage. No invented scores,
  global totals, supplier images, model features, statuses or recommendations.
- Preserve immutable storage/PDF, V1 compatibility, original-base scenarios,
  explicit selection/finalization and existing server-side token/artifact trust.
- Guard dirty/pending navigation, purposefully manage focus, and keep contextual
  labels/errors/status. Every slice includes its own narrow/keyboard checks.
- Use focused state/API/browser checks during changes; required fast/static checks
  once before handoff. Actual server-side faults use owned API processes and
  disposable helper persistence, never Odoo/owner database resets.
- Record source identity, executed/unrun gates, failures and next capability.
  Reuse unchanged checks/measurements; no repeated benchmark or speculative backend
  refactor solely for presentation. Commit/push/merge remain user-controlled.

## S1 — Make comparison saving and approval clearly separate

**Outcome:** a buyer recovers an uncertain comparison save without approving it
to complete recovery. Preparing another case does not show an old final-decision
success message. Follow [the focused correction](UX41_RECOVERY_CLARITY_BRIEF.md).

Acceptance:

- [ ] Distinguish unsaved draft, saved/awaiting-decision comparison and immutable
  final decision. Use Calculate and save comparison and Comparison saved.
  Approval is a separate choice, including the recovered-save outcome.
- [ ] Explain may-already-be-saved uncertainty and the session-bound pending record
  separately from durable backend cases. Reuse exact URL/input/key and navigation
  guards; no automatic retry, new key, rollback or outbox.
- [ ] Clear stale notice/review feedback at the shared new-context/reset seams,
  covering Practice, prepared synthetic/Odoo creation and relevant scenario/decision
  entry without clearing an active pending request or saved decision.
- [ ] Verify affected resets/recovery state and a genuine uncertain-save browser
  task with one stored case and no finalization to finish recovery. Preserve B08
  attempt 1; record a separate neutral owner retest and its actual outcome.

Traceability: FR/AC-V2-09/10/11; NFR-V2-05/06/07;
UX-AC-11/13; owner B08. Initial implementation can proceed without new Odoo data.

## S2 — Open a compact case Overview and focused task navigation

**Outcome:** a reopened saved case shows its demand/result/state and useful next
action before technical metadata, while old case bookmarks remain valid.

Acceptance:

- [ ] Implement Overview/Suppliers/Plans/Scenarios/Decision & PDF navigation and
  labelled secondary Audit. Add overview/decision to shared view validation;
  retain existing plans/whatif/suppliers/audit values and omitted-view Plans behavior.
- [ ] Build the compact context band and at most four factual overview summaries.
  Keep source/Practice/original-child context visible; disclose exact IDs/time/
  provenance without a default metadata wall. Do not select a plan implicitly.
- [ ] Keep each existing task functional during the transition. Compose existing
  components behind the new views; later slices improve their internal layout,
  not replace working behavior with placeholder controls.
- [ ] Verify new/legacy deep links, safe invalid open, case identity reset, Audit
  return, dirty/pending guards, result focus, drawer and narrow/200% zoom behavior
  through state/browser seams. Navigation/reopening never creates or recomputes.

Traceability: FR/AC-V2-09/10; NFR-V2-06/07;
UX-AC-04/06/07/15. Source seams: planning state/page and shared shell/theme.

## S3 — Inspect a supplier beside its saved assessment explanation

**Outcome:** select a supplier row to inspect the evidence that actually produced
that supplier's class, without changing the procurement plan.

Acceptance:

- [ ] Render case supplier terms and actual saved class/score; selection drives a
  contextual tree-path/sample/reference/applicability panel. It is independent of
  allocation-plan selection and performs no write/upstream/model action.
- [ ] Keep historical schedule adherence distinct from verified supplier promise;
  source/cutoff/count and synthetic limitations remain understandable at point of use.
  Do not create risk categories, market pricing or model-confidence claims.
- [ ] Keep exact evidence in Audit, with a labelled return to supplier context.
  Selecting/disclosing a row uses the loaded validated case, without N+1 requests.
- [ ] Verify mapping to the selected supplier, missing/long/non-Latin data,
  changed-case selection reset, keyboard detail access and desktop/narrow layouts
  against actual saved values. Use case data, not a new global directory.

Traceability: FR-V2-02/03/07/09; AC-V2-02/03/07/09;
UX-AC-12. Historical/model validity remains as defined by the saved artifact.

## S4 — Compare exact plans beside the selected allocation

**Outcome:** a buyer understands EUR 102 minimum versus EUR 109 alternative,
the EUR 7 premium and the different supplier split before choosing a plan.

Acceptance:

- [ ] Present minimum cost and actual distinct alternatives with aligned cost,
  premium, exposure and allocation values. No Recommended balanced default or
  unproven single-supplier savings comparison is introduced.
- [ ] Explicit selection updates a contextual allocation/terms panel and concise
  persistent next-step summary; Review decision enters the dedicated view with
  the exact saved plan. Selection/review alone perform no finalization.
- [ ] Keep exact money/fractions beside approximate scales and chart equivalence.
  Single/no-distinct/incomplete/infeasible/technical outcomes are honest; returned
  plan/supplier counts derive from saved results, not requested epsilon count.
- [ ] Verify 3/5/10 suppliers, variable alternatives, changed-case reset,
  selected versus recorded approved identity, long labels and keyboard/narrow/zoom
  comparison. Preserve approval/PDF content and existing mapping/solver contracts.

Traceability: FR-V2-06/07/09; AC-V2-05/07/09; UX-AC-08/09.

## S5 — Compare a disruption with its immutable original

**Outcome:** a buyer sees the original result beside a saved feasible/infeasible
simulation and understands which reference plan is being compared.

Acceptance:

- [ ] Arrange supported choice/parameters and original/scenario results with
  contextual assumptions/changes. Keep all five existing types and combined bounds;
  child entry always targets the original. Calculation/save remains explicit.
- [ ] Identify the compared minimum-cost original/scenario reference. Local
  Alternative 1 numbers do not imply matching allocation; distinguish same-demand
  comparisons from changed-demand totals and simulated prices from Odoo quotations.
- [ ] Preserve original cost/allocation through child infeasibility. Missing child
  values are unavailable, not zero. Return to original is stored retrieval; no
  reset/mutation, child finalization or multi-period outage model is added.
- [ ] Verify all types, feasible/infeasible outcomes, child-to-original lineage,
  precise delta display and genuine original-read/uncertain-save recovery, including
  guards, focus and desktop/narrow layouts. Reuse the existing MILP/API.

Traceability: FR/AC-V2-08; NFR-V2-06; UX-AC-10/13.

## S6 — Review the decision and access its approved document together

**Outcome:** a buyer can deliberately approve one saved original-base plan or
decline all plans, and later find its immutable decision/document in one view.

Acceptance:

- [ ] Place the existing exact selected terms, actor/reason and read-only review/
  cancel/confirm in Decision & PDF. Other views have next-step navigation rather
  than duplicated approval forms. Alternative/No-award reason rules remain intact.
- [ ] Explain Decline all plans as a permanent No-award decision with no approved
  PDF. Show saved choice/time/reason read-only; maintain base-only eligibility and
  explicit original navigation from children. No reviewer queue or Request changes.
- [ ] Show eligible approved terms and existing page/fit/zoom/download together.
  Pending/no-award/child states have no working approved export. PDF errors preserve
  the decision and retry only document access; downloaded bytes match the artifact.
- [ ] Verify deliberate selection/review/cancel/confirmation, duplicate/uncertain/
  conflict behavior, stored reopening and actual PDF failure/retry/hash through
  browser/API seams, with keyboard/dialog return and narrow/200% zoom controls.

Traceability: FR/AC-V2-11/12; NFR-V2-05/06/07; UX-AC-11/13/14.
No storage, renderer or Odoo-write contract change is required.

## S7 — Browse lightweight RFQ summaries and saved cases

**Outcome:** a returning buyer finds a stored case, while a new buyer can inspect
currently available open RFQ summaries without a false generic conversion promise.

Acceptance:

- [ ] Provide separate RFQ and saved-case entries using existing HTTP clients;
  preserve root/RFQ/Practice routes and guarded global navigation. New saved-case
  entry links to Overview explicitly; historical bookmarks stay compatible.
- [ ] Keep product/demand/date/status/source/Practice labels, actual supported
  library filters, bounded paging and lazy scenarios. Retain Earlier/unclassified
  cases. Full IDs stay copyable; no fabricated persistent display alias or global totals.
- [ ] Render only existing RFQ summary fields and actual retrieval time/refresh.
  Clearly name the fixed prepared Odoo comparison action. Do not advertise generic
  row conversion, unsupported product/due-date/quote-count fields, unlimited search
  or persistent connected/synced status without a verified read.
- [ ] Verify company/query/cursor constraints, empty/no-match/loading/failure,
  recognized case → Overview → Decision & PDF reopening, RFQ unavailable handling
  and narrow/keyboard layout. Retain unchanged #32 p95 evidence unless queries change.

Traceability: FR-V2-01/09/10; AC-V2-01/09/10; NFR-V2-05/06/07;
UX-AC-01–06. New quotation-selection data is not a prerequisite for this honest view.

## S8 — Consolidate the changed workspace and carry acceptance into #41

**Outcome:** the owner can distinguish implemented behavior from technical, visual
and human evidence before the new workspace or old parents are declared complete.
Reuse #41 for final human acceptance; this is not a duplicate cohort obligation.

Acceptance:

- [ ] Run the affected genuine full-stack saved workflow and fault/document
  checks, required fast gates and the named visual/accessibility matrix. Record
  source/versions and reused versus freshly executed evidence; no blanket CI PASS.
- [ ] Version the changed task protocol after approval of instructions/fixtures,
  retaining UX41-v1 and its failed/skipped owner records. Test B08 save/recovery
  meaning neutrally; simplify B09 into clear find/reopen and document-access tasks
  with facilitator fault staging described separately from owner actions.
- [ ] Record owner retests separately, including assistance and unset timing where
  not measured. A critical misunderstanding or unintended finalization remains a
  failure until corrected/retested; no retrospective reinterpretation of attempt 1.
- [ ] Apply the existing 3–5 novice / ≥80% independent completion per essential
  task / zero critical misunderstanding or unintended finalization gate. Round
  success counts up. Missing participants stay NOT ASSESSED; owner/agent runs do
  not enter the novice denominator. Carry findings/evidence into existing #41/#42.
- [ ] Deliver dated traceability and handoff with current capability, blockers,
  needed human actions and next integration dependency. Technical delivery may be
  reviewed separately, but human acceptance and parent closure cannot be inferred.

Traceability: AC-V2-09/13; NFR-V2-04/08; UX-AC-15/16.
Human sessions are ready-for-human once the revised runtime/protocol is available.

## Separate integration investigations, not executable UI tickets

These remain needs-info/needs-triage proposals until bounded primary evidence and
an explicit contract are available. Do not publish a ready-for-agent implementation
ticket by filling unknowns with screenshot fields.

### I1 — Start a comparison from selected Odoo quotations

Question: which explicitly selected, company-scoped quotation group/lines can be
validated into one product/unit/currency and at least three known suppliers using
the existing comparison reader, with separately supplied business terms?

Read-only evidence: inspect supported ports/mapping and a controlled authorized
Odoo sample; record validated selection identifiers, boundaries, freshness and
missing terms. Resolve product/line quantities/date meaning and group membership
without heuristic RFQ aggregation. Close the investigation with GO/NO-GO, smallest
adapter/application/API extension and negative contracts for mismatch/missing/stale
expectations. Manual Odoo setup follows AGENTS.md; no UI automation or Odoo writes.

New comparison reads Odoo at save; exact retry/GET remain stored-only. The model
stays synthetic unless I3 separately promotes a validated observed artifact.
This investigation does not implement generic quotation conversion itself.

### I2 — Show scoped supplier, confirmed PO and receipt context

Question: what reliable directory/history facts can the existing bounded reader/
projection provide for selected case suppliers, at a stated reference time?

Evidence: verify identity/company/time/limit, permission and receipt/date semantics;
reuse T7/T8 contracts. Distinguish Expected Arrival adherence from supplier promise,
sample count from global performance and missing history from zero. Decide the
smallest read-only API/projection and UI contract; omit unsupported photos, market
benchmarks, global trend cards and connection indicators. This is supporting data,
not supplier recommendation, automatic training or a validated observed model.

### I3 — Establish the observed-history training/promotion boundary

Question: does available Odoo history meet the official controlled-history
obligation and support the chosen target, cutoff, feature and disjoint time/
supplier evaluation requirements without leakage?

Evidence: audited extraction/source, label/feature construction, sample and support
limits, split, metrics and artifact/mapping/validity contract. Missing adequate
history is a blocker, not permission to relabel generated receipts or patch a
synthetic manifest. Preparation/training is offline; new promotion requires its own
accepted data/model specification and actual evaluation. No HTTP training,
browser-selected artifact or predictive-superiority/calibration claim is implied.

These investigations may be planned independently of S1–S7, but their UI/data
extensions and I3 promotion must wait for their own GO decisions and validation.
No new canonical requirement IDs, Odoo models/fields or training source are invented.
