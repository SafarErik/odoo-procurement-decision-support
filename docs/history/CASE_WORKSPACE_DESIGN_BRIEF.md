# Case workspace and procurement overview — reference-led design brief

Date: 2026-10-14. Status: structure and palette confirmed by owner for the next
specification; detailed behavior/delivery proposal remains planning. No UI
implementation or new GitHub publication. Current repository baseline:
`dc2cf575f8abf1bd9c29e1b549fad72b1a822388`.

## Job, audience and outcome

A procurement buyer opens one product/demand case, understands its supplier
assessment and allocation choices, tests a disruption, and makes a deliberate
decision. This is an Operate surface: clear tasks and trustworthy data lead.
The primary workspace is one selected case. A separate lightweight overview is
the entry to open RFQs/quotations and previously saved cases.

Success means finding the relevant case, explaining its quantities and premium,
distinguishing a saved comparison from a final decision, and locating the next
action without developer instructions. Retain [#41's failed and unassessed human
evidence](UX41_ASSESSMENT.md); this brief is not a usability pass.

## Visual authority and selected direction

The owner supplied eight visual references and explicitly confirmed keeping the
existing green/mint/purple palette. Adopt their horizontal composition, compact
case summary, aligned data, clear tab navigation and contextual detail panels.
The reference screenshots are inspiration, not numerical evidence, new backend
requirements, an approved brand name or a pixel-perfect implementation target.

- Deep-green navigation, light mint background, white data surfaces and purple
  primary action/selection continue the existing Decision editorial identity.
- Use one compact case-context band above the task. Give cost and quantities
  visual prominence; show technical identity, hashes and fractions on demand.
- At desktop widths, use a broad working area plus a narrower contextual panel.
  Related comparisons can sit side by side. Avoid putting every chart, table,
  explanation and action on Overview.
- Use restrained borders, readable typography, consistent spacing and aligned
  figures. Status is explicit text plus a semantic indicator, not colour alone.
- Keep Procurement workspace branding. New logos, blue styling, fictional buyer
  avatars, notifications and empty Settings controls are not part of this brief.

## Reference interpretation

| Attachment | Reference surface | What to reuse |
| --- | --- | --- |
| 1 — `02_35_56 PM-2.png` | Saved cases | Recognizable rows, concise filters, status and direct open/document action |
| 2 — `02_35_54 PM-1.png` | Supplier directory | List and selected-supplier detail panel; broader directory needs separate data support |
| 3 — `02_29_13 PM-6.png` | Decision and PDF | Selected terms next to decision state; document alongside its saved summary after approval |
| 4 — `02_29_12 PM-5.png` | Scenarios | Clear scenario choice, parameters and original/scenario comparison |
| 5 — `02_29_11 PM-4.png` | RFQ overview | Open quotations and saved cases as distinct entry tabs |
| 6 — `02_29_10 PM-3.png` | Supplier assessment | Case supplier table beside the selected supplier's actual tree-path explanation |
| 7 — `02_29_09 PM-2.png` | Plans | Allocation detail beside exact alternative comparison; constraints available contextually |
| 8 — `02_29_08 PM-1.png` | Case Overview | Compact product/demand context and a small number of useful summaries |

All full filenames, original local paths and SHA-256 identities are recorded in
ignored `.artifacts/case-workspace-reference-20261014/references.json`. Originals
are unchanged; reference PNGs are not added to the repository in this step.

## Information architecture and interaction

### Procurement overview

Offer Open RFQs & quotations and Saved cases as lightweight entry views. Keep
Practice clearly separate and accessible. A saved row leads with product, demand,
required date, source/workspace and decision status. The full UUID remains copyable
in details; do not invent a persistent `PC-2024-001` alias or use a shortened UUID
as the sole identifier.

Reuse current library paging, workspace/status and product/case-ID search. Do not
present supplier-wide search, global totals, arbitrary sort orders, scenario-count
filters or Last updated semantics until their API support is established. Show
bounded page results honestly. Approved rows can lead directly to the existing
document view; undecided and No-award rows cannot export an approved PDF.

The current RFQ ledger and fixed prepared comparison remain useful. General
RFQ/quotation selection and conversion to a comparison require a separately scoped,
validated adapter/application/API increment. Confirmed purchase orders and receipts
are supporting historical context, not the primary new-comparison entry.

### Selected case workspace

Proposed primary tabs: Overview, Suppliers, Plans, Scenarios, Decision & PDF.
Keep exact Audit reachable through a labelled secondary entry from each tab.
Preserve existing Plans/What-if/Suppliers/Audit bookmarks and retrieval semantics
when the implementation maps them into the new arrangement.

| View | Main working area | Contextual detail |
| --- | --- | --- |
| Overview | Product, demand, due date, source, saved state and a concise result/next-step summary | Current selection/decision and links to inspect plans or a disruption |
| Suppliers | Saved classes, actual quoted prices and applicable business terms | Actual saved tree path, history sample/reference time and applicability for one selected supplier |
| Plans | Exact minimum-cost and alternative comparison | Selected allocation, quantities, premium and delivery/constraint detail |
| Scenarios | Supported scenario choice and parameters, followed by original/scenario results | Saved assumptions, meaningful differences and explicit Return to original |
| Decision & PDF | Selected saved plan, actor audit text and reason; deliberate review/confirmation | Saved final decision; approved summary and PDF navigation/download when eligible |
| Audit | Exact inputs, versions, solver/model evidence, provenance and source identities | Contextual explanation of the field or artifact being inspected |

Overview should not repeat every full supplier table and plan table. Default
summaries may show proven minimum cost, demand coverage, returned plan count and
decision status. No selected-plan summary exists until the buyer selects one;
displaying a minimum-cost reference must not implicitly select or approve it.

Keep terminology human and specific: Plans instead of Optimization as a primary
task label; Review decision for the next action; Decline all plans with a clear
No-award explanation before confirmation. Exact API/status names remain unchanged.
Avoid replacing a factual class or score with an invented business recommendation.

## State clarity is part of the design

Apply the [save/recovery correction brief](UX41_RECOVERY_CLARITY_BRIEF.md) before
treating this composition as ready for buyer acceptance.

| State | Visible meaning and next action |
| --- | --- |
| Unsaved draft | Review inputs; Calculate and save comparison explicitly writes the case |
| Saved comparison, no decision | Comparison saved. Approval is a separate choice. Compare/select or test a scenario |
| Unconfirmed save response | The comparison may already be saved; recover the same request/key. Approval is not a recovery step |
| Scenario result | Saved simulation against the original base; Return to original does not mutate either result |
| Infeasible scenario | No plan satisfies these saved constraints; preserve the original result and explain missing scenario values |
| Approved | Immutable selected terms, decision time and reason; view/download this approved document |
| No-award | No plan was approved; immutable decision and reason, with no approved-plan PDF |
| PDF unavailable | Approval and saved terms remain visible; retry document access only |
| Backend or case-open failure | Name the failed operation; do not show another case as the requested result |

Separate simulation reference/captured data dates, comparison save time and final
decision time. Human-readable dates can lead; exact UTC/provenance remains in Audit.
Clear stale success messages on a new draft. Preserve exact pending intent through
navigation and explicit retry; explain session-loss limits without promising a
durable outbox. Never suggest rollback or another approval to finish a saved case.

## Product truth adaptations

The screenshots contain illustrative claims and some internally inconsistent
values. For example, a reference counts three suppliers while only two have a
nonzero allocation. The implementation must derive presentation from saved results.

| Reference element | Required adaptation |
| --- | --- |
| Higher decision score means better; Low/Medium/High risk | Current model exposure is lower-is-better, synthetic and uncalibrated. Show the actual saved class/score; introduce no invented categories or confidence thresholds |
| Tree explanation based on price, quality and risk incidents | Show only the actual saved path and supported historical features; no explanatory fiction |
| Training on three years of Odoo history; live model metrics/trends | Current fitted model uses synthetic history. Observed-history training/promotion is a separate audited offline pipeline; evaluation metrics belong in model/Audit detail |
| Savings versus a single supplier or market average | Show verified saved-plan cost/premium comparisons. A single-supplier point may violate concentration limits; do not invent a feasible baseline or market benchmark |
| Recommended balanced plan automatically selected | The backend offers minimum cost and distinct epsilon alternatives. Buyer selection is explicit; no unsupported automatic best-plan claim |
| Scenario options described as cost/risk plan alternatives | Separate alternative allocations from disruptions. Preserve all five supported disruption types, including the bounded combined change |
| Outage period across months | The current solver is not a multi-period model. Use the supported availability/date/business-term contract, not an invented interval control |
| Export PDF before approval; Request approval/changes | Current finalization is one deliberate, immutable decision. Export only when approved; do not imply a separate reviewer queue, authenticated buyer identity or reversible approved record |
| Odoo Connected / last synced / live history everywhere | Status must come from an actual bounded read/check. A saved case is captured data; reopening does not refresh Odoo or prove connectivity |
| Global supplier directory, historic KPIs, product pictures | Validate additional adapter/API fields and scope first; omit unavailable fields and ornamental product photos rather than fabricating data |

Scenario comparisons must identify the plan being compared. Existing minimum-cost
original/scenario comparison is not a comparison of the previously selected
alternative. Alternative numbers are local to each saved case; equal numbers do
not identify the same allocation. Changed-demand totals are not like-for-like
savings, simulated prices are not fresh Odoo quotations, and absent values are not zero.

## Layout, accessibility and realistic ranges

Desktop is horizontal where it helps the task, not a collection of equally weighted
cards. At tablet/narrow widths, place the primary task before contextual detail;
panels stack or open on demand. Use labelled case tabs and drawer navigation. Keep
an exact comparison table accessible with scoped scrolling where needed; never
force horizontal overflow on the whole page or shrink body text to fit.

Verify three, five and ten suppliers, variable distinct-plan counts, a single-plan
case, infeasibility, missing/long/non-Latin labels, exact money/fractions and empty
or unavailable histories. Preserve keyboard focus/order, dialog cancel/return,
visible selected state, error/status feedback, reduced motion, contrast and 200%
browser text zoom. Screen-reader speech and physical-phone evidence remain their
own gates; a screenshot is not whole-app accessibility conformance.

## Delivery sequence and boundaries

1. Correct save/recovery/approval wording and state feedback; retain B08 attempt 1
   and retest on a fresh case with neutral task instructions. Clarify B09's test
   instructions without rewriting its skipped outcome.
2. Build the selected-case layout and task navigation over existing saved APIs.
   Keep one concrete vertical flow working: open saved case, inspect supplier,
   compare/select plan, test disruption, review decision, reopen approved document.
3. Align the lightweight saved-case/RFQ overview with the same visual system.
4. Scope general quotation selection and supporting supplier/history data through
   validated read-only adapter/API increments. Treat observed-model promotion as
   a separate offline evidence/model gate.
5. Reassess with owner and 3–5 unfamiliar buyers under the approved completion/
   mistake rules. Carry #41/#42's open acceptance work forward explicitly.

This sequence is a planning proposal, not newly published tickets or a silently
expanded #42 contract. UI layout and Odoo data integration can be planned together
but have different prerequisites. Preserve Python/Reflex, thin HTTP routes,
application orchestration, ERP-neutral core, solver/ML/storage/PDF adapters,
read-only Odoo, immutable original/child results and V1 compatibility. No frontend
DB/ERP calls, Odoo PO creation, automatic training, PDF renderer replacement,
production identity system or commit/push/merge is introduced.

## Traceability and remaining decisions

This refines FR-V2-07/09 and AC-V2-09; stored discovery and lifecycle touch
FR/AC-V2-10/11/12, disruptions FR/AC-V2-08, and integration dependencies
FR/AC-V2-01/02/03. NFR-V2-01/04/05/06/07/08 and existing UX-AC-01–16 remain
applicable. Canonical Drive requirements/ADRs are unchanged. Thesis relevance:
chapters 3 (buyer problem), 4 (boundaries), 6 (implementation), 7 (evaluation).

The owner explicitly confirmed the five primary tabs, secondary Audit and
RFQ/Saved cases overview for the next specification. Palette and case-first intent
are confirmed. The [implementation specification](CASE_WORKSPACE_INCREMENT_SPEC.md)
and [proposed tickets](CASE_WORKSPACE_TICKET_BREAKDOWN.md) define behavior and
delivery for review; their preparation is not GitHub publication or implementation.
Reference images do not establish a working UI, new Odoo fields or human acceptance.
No application tests or UI build were run for this planning artifact.
