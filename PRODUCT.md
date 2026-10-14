# Product

<!-- impeccable:product-schema 1 -->

Confirmed product context, 2026-10-12. This is a design aid, not a replacement
for [the accepted project baseline](docs/agents/project-baseline.md), canonical
Drive requirements/ADRs or [current technical evidence](docs/T18_CONTROLLED_ASSESSMENT.md).

## Platform

web

## Users

A procurement buyer who understands purchasing but is using this app for the
first time. Thesis demonstration is a secondary use of the same honest workflow.
The workspace is English and desktop-first, with usable mobile layouts.

## Product Purpose

Help a buyer compare supplier allocations for one product and one approved
integer demand, understand cost/exposure trade-offs, test disruptions and make
a deliberate human decision with a saved approved PDF.

## Positioning

A Python side-by-side procurement helper that combines validated read-only Odoo
quotations, explicitly sourced business terms, saved Decision Tree supplier
assessments and MILP allocations with immutable retrieval and human approval.
It complements Odoo; it does not place orders or autonomously procure.

## Operating Context

Buyers review input, compare Plans, test What-if scenarios, inspect Suppliers and
Audit, approve a specific original-base plan or record No-award, then reopen work
and its document. FastAPI and separate application PostgreSQL sit behind an
API-only Reflex frontend. Python 3.11 and local Podman/Compose remain the baseline.

## Capabilities and Constraints

- Current creation uses controlled synthetic inputs or a fixed prepared Odoo
  quotation comparison. Arbitrary quotation discovery is a separate capability.
- Training is offline. Current Decision Tree evidence is synthetic even in the
  Odoo quotation flow; exposure is not calibrated failure probability.
- Saved GET/exact replay never rereads Odoo, trains, scores or solves. Scenarios
  target the immutable original base; their simulated inputs are not fresh facts.
- Decisions are immutable and explicit. Alternative selection and No-award retain
  required reasons. Actor attribution is not authenticated user identity.
- Approved PDFs come from the backend's immutable approved content. A document
  failure preserves approval; no PDF exists for No-award or scenario children.
- Tokens remain server-side. No direct frontend Odoo/database access, frontend
  business logic, ERP write-back or production identity/deployment expansion.
- On 2026-10-12 the user confirmed a curated **Practice** workspace without database
  resets and a bounded saved-case library with recognizable labels and grouped
  scenarios. These are planned additions, not current capabilities. Practice is
  explicit synthetic training/example use, not a claim of isolated storage.
- Keep exact pending payload/key and explicit retry after uncertain outcomes.
  Context changes cannot discard this intent. Preserve historical snapshots.

## Evidence on Hand

[README](README.md) records current capability;
[T18's assessment](docs/T18_CONTROLLED_ASSESSMENT.md) records controlled technical
evidence and limits; [the buyer assessment](docs/T18_29_BUYER_ASSESSMENT.md) records
entry/hierarchy/approval/focus/recovery/document findings. Offline demo inputs and
the fixed Odoo comparison are available. Owner and unfamiliar-participant usability
remain pending; browser text zoom, screen-reader speech and physical-phone evidence
must not be invented. No operational ML validity or production-readiness claim.

## Product Principles

- Lead with the buyer's quantities, cost and next task; retain exact audit evidence.
- Make source, case lineage and human authority understandable at the point of use.
- Keep Practice distinct and honest about persistence and synthetic evidence.
- Make finding, comparing, recovering and reopening work possible without a runbook.
- Judge polish by task comprehension, accessibility and safe completion as well as
  visual coherence; retain unassessed usability limits until evidence exists.

## Confirmed Design Reference

On 2026-10-12 the user selected **Decision editorial** in the local design review
and confirmed it in chat. The code-led desktop planning sketch uses a deep-green
rail, soft mint ground, purple selection, aligned plan comparison and persistent
review strip. Preserve this chosen direction when specifying the new workspace;
see [the confirmed planning brief](docs/UX_UI_INCREMENT_PLAN.md#final-design-brief--confirmed)
and [implementation specification](docs/UX_UI_INCREMENT_SPEC.md). The user confirmed
the full brief and authorized specification work on the same date. The chosen
static reference is preserved in [the repository](docs/design/decision-editorial.html).
This records user intent, not a finished design system or responsive implementation.

## Owner-confirmed workspace direction — 2026-10-14

The primary dashboard focuses on one selected procurement case: supplier evaluation,
MILP alternatives, scenario analysis, explanations and human approval. A separate
lightweight overview provides open RFQ/supplier quotation discovery and saved-case
entry. Confirmed POs and receipts are supporting historical context, not the primary
start. Keep the interface spacious, with tabs, progressive disclosure and contextual
panels rather than every chart/table/control visible at once. Related information
can sit side by side on desktop with narrow-screen reflow.

This is the owner-confirmed direction from the #41 pilot, not a claim that buyer
quotation discovery or observed-history training is implemented. Preserve read-only
Odoo, API-only frontend, explicit terms, offline training and immutable retrieval/
approval boundaries. [Brief and evidence](docs/UX41_ASSESSMENT.md#confirmed-case-workspace-direction--2026-10-14).

## Critical save/recovery/approval clarification — 2026-10-14

Owner B08 treated approval as necessary for recovery. Make durable comparison
saving distinct from optional later finalization; uncertainty means the response
could not confirm the save, not that approval/database rollback is needed. Pending
recovery is session-bound while already saved cases remain in backend storage.
The [correction brief](docs/UX41_RECOVERY_CLARITY_BRIEF.md) is proposed, not
implemented/retested; the first-attempt failure must remain in the evidence.

## Reference-led case workspace brief — 2026-10-14

The owner supplied eight dashboard references and explicitly confirmed retaining
the current green/mint/purple palette. Use their horizontal task layout, compact
case summary, tabs and contextual detail panels to develop the selected-case
workspace and separate procurement overview. The references' branding, numerical
claims, statuses and unsupported features are illustrative, not product facts.

The [design brief](docs/CASE_WORKSPACE_DESIGN_BRIEF.md) maps the references to current
capabilities, safe state wording and separate Odoo/history dependencies. The owner
confirmed Overview, Suppliers, Plans, Scenarios and Decision & PDF as primary views,
secondary exact Audit, and the lightweight RFQ/Saved cases overview for the next
specification. The [specification](docs/CASE_WORKSPACE_INCREMENT_SPEC.md) and
[ticket breakdown](docs/CASE_WORKSPACE_TICKET_BREAKDOWN.md) are local planning
artifacts; this is not implemented UI, a published increment or completed #41/#42
acceptance.
