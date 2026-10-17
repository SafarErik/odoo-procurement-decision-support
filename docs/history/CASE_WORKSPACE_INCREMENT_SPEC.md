# Procurement overview and selected-case workspace — implementation specification

Date: 2026-10-14. Status: local specification draft; approved structure, proposed
delivery details. No application implementation or GitHub publication in this step.
Baseline: `dc2cf575f8abf1bd9c29e1b549fad72b1a822388`.

## Decision and source authority

The owner confirmed a lightweight RFQ/Saved cases overview and a selected-case
workspace with Overview, Suppliers, Plans, Scenarios and Decision & PDF as primary
tabs, with exact Audit as a secondary entry. Keep green/mint/purple and use the
eight supplied screenshots as layout references. The [design brief](CASE_WORKSPACE_DESIGN_BRIEF.md)
records reference identities, adaptations and the buyer task. This specification
defines that structure's behavior; illustrative reference data is not a requirement.

The official task remains 423.589/25/140, routed through
[project alignment](agents/project-baseline.md). Refreshed read-only sources:
[00 status](https://docs.google.com/document/d/1X2WGVVYn0j1ymX0cv5kQQGIaJiEc7pcLSZYDIrXA3VU/edit),
[06 requirements](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit),
[02 roadmap](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit),
and [03 ADRs](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit).
Their October 14 additions preserve technical versus human acceptance and the
new dashboard direction. Their earlier publication statements remain dated history:
local HEAD now includes the owner's #41 commit `dc2cf57`; this specification does
not infer current remote publication/CI or update Drive.

The original [#42 specification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/42)
keeps its original definitions and open reassessment. This is a proposed next
increment, not retroactive fulfillment or a replacement of #41/#42's human gates.
Canonical FR/NFR/AC and accepted ADR identifiers remain unchanged.

## Problem and buyer-visible result

The buyer can compute and save real controlled results, but long vertical result/
metadata pages obscure the relationship among assessment, allocation, scenarios
and a human decision. The owner confused recovery of a saved comparison with
approval; later PDF-test instructions were unclear. A new layout must improve
task understanding as well as visual hierarchy.

Deliver a case workspace where a buyer can open recognizable saved work, inspect
one supplier, compare exact allocation alternatives, test an assumption and review
the chosen plan beside relevant detail. Saving a comparison and finalizing a
decision must be visibly separate. Approval enables the immutable document;
No-award records that no plan was approved. Neither action creates an Odoo PO.

## Scope and data readiness

| Work | This increment | Separate dependency |
| --- | --- | --- |
| Saved-case overview and selected-case dashboard | Existing stored list/get, prepared creation, scenario, decision and PDF APIs | No database/API expansion solely for presentation |
| RFQ overview | Present the existing bounded RFQ summary and explicit refresh honestly | General quotation-group/line selection and creation from that selection |
| Case supplier evaluation | Saved assessment, history/reference context and exact path for suppliers in this case | Global supplier directory and broader linked receipt/PO history |
| Model evidence | Current separately synthetic model and saved inference; actual metrics in Audit | Audit and promote an offline model trained on observed Odoo history |
| Human acceptance | Correct owner findings and reassess changed tasks; keep existing gate | No waiver of absent unfamiliar-buyer evidence |

The later dependencies are important product work, but are not silently bundled
into a UI ticket. [The breakdown](CASE_WORKSPACE_TICKET_BREAKDOWN.md) defines their
questions and bounded evidence needed before executable integration specifications.

### Existing contracts verified during planning

- `GET /api/v1/procurement/rfqs`: limit defaults to 20, allowed 1–50. Returned
  summaries expose source ID, reference, vendor name, order date, status and money;
  response count describes returned items and retrieved_at the actual read. It
  does not expose product, ordered quantity, due date, supplier-quote count,
  quotation-group discovery, global totals or cursor paging.
- Saved library: backend-owned company, workspace controlled/practice/unclassified,
  decision status all/draft/approved/no_award, trimmed product/case-ID search up to
  80 characters, limit default 20 and 1–50, context-bound cursor and lazy children.
  `draft` means a saved comparison awaiting decision, not an unsaved form.
- Saved case GET/exact POST replay reuse immutable data. The UI may format or
  project validated values but may not evaluate constraints, train, score or solve.
- Existing `/from-odoo` creates from a fixed prepared comparison, re-reading and
  checking quotations for a new save. Its model history remains synthetic. It is
  not a generic RFQ-row-to-comparison operation.

Code navigation used CodeGraph first; its flagged source/omitted relevant ranges
were inspected directly in planning state/page, RFQ route and library validation.
Source revisions/readiness notes are in ignored
`.artifacts/case-workspace-spec-20261014/sources.json`. This is contract inspection,
not a new runtime verification.

## User tasks

1. Browse saved work by meaningful product/demand/date/status and open the exact case.
2. Understand captured quotation facts, supplied terms, synthetic assessment and
   Practice persistence without reading a wall of developer metadata.
3. Inspect a supplier's recorded class/path beside applicable terms and sample context.
4. Compare minimum cost and actual distinct alternatives, then explicitly select
   one saved plan while understanding its premium, split and model exposure.
5. Run a supported disruption and compare its proven result with the original
   without mistaking changed demand, simulated prices or local plan numbers.
6. Review and confirm a final approval, or separately decline all plans with a reason.
7. Reopen a saved decision and access its eligible PDF, including document failure/retry.
8. Recover an unconfirmed save with the original request/key, without extra approval.

## Composition and navigation contract

Retain current shared theme and components; no framework/dependency upgrade is
required by this specification. A compact case band leads with product, demand/
unit, currency, required date, outcome, Practice/source and original/scenario context.
Captured/reference time, save time and decision time have distinct labels. Exact
UTC, full IDs/hashes and provenance remain accessible via Audit/support detail.

| Primary view | Route view value | Working area and context |
| --- | --- | --- |
| Overview | `overview` (new) | Concise result, saved state and next step; selected-plan summary only after explicit selection |
| Suppliers | `suppliers` (existing) | Case supplier table plus one supplier's saved explanation/context |
| Plans | `plans` (existing) | Exact alternatives plus the selected allocation/premium/constraints |
| Scenarios | `whatif` (existing, relabelled) | Supported parameters and saved original/scenario comparison plus changes |
| Decision & PDF | `decision` (new) | Chosen terms/reason/review, or immutable decision and eligible document |
| Audit, secondary | `audit` (existing) | Complete exact saved input/evidence; labelled return to the originating task |

Preserve `/planning?case_id=<uuid>&view=plans|whatif|suppliers|audit`. Omitted view
keeps its legacy Plans behavior. New overview/decision values are allowlisted in
every relevant navigation/load path; invalid values/IDs cannot display a previous
case as the requested result. New overview links explicitly request overview;
do not make old bookmarks create or recalculate anything.

The new Overview is not a duplicate of every full table/chart. Show at most four
relevant summaries, such as proven minimum cost, demand coverage, actual returned
plan count and decision state. Unknown/unavailable values are absent or explicitly
unavailable, never zero or invented global totals. Show a cost/exposure chart in
Plans or contextual detail rather than giving every view an identical chart.

Desktop uses one dominant working area and narrower contextual detail where useful;
original/scenario or alternative comparisons can sit side by side. At tablet and
narrow widths, the primary task precedes details, which stack or open on demand.
Drawer/tab navigation stays labelled; exact tables may scroll within their region.
Do not shrink body text, force page-wide horizontal overflow or cover focus/actions.

Keep Cases/Open RFQs/Practice destinations functional. The procurement overview
offers RFQ and saved-case entries without inventing a global search service,
supplier directory, Settings page, notification system or authenticated avatar.
Existing root/RFQ/Practice routes remain compatible. Metadata classification is not
buyer authorization or an operational-validity claim.

## Task behavior and truthful explanation

### Suppliers and exact Audit

Selecting a supplier is a read-only presentation choice within the loaded saved
case. It changes the contextual path/terms, not procurement allocation or backend
assessment. Render actual saved class, score, tree splits and evidence reference/
sample count. Do not fabricate price/quality features, market competitiveness,
three-level risk bands, high-confidence recommendations or Odoo-trained metrics.
Higher model exposure is more adverse; it is not calibrated failure probability.

Audit keeps exact input/policy, model/solver versions, tree path, provenance and
full saved snapshot. Supplier selection/Audit disclosure perform no Odoo refresh,
training or optimization and need no per-row backend fan-out.

### Plans

No plan is preselected for approval. The minimum-cost reference is labelled as
such, with genuine distinct epsilon alternatives. The contextual allocation uses
the selected saved plan ID/index, exact quantities, delivery terms, cost, premium
and exposure; approximate percentages/scales do not replace exact saved values.

Changing selection writes nothing. Review decision navigates to Decision & PDF
and preserves that exact choice. New case identity clears the prior unfinalized
selection/review; reopening a finalized case restores its recorded choice read-only.
Keep single/no-distinct/incomplete/infeasible/technical outcomes distinct and honest.

### Scenarios

Keep outage, capacity reduction, demand increase, price increase and the existing
bounded combination of demand plus one supplier's capacity/price. Always target
the original base, even when starting from a child. Draft → explicit calculation/
save → child result are distinct. No ephemeral preview or multi-period outage
interval is introduced.

Name the compared reference explicitly: existing original/scenario minimum-cost
plans. Do not imply comparison of a selected alternative or match alternatives
solely by their local index. Original facts remain visible when a child is
infeasible; missing child cost/allocation/exposure is not zero. Changed quantities
do not imply like-for-like savings; scenario prices are assumptions, not Odoo facts.

Return to original loads stored original data; it does not reset/mutate either
saved record. Scenario children offer no finalization or child-approved PDF.

### Decision and approved document

Decision & PDF is the dedicated place for final review and documents. Other tabs
retain a concise selected-plan/next-step context, not duplicate finalization forms.
Approval uses existing exact review/cancel/confirm and actor/reason rules. Decline
all plans explains the existing No-award outcome before its separate confirmation.
Actor audit text is not authenticated identity. A decision cannot be replaced.

Before approval, explain why an approved PDF is unavailable; do not show a working
export button. After approval, show its exact saved terms and document controls
together. Reuse existing page status, previous/next, fit/zoom and byte-identical
download. A PDF failure retains approval, selection, reason and audit; retry only
document access. No-award and children retain their backend ineligibility.

No Request approval queue, Request changes workflow, legal-signature system,
editable approved record or Odoo order creation is introduced.

## Saving, errors and navigation

First deliver [the B08 correction](UX41_RECOVERY_CLARITY_BRIEF.md): Calculate and
save comparison; Comparison saved. Approval is a separate choice. Explain that
an unconfirmed response may follow a successful save. Recovering the same request
retrieves/completes it once; finalization is not needed to complete recovery.

| State | Required feedback/action |
| --- | --- |
| Unsaved draft | Review inputs; explicit calculate/save; dirty navigation offers Stay/Discard |
| Saved, awaiting decision | Already stored and reopenable; choose/compare/scenario independently of approval |
| Pending write | Preserve exact URL/payload/key; no replacement, automatic POST retry or discard escape |
| Pending session lost | Pending recovery details may be lost; an already stored case is not deleted; retain existing support record and no durable-outbox promise |
| Validation rejection | Field-specific errors and focus; retain editable input |
| Backend failure | Name failed operation; retain only correctly labelled prior context and read/retry semantics |
| Decision conflict | Explicit stored-only reopening; no suggestion to create another decision |
| Finalized | Immutable recorded choice/time/reason and correct document eligibility |

Clear stale final-decision/success notices when a new draft/context begins.
Keep current guards across global navigation, case/view changes, Audit and decision
entry; moving a form to another tab must not bypass guards or lose exact intent.
Preserve duplicate-submit protection, purposeful result focus, dialog Escape/cancel
and focus return. Route/state refinements must share the existing validation/reset
seams rather than introduce a parallel pending-request system.

## Architecture and exclusions

Use `frontend/app.py` as composition root and the existing planning state/input/
results/scenario/audit/decision/PDF modules and HTTP clients. Small task-specific
frontend modules are acceptable where needed; broad state/backend refactoring is
not a prerequisite. Business rules remain in existing core/application services;
Odoo mapping stays behind its adapter, solver infrastructure behind its port,
storage and PDF behind their existing adapters. Thin FastAPI routes remain thin.

No schema migration, new endpoint, ERP field or training dataset is authorized
solely to resemble the screenshots. Preserve V1 reads, existing hashes, atomic
classification, immutable snapshots/decisions/PDFs and stored-only replay. Keep
tokens/artifacts server-side. No Odoo UI automation, direct ERP/DB access, writes,
PO creation, observed-source relabelling, HTTP training, multi-product/time-period
MILP, durable outbox, PDF renderer/format replacement or production IAM/cloud work.

## Verification and acceptance

| Gate | Required evidence |
| --- | --- |
| Focused behavior | Changed shared state/route/reset/selection boundaries, old/new links, unknown IDs/views, draft/pending guards and exact field mapping |
| Genuine browser flow | Existing real Reflex/FastAPI/owned disposable PostgreSQL: save → supplier detail → exact plan selection → original/child scenario → review/cancel/confirm → library reopen → PDF/hash; separate No-award |
| Actual faults | Owned API downtime for uncertain creation/scenario/decision and PDF/read failure as relevant; same intent/key, one result, no extra approval; do not use browser interception as proof of server-side downtime |
| Content/ranges | 3/5/10 suppliers; variable distinct-plan counts; single/infeasible/incomplete outcome; long/non-Latin/missing labels; exact money/fractions and source/reference dates |
| Visual/accessibility | Compare composition to supplied references in retained palette; 1440/1280 desktop, 768 tablet, 390/320 narrow, keyboard, actual 200% browser text zoom, focus/dialog return, contrast/non-colour state and reduced motion |
| Query integrity | Retain company/query/cursor and stored-only behavior; reuse unchanged #32 measurements, rerun affected queries only if query/index behavior changes; do not add global count scans |
| Required fast/static | Run AGENTS.md's required Python 3.11 checks once before implementation handoff, with actual CBC/ML; relevant service checks only with documented services |
| Human | Retest changed owner tasks with neutral clear instructions and source/version evidence; 3–5 unfamiliar buyers, ≥80% independent success per essential task, zero unintended finalizations/unresolved critical misunderstandings |

Technical delivery, owner visual approval and novice acceptance are separate.
Do not claim hosted browser execution, whole-app WCAG, screen-reader speech,
physical-device or human timing evidence unless actually obtained. Code review,
static compilation, screenshots and green CI do not replace human task evidence.

Keep O01 B08 attempt 1 and B09's skipped/unclear-instruction report unchanged.
The new tab/task arrangement requires a versioned subsequent protocol; do not edit
the frozen UX41-v1 file. Explain staged faults simply, separately from the task
goal. Record owner/agent/novice role, source hashes, completion/assistance/errors/
time/comprehension; unknown time stays unset. Existing #41 remains the acceptance
record until its defined gate is met; #42 is not closed by this new specification.

## Traceability and delivery

| Capability | Canonical mapping | Retained UX reference |
| --- | --- | --- |
| Overview, navigation and library | FR/AC-V2-09/10; NFR-V2-05/06/07 | UX-AC-01–07, 15; UX29-03/04/10 |
| Saved supplier explanation | FR-V2-02/03/07/09; AC-V2-02/03/07/09 | UX-AC-12; UX29-04/10 |
| Exact plans and choice | FR-V2-06/07/09; AC-V2-05/07/09 | UX-AC-08/09; UX29-04/05 |
| Original-base scenarios | FR/AC-V2-08; NFR-V2-06 | UX-AC-10; UX29-05/07 |
| Save/recovery and final decision | FR/AC-V2-09/10/11; NFR-V2-05/06/07 | UX-AC-11/13; UX29-05/06/08; owner B08 |
| Approved document | FR/AC-V2-12; NFR-V2-06/07 | UX-AC-14; UX29-09 |
| Reassessment | AC-V2-09/13; NFR-V2-04/08 | UX-AC-15/16; owner B08/B09 |

See [proposed vertical tickets/dependencies](CASE_WORKSPACE_TICKET_BREAKDOWN.md).
These are local delivery labels, not new canonical requirement IDs or GitHub issue
numbers. Evidence/handoffs will record problem → decision → behavior → verification
→ limitation → thesis relevance (chapters 3/4/6/7), with the next buyer capability.

Structural direction and palette are confirmed; detailed ticket contracts remain
proposed for publication review. No issue creation/closure/comment, Drive write,
application implementation, commit/push/merge or new runtime test occurred here.
