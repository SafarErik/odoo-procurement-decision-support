# T17 published ticket breakdown

Status: APPROVED AND PUBLISHED - user approved granularity and blocking edges on 2026-10-09.
Issue bodies, open states, labels and text links were read back and verified. No implementation has started.

Parent: [#19 — V2 human approval/no-award and approved-snapshot PDF](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19), ready-for-agent. Its body, state and labels were unchanged by ticket publication.

## Implementation order

1. [#20 — Finalize a saved base plan or record no-award in the planning workspace](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20) — Blocked by: none.
2. [#21 — View and download the approved snapshot PDF from the planning workspace](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21) — Blocked by: #20.
3. [#22 — Reproduce the complete controlled procurement-to-approved-PDF flow locally](https://github.com/SafarErik/odoo-procurement-decision-support/issues/22) — Blocked by: #21.

Dependency graph: #20 -> #21 -> #22. Start with #20 after implementation authorization.
No prefactoring is justified by the inspected implementation. Reuse current seams without broad restructuring.

The available GitHub connector has no native sub-issue/dependency operation. These are linked implementation issues using explicit Part of #19 and Blocked by references, not native GitHub relationship objects. The to-tickets skill prohibits parent modification, so no parent task-list edit or closure was made.

Each issue is labelled ready-for-agent. A blocked issue is not startable until its blocker is complete; readiness does not grant implementation, Git publication, Odoo writes or Drive edits.

## Published issue bodies

### Ticket 1: #20 — Finalize a saved base plan or record no-award in the planning workspace

## Parent

Part of [#19 — V2 human approval/no-award and approved-snapshot PDF](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19).

## What to build

Let a buyer explicitly select a proven valid saved original-base plan, provide actor attribution and any required reason, and finalize once through Reflex -> backend -> PostgreSQL. Alternatively, record a reasoned no-award, including when no valid plan exists. Reopening and exact retry show the same saved human outcome and time.

This is a complete human-decision capability, including the immutable approved content that the next ticket will render. It includes the necessary persistence/API/UI integration and integrity checks; it does not generate PDF yet.

## Acceptance criteria

- [ ] The buyer explicitly chooses a saved minimum-cost plan or valid alternative; nothing is approved through default selection. Alternative approval requires a nonblank reason. No-award requires a nonblank reason and no selected plan, including for a base with no available plan.
- [ ] Finalization is restricted to original base cases. All stress children are rejected by the backend and have no actionable finalization control. Their analytical use and existing creation/retrieval behavior remain available.
- [ ] The command validates case/snapshot hash and saved plan index, snapshot contracts/integrity, saved proof and business constraints. Invalid/unproven/no-plan approval and malformed persisted evidence fail closed without a decision.
- [ ] A retained proven plan remains approvable after a later alternative calculation fails; UI and stored approved content preserve the solver outcome and explicitly record incomplete comparison.
- [ ] Actor attribution is nonblank/bounded audit text; UI does not present it or the PoC shared secret as authenticated buyer identity. Boundary validation and stable existing authentication/error conventions are preserved.
- [ ] The server records UTC decision time once. Explicit historical-demo context preserves saved simulation/planning dates and synthetic provenance separately, with visible demonstration labels; arbitrary case age is not a demo classifier.
- [ ] A separate linked immutable final-decision record leaves the original planning row/hash unchanged. Approval atomically establishes versioned approved content identifying the exact case/hash/index, terms and human audit. No-award establishes no approved document content.
- [ ] Same finalization key and semantic intent returns the original decision/content identity/timestamp. Changed intent, cross-case key reuse or competing later finalization conflicts. Creation and finalization keys are separate.
- [ ] Real disposable PostgreSQL tests use genuinely contending transactions for identical/conflicting finalization; only one decision exists, rollback leaves no partial decision, and direct final-decision UPDATE/DELETE and original-snapshot mutation are rejected.
- [ ] Reflex preserves the exact pending payload/key after an uncertain response and requires explicit retry. Reload displays the recorded selected plan/outcome and audit; backend unavailability cannot falsely show a successful decision.
- [ ] HTTP tests cover the above external behavior, and sentinels prove approval, stored GET and exact retry perform no Odoo read, model load/inference, training, scoring or solve. Stored reopening works with the model unavailable.
- [ ] Browser/API/PostgreSQL acceptance demonstrates minimum/alternative approval, no-award, reload, uncertain-response recovery, errors and mobile usability; compilation is recorded separately.
- [ ] Preserve V1 contracts/records and existing V2 create/scenario/retrieval behavior. Run focused checks and the required Python 3.11 fast gates before handoff; record executed/skipped/blocked runtime gates without converting them to PASS.
- [ ] Update only affected capability status, run instructions and dated thesis evidence: problem -> decision -> implemented behavior -> evidence -> limitation -> chapter relevance.

Traceability: FR-V2-09/10/11; AC-V2-10 regression and AC-V2-11; relevant NFR-V2-01/02/04/05/06/07/08. Completion supplies the human-decision evidence; it does not close AC-V2-12/13.

All constraints and exclusions in [the parent specification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19) apply. Preserve the official task, existing FR/AC identifiers and accepted ADRs, including ADR-006/007/013/022/023/026/027. Python 3.11, Odoo 19, the current stack and read-only/API-only boundaries remain fixed. Keep synthetic/historical provenance explicit. No Drive edits, Odoo writes, commit/push/merge or unrelated infrastructure are authorized by this ticket.

## Blocked by

None (can start immediately after implementation is authorized).

### Ticket 2: #21 — View and download the approved snapshot PDF from the planning workspace

## Parent

Part of [#19 — V2 human approval/no-award and approved-snapshot PDF](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19).

## What to build

For an approved original base, let the buyer view/download a backend PDF containing the immutable approved allocation and decision. A rendering failure leaves approval visible, and explicit retry renders the same content version. This extends the existing saved human-decision path through document storage/reference, backend delivery, Reflex and verification.

Keep the bounded renderer/storage spike inside this ticket: choose and verify the smallest Python 3.11-compatible solution within the current stack before integrating it.

## Acceptance criteria

- [ ] Close the PDF spike with its question, evidence, dependency choice, artifact-reference/storage mechanics and any blocker; prove Python 3.11 compatibility, required content, long/Unicode text pagination and view/download behavior without introducing a service.
- [ ] The backend renders solely from the immutable approved content established during finalization. Persist a stable content-version/PDF-artifact reference consistent with ADR-006; never mutate the original planning or final-decision content.
- [ ] PDF content includes case/hash/plan identity, product/Q/unit, supplier identities/labels and allocations, exact prices/cost/currency, relevant capacity/MOQ/quantity/delivery terms, source/model/policy references and human approval metadata.
- [ ] Preserve saved decimal/rational values; any display approximations are labelled. Identify the approved result as the original base and distinguish supporting analytical comparisons from approved terms. Do not invent supplier legal/tax/address fields.
- [ ] UI/PDF prominently show controlled-demo/simulation context, saved planning dates, separate server-recorded decision time, synthetic ML provenance and any incomplete-comparison warning. Do not imply current operational validity or calibrated failure probability.
- [ ] Unapproved, no-award and scenario cases are denied approved procurement PDFs by the backend; the UI reflects that eligibility.
- [ ] Rendering/download failure leaves the recorded approval and content unchanged. Retry uses the same content version; content equality is required, binary byte equality is not.
- [ ] Authenticated backend PDF delivery supports browser viewing and downloading while keeping the service token on the Reflex server. No frontend PDF generation, Odoo/database access or browser token exposure.
- [ ] HTTP tests compare extracted PDF content to approved content and exercise denial, stable rendering errors and retry. Forbidden-call sentinels prove document operations need no Odoo, model load/inference, training, scoring or solve.
- [ ] Rendered-page inspection covers long supplier names, Unicode, multi-page content and clipping; actual browser/API/PostgreSQL acceptance covers view/download, rendering failure/recovery and mobile access.
- [ ] Existing decision/retry/no-award and V1/V2 regression behavior remains intact. Run focused checks and required fast gates; record compilation, browser and runtime evidence separately.
- [ ] Update only affected status, execution instructions and dated thesis evidence, with links to exact content-identity/rendering evidence and stated limitations.

Traceability: FR-V2-09/10/12; AC-V2-10/11 regression and AC-V2-12; relevant NFR-V2-01/02/04/05/06/07/08. This ticket does not by itself claim AC-V2-13 or full V2 acceptance.

All constraints and exclusions in [the parent specification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19) apply. Preserve the official task, existing FR/AC identifiers and accepted ADRs, including ADR-006/007/013/022/023/026/027. Python 3.11, Odoo 19, the current stack and read-only/API-only boundaries remain fixed. Keep synthetic/historical provenance explicit. No Drive edits, Odoo writes, commit/push/merge or unrelated infrastructure are authorized by this ticket.

## Blocked by

- [#20 — Finalize a saved base plan or record no-award in the planning workspace](https://github.com/SafarErik/odoo-procurement-decision-support/issues/20)

### Ticket 3: #22 — Reproduce the complete controlled procurement-to-approved-PDF flow locally

## Parent

Part of [#19 — V2 human approval/no-award and approved-snapshot PDF](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19).

## What to build

Provide a repeatable local demonstration through the real Reflex -> backend -> read-only Odoo/saved model -> MILP -> PostgreSQL path, stress analysis, explicit original-base human decision, stored reload and approved PDF. A separate case demonstrates no-award. Make the complete capability reproducible from documented prerequisites, with measured runtime and thesis-useful evidence.

Use the existing controlled hybrid fixture and known model/input preparation. Make only bounded integration corrections needed for this complete flow; this is not a catch-all hardening or final evaluation ticket.

## Acceptance criteria

- [ ] Document prerequisite configuration, offline fixture/model preparation, service startup, commands, expected buyer outcomes and cleanup using the existing Podman machine and stack. No database-reset test targets application/Odoo data.
- [ ] Fresh controlled creation independently reads the supported Odoo comparison and attributed supplemental terms, then records the separately synthetic saved tree assessment and MILP result in PostgreSQL. No browser-selected model or training in HTTP/Reflex is introduced.
- [ ] The buyer compares base plans and exercises the supported five stress types, including an infeasible result, before explicitly finalizing the original base. Stress children stay analytical and cannot be finalized.
- [ ] The buyer approves a valid saved alternative with a reason, reopens it and views/downloads matching approved content. A separate original base records reasoned no-award and cannot receive an approved PDF.
- [ ] Stored retrieval, exact decision retry and PDF continue without upstream/model/solver access, including model-unavailable reopening. Demonstrate renderer/backend failure recovery without altering recorded decisions.
- [ ] Record actual browser/API/PostgreSQL results, reproducible input/model/policy/solver references, runtime and dataset bounds. Keep Odoo facts, supplemental inputs, historical simulation context and synthetic ML evidence distinct.
- [ ] Required fast/service checks and relevant negative/regression gates are executed or explicitly recorded as skipped/blocked; hosted CI is tied only to the exact user-published SHA. All implementation slices remain independently verifiable.
- [ ] Provide a dated acceptance handoff with problem -> decision -> implemented behavior -> evidence -> limitation -> chapter relevance. State whether the defined controlled AC-V2-13 gate is met without claiming observed-model promotion, operational forecast validity, final T18 evaluation or complete thesis acceptance.

Traceability: AC-V2-13; FR-V2-01/02/03/04/05/06/07/08/09/10/11/12 across the controlled chain; AC-V2-11/12 regression and relevant NFR-V2-02/04/05/06/08. Preserve prior controlled PASS evidence and leave unrelated acceptance scopes open.

All constraints and exclusions in [the parent specification](https://github.com/SafarErik/odoo-procurement-decision-support/issues/19) apply. Preserve the official task, existing FR/AC identifiers and accepted ADRs, including ADR-006/007/013/022/023/026/027. Python 3.11, Odoo 19, the current stack and read-only/API-only boundaries remain fixed. Keep synthetic/historical provenance explicit. No Drive edits, Odoo writes, commit/push/merge or unrelated infrastructure are authorized by this ticket.

## Blocked by

- [#21 — View and download the approved snapshot PDF from the planning workspace](https://github.com/SafarErik/odoo-procurement-decision-support/issues/21)

