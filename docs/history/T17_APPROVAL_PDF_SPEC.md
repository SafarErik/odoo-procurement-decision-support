## Problem Statement

Buyers can already create, compare and reopen immutable procurement plans, but the V2 workflow stops before a recorded human final decision. They cannot approve a particular saved allocation, record no-award, or obtain a document proving exactly what they approved. Historical V1 offer finalization does not close this gap for V2 multi-supplier plans.

The official thesis task requires systematic storage, technical human approval and final PDF output. AC-V2-11/12/13 remain open. This increment must complete that buyer workflow without changing saved planning evidence, refreshing Odoo during finalization/download, or presenting synthetic historical demonstrations as current operational evidence.

## Solution

Extend the existing planning workspace so a buyer explicitly approves a proven valid saved plan from an original base case, or records a reasoned no-award. Record the final decision once with caller-supplied actor attribution and a server-recorded UTC time. Exact retries and reopening return the same decision; competing decisions fail without altering it.

Only approved base plans produce an approved procurement document. The backend builds the viewable/downloadable PDF from immutable approved content, including the exact allocation, effective business terms, sources, model/policy references and human decision. Rendering failure leaves approval intact and permits retry from the same content version.

Keep stress scenarios analytical. Permit approval of a retained proven plan when later alternative calculations fail, with an explicit incomplete-comparison warning. Support the existing historical controlled demonstration with prominent simulation and synthetic-evidence labels and a separate current approval record time.

Concrete outcome: after comparing the controlled hybrid base's saved USD 1,850 minimum-cost plan and USD 2,200 lower-exposure alternative, the buyer selects the alternative, supplies a reason and actor reference, and finalizes once. Reload and PDF show that exact saved choice and audit context. A stress scenario cannot be finalized. A separate original base can receive no-award and has no approved PDF. These amounts are existing demonstration references, not new runtime verification or business-savings claims.

## User Stories

1. As a buyer, I want to explicitly select a saved procurement plan, so that approval records my choice rather than an automatic default.
2. As a buyer, I want to approve the saved minimum-cost plan, so that I can finalize its complete multi-supplier allocation.
3. As a buyer, I want to select another proven valid saved plan and record my reason, so that the cost/exposure trade-off is auditable.
4. As a buyer, I want to record no-award with a reason, so that deciding to place no order is distinguishable from an unfinished decision or solver failure.
5. As a buyer, I want to record no-award when no valid plan exists, so that an infeasible or unsuccessful planning case can still receive an explicit human outcome.
6. As a buyer, I want finalization restricted to original base cases, so that simulated commercial terms cannot accidentally become an approved commitment.
7. As a buyer, I want to keep comparing stress scenarios, so that approval does not rewrite the analytical evidence.
8. As a buyer, I want confirmed changed terms to require a new base through the existing creation flow, so that any later approval has its own recorded input context.
9. As a buyer, I want a retained proven plan to remain selectable after a later alternative calculation fails, so that incomplete comparison does not discard a valid saved result.
10. As a buyer, I want an incomplete-comparison warning beside that choice and in its PDF, so that I understand the calculation's limitations.
11. As a buyer, I want unproven, missing or invalid allocations to be rejected, so that only valid saved plans can receive approval.
12. As a buyer, I want to supply an actor reference, so that the decision has explicit human attribution.
13. As an auditor, I want caller attribution distinguished from authenticated identity, so that the PoC token and audit field are not overstated.
14. As a buyer, I want the server to record the decision time, so that it cannot be confused with a backdated simulation date.
15. As a buyer, I want to approve an explicitly labelled historical demonstration, so that I can demonstrate the technical workflow without claiming that its inputs are current.
16. As an auditor, I want simulation dates, approval record time and synthetic ML provenance preserved separately, so that evidence remains interpretable.
17. As a buyer, I want exact retries to return the original outcome and time, so that an uncertain response cannot create a second decision.
18. As a buyer, I want my pending request and finalization key preserved after an uncertain HTTP outcome, so that I can deliberately retry the same intent.
19. As a buyer, I want conflicting payloads or later finalizations rejected, so that a completed decision cannot be silently replaced.
20. As a buyer, I want simultaneous requests handled atomically, so that only one final decision is recorded.
21. As a buyer, I want reopening a case to show its saved human outcome and selected plan, so that I can recover the decision after leaving the workspace.
22. As an auditor, I want original planning and approved content to remain immutable, so that evidence cannot drift after approval.
23. As a buyer, I want to view an approved procurement document, so that I can review the recorded allocation and decision.
24. As a buyer, I want to download the same approved content as PDF, so that I can retain or share a readable decision record.
25. As a buyer, I want the PDF to show exact quantities, prices, cost, currency and relevant terms, so that rounded UI charts do not change the approved commitment.
26. As an auditor, I want plan identity, source, model, policy and approval references in the document, so that I can trace it to the saved evidence.
27. As a buyer, I want clear document denial for unapproved, no-award and scenario cases, so that an analytical or rejected result cannot masquerade as approved.
28. As a buyer, I want PDF errors to leave approval visible and allow rendering retry, so that a presentation failure does not lose my decision.
29. As an operator, I want approval, retrieval, exact retry and PDF to work from stored evidence without upstream/model/solver access, so that reopening a decision does not change its meaning or require those dependencies.
30. As a buyer, I want usable mobile controls and clear unavailable-backend states, so that I can understand whether my decision was recorded.
31. As a thesis author, I want a reproducible complete local flow with measured runtime and explicit limitations, so that I can support the approval/PDF requirements with defensible evidence.
32. As a maintainer, I want historical V1 contracts and records preserved, so that the V2 addition does not invalidate earlier results.

## Implementation Decisions

- Preserve Python 3.11 compatibility, Odoo 19, the side-by-side architecture, ERP-neutral Decision Core, existing FastAPI/PostgreSQL/Reflex roles and Podman + Compose baseline. Keep solver and ML infrastructure behind their current boundaries. Odoo remains bounded, company-scoped and read-only.
- Extend existing V2 application use cases, repository/unit-of-work ports, persistence adapter, thin HTTP contracts/routes and Reflex client/state/Plans/Audit views. Reuse existing finalization, conflict and retry patterns; do not reuse V1's single-offer outcome semantics for V2 allocations.
- Preserve the original immutable planning records and their update/delete protection. Add an immutable linked V2 final-decision record rather than modifying the planning snapshot. Protect decisions against UPDATE/DELETE at the database boundary. Add a uniqueness/locking contract for one final decision per original base case and atomic rollback on failure.
- The finalization command identifies the base case and expected snapshot hash, outcome, selected saved plan index for approval, actor reference, applicable reason, and a separate canonical UUID finalization idempotency key. Index 0 identifies the existing minimum-cost reference; higher indices identify existing distinct alternatives. No independent plan UUID or new ranking algorithm is required.
- Approval requires an explicit selected proven valid saved plan. Alternative selection requires a nonblank reason. No-award requires a nonblank reason and no selected plan; it remains valid when the original base has no available plan. Actor reference must be nonblank and bounded using existing audit conventions. Validate payload shape, types and lengths at the HTTP boundary and business semantics in the application.
- Reject all scenario finalizations. Changed assumptions becoming actual business terms require a new original base through existing supported input creation; no automatic scenario promotion or demand-family decision registry is introduced.
- Validate snapshot version/integrity, plan identity, saved proof and business constraints against recorded effective inputs. Reject unsupported, malformed, missing or inconsistent stored evidence without persisting a decision. Validation is not fresh inference, scoring or optimization. Do not require the overall run to be successful if a proven valid plan survived a later alternative failure.
- Preserve the recorded overall solver outcome. UI and PDF must explicitly warn that comparison is incomplete for a retained-plan approval after later calculation failure; they must not imply that every requested alternative completed.
- The server captures UTC decision time once within successful finalization. Do not accept a caller-selected decision timestamp. Include it in the recorded outcome but not in caller intent; an exact replay returns the original timestamp.
- Serialize finalization per base and enforce finalization-key uniqueness within the V2 finalization namespace. Same key and normalized semantic intent returns the same stored decision; changed intent, cross-case reuse or a competing later finalization returns conflict. Creation keys and finalization keys remain separate. Identical concurrent requests converge on the same decision; conflicting concurrent requests leave one winner and a stable conflict for the loser.
- Reuse existing API conventions: authentication failure is 401, missing case is 404, conflicting finalization/key reuse is 409, invalid or ineligible caller intent is 422, and dependency/rendering unavailability uses a stable service error. Do not leak database, token or renderer internals. All relevant routes retain the trusted-caller guard and existing bounded request handling. Stored integrity errors fail closed, separately from buyer input errors.
- Retrieval exposes the original stored case and its human final decision without mutating either. Preserve existing V2 creation/scenario/retrieval and V1 compatibility. Adding finalization does not turn analytical scenario creation into a new finalization.
- Atomically establish immutable approved content for an approval: original case ID/hash, selected plan/index, effective terms, recorded decision and content schema/version/reference. No-award has no approved document content. Use the own PostgreSQL decision store for approved content and a stable PDF-artifact reference, consistent with ADR-006.
- Generate PDF solely in the backend from that approved content. Include plan identity, product, approved demand Q, unit, supplier identities/labels and allocations, effective prices, costs/currency, relevant capacity/MOQ/quantity/delivery terms, policy/model/source references, recorded solver limitations and approval metadata. Identify the approved result as an original base; any supporting stress comparison remains analytical and cannot replace the approved allocation or terms.
- Preserve exact saved decimal/rational values and clearly labelled display approximations. Do not invent supplier legal names, addresses, tax identifiers or document fields absent from established inputs. The PDF represents an approved procurement plan; automatic ERP PO creation and legally complete external-order data are outside this increment.
- Historical-demo approval must be explicit for the existing controlled fixture/provenance context, not inferred solely from a case's age. Store that context with the decision/document; show prominent demonstration/simulation labels, saved planning dates, separate current decision time and synthetic ML provenance in UI/PDF. Validate evidence against its saved planning context without claiming current operational validity. No general live-operation freshness policy or observed-model promotion is introduced.
- Rendering happens independently after the approval transaction. A rendering failure never changes approved state or content. Retry uses the same content version. Require content equality, not byte equality across render attempts unless a separate renderer contract is later accepted.
- Close one bounded Python 3.11 PDF spike before integrating the renderer: prove required content, long/Unicode text pagination, view/download behavior and dependency compatibility; choose the smallest suitable library and artifact-storage/reference mechanics within the existing stack. Record its question, evidence, decision and any blocker. No new service or speculative abstraction is required.
- Keep the service token on the Reflex server. The frontend calls only the backend API, performs no Odoo/database/model/solver access and generates no PDF locally. Preserve exact pending finalization payload/key on uncertain responses and require explicit retry. A PDF error leaves the saved decision visible; reload restores the saved outcome.
- Deliver three bounded capabilities: saved human decision; approved document; controlled full local demonstration. During implementation, update only affected capability/status, execution instructions and dated evidence. Retain user control of commit/push/merge. This specification publishes the work definition; it does not start implementation.

## Testing Decisions

- Test observable behavior and invariants rather than private helpers, internal SQL sequences or renderer internals. The primary automated seam is the existing backend HTTP API with dependency overrides for controlled repositories/failure injection. Cover finalization, stored retrieval and approved PDF through this boundary instead of creating parallel test-only business interfaces.
- Prior art is the existing V2 controlled planning HTTP suite, stored-only retrieval tests, V1 final-decision API coverage and planning PostgreSQL rollback/idempotency tests. Reuse controlled prepared snapshots and known allocations; do not train or reread Odoo merely to arrange each approval test.
- Exercise valid minimum/alternative approval; mandatory alternative/no-award reasons; no-award with and without plans; blank/bounded actor attribution; invalid index/hash; no-plan/unproven-plan rejection; base-only scope; historical-demo labels/time; retained-plan approval with incomplete-comparison warnings. Rejected operations leave no decision.
- Verify exact retry preserves outcome, selected plan, content identity and original server timestamp. Changed intent, cross-case key reuse and later decisions conflict. Use forbidden-call sentinels to prove finalization, GET, exact retry and PDF make no upstream read, model load/inference, training or solve. Demonstrate stored reopening/PDF with the model unavailable.
- Real disposable PostgreSQL integration is a necessary separate seam for transaction/concurrency guarantees. Test concurrent identical and conflicting finalizations with actual contending connections, key uniqueness, rollback, unchanged planning hash/content, and direct rejection of decision UPDATE/DELETE. Sequential duplicate requests or an in-memory repository do not establish database race safety.
- Compare extracted PDF content with approved content: identity, allocation, demand/unit, money/currency, terms, sources, model/policy, audit and warnings. Inspect rendered pages for Unicode supplier names, long tables/text, pagination and clipping. Test document denial for unapproved/no-award/scenario cases and renderer failure/retry without approval rollback. Content identity is the gate; matching binary bytes is not.
- Use browser/API/PostgreSQL milestone acceptance for explicit selection, alternative/no-award reasons, approved/no-award reload, uncertain-response exact retry, PDF view/download/failure, unavailable backend and mobile accessibility. Compilation alone cannot prove these user interactions.
- AC-V2-11 acceptance: one original base receives one valid explicit approval or reasoned no-award; its audit survives reload/retry, conflicts/races are safe, and original snapshots remain immutable.
- AC-V2-12 acceptance: a viewable/downloadable PDF matches the approved immutable content; unapproved/no-award/scenario document requests are denied, and download performs no source/model/solver work.
- AC-V2-13 acceptance: reproduce the controlled read-only Odoo plus source-attributed supplemental input -> saved Decision Tree evaluation -> MILP alternatives -> stress analysis -> original-base human approval -> stored retrieval/PDF flow under local Podman + Compose. Include a separate no-award flow; document prerequisites, runtime, dataset scope, provenance and limits. This first full demonstration does not replace T18's integrated evaluation.
- Run focused checks during implementation, then the required Python 3.11 fast gates once before handoff, including actual CBC/ML runtime dependencies. Use the existing Podman machine; never reset an application or Odoo database for tests. Record executed, skipped and blocked service/browser gates separately, and verify hosted CI only for the exact user-published SHA.

## Out of Scope

Automatic Odoo PO creation/write-back or Odoo GUI automation; arbitrary quotation discovery; observed-history/model promotion; new training or optimization during finalization/retrieval/PDF; finalizing stress children; automatic scenario promotion; multi-product optimization; manual allocation editing; decision revision/revocation or multi-stage/legal approval; electronic signatures; production IAM/RBAC; no-award/rejection PDFs; supplier legal-data enrichment; general operational freshness policy; new infrastructure/cloud deployment; T18's final measured evaluation and T19 thesis closure.

Any later manual allocation change needs a separately validated new plan and approval. This increment never mutates the saved approved allocation. No Drive document edit, commit, push or merge is authorized by publishing this specification.

## Further Notes

This specification synthesizes the user-confirmed planning session on 2026-10-09. Q1 accepted base-only finalization; Q2 accepted retained proven plans with incomplete-comparison warnings; Q3 accepted explicitly labelled historical-demo approval with current server-recorded decision time. The user confirmed the plan by requesting progression to to-spec. It adds no new requirement namespace or accepted ADR.

Traceability remains FR-V2-10/11/12, affected frontend completion FR-V2-09, AC-V2-10 regression and AC-V2-11/12/13 acceptance, with relevant NFR-V2-02/04/05/06/07/08 and architectural modularity NFR-V2-01. AC-V2-10's existing controlled PASS is preserved; AC-V2-11/12/13 remain OPEN until their defined evidence exists. Preserve ADR-006/007/013/022/023/026/027 and all other accepted records.

Authoritative sources:
- [Official thesis task, reference 423.589/25/140, dated 2026-09-22](https://drive.google.com/file/d/1T4Fo_RsSFgs-zjV5NUPfF6_h7xOraog8/view): storage, technical human approval, final PDF and reproducible full-flow testing obligations.
- [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit): existing FR/NFR/AC definitions.
- [03_ARCHITECTURE_DECISIONS](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit): canonical accepted ADR register.
- [02_ROADMAP](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit): T17 approval/PDF/full demonstration, followed by separate T18 evaluation.
- [Published T16 implementation, PR #18](https://github.com/SafarErik/odoo-procurement-decision-support/pull/18): prior planning-workspace capability, not V2 approval/PDF evidence.
- [T16 implementation evidence at its merged revision](https://github.com/SafarErik/odoo-procurement-decision-support/blob/979b9b89e8517c65daefcf7e533c8b3f9c2c0ccd/docs/T16_HANDOFF.md): prior controlled runtime/browser evidence and limitations.

Drive requirements/ADRs/status/roadmap were refreshed for this synthesis. Some Drive publication wording still predates T16's merge; preserve that historical wording and keep correction as a separate explicitly requested Hungarian Drive stage. Repository engineering artifacts and this issue remain English.

Thesis evidence must record problem -> decision -> implemented behavior -> evidence -> limitation -> chapter relevance. At present this is planned behavior, not implementation or PASS evidence. Relevant chapters: 3 requirements, 4 lifecycle/architecture, 5 invariants, 6 implementation, 7 tests/content integrity/runtime/limitations, and 8/9 conclusions and further work. Synthetic exposure is not calibrated failure probability; controlled historical quotations are not a current operational forecast.

The renderer/storage spike is an implementation decision within these constraints, not a request to reopen buyer policy or the accepted baseline. Publish as one ready-for-agent specification; the delivery slices explain execution order without creating a competing Drive roadmap.

