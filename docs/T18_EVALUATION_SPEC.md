# Integrated procurement evaluation and buyer usability — T18 specification

Status: **PUBLISHED — [specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25), `ready-for-agent`; [#26](T18_26_HANDOFF.md) and [#27](T18_27_HANDOFF.md) have local results; #27's T7-S/T8 credential gate passed after user key renewal, with the initial failures retained. Overall T18 remains in progress.**
Prepared 2026-10-11 from the user-confirmed T18 plan. This specifies work,
not measured results or complete V2/thesis acceptance.

Approved [delivery tickets #26–#30](T18_TICKET_BREAKDOWN.md) are published;
#26 is committed at `97afe03`; the user authorized #27, whose measured results
and limitations are recorded separately. This specification's agreed contract
is unchanged; #28–#30 and hosted checks retain their own gates.
The parent issue body remains unchanged.

## Problem Statement

A buyer can use the controlled procurement-to-approved-PDF workflow, but a
successful demonstration does not establish repeatable correctness, interactive
performance across supported sizes, or an understandable first-time experience.
Evidence currently spans separate increments; runtime observations are single
descriptive runs, browser acceptance is manual, and unfamiliar-buyer usability
has not been assessed. The thesis needs a reproducible, bounded assessment whose
conclusions distinguish implemented capability from measured and unassessed claims.

## Solution

Evaluate the current controlled hybrid system: read-only Odoo quotations,
source-attributed explicit business terms, separately synthetic historical data
and saved Decision Tree, MILP plans, five stress types, immutable storage, human
approval/No-award and approved PDF. Reuse existing correctness and integration
evidence, measure supported synthetic HTTP workloads, add a local browser smoke
suite, and investigate buyer tasks through agent/user walkthroughs.

Fix evidenced defects that block these checks in bounded changes. Deliver an
AC/NFR/RQ assessment with reproducible evidence, failures and limitations, plus
a prioritized substantial UX/UI follow-up. The intended buyer understands
procurement but has not learned this app. T18 is not the final development
increment: improve and reassess the buyer experience before final acceptance
and thesis closure. External unfamiliar-participant sessions remain pending.

## User Stories

1. As a procurement buyer, I want evaluations to identify their quotation, business-term and synthetic-model sources, so that I understand what the result represents.
2. As a procurement buyer, I want saved supplier evaluations and tree explanations to remain traceable, so that I can question a plan's assumptions.
3. As a procurement buyer, I want allocations to satisfy demand and every supported hard constraint, so that I do not approve an invalid procurement plan.
4. As a procurement buyer, I want minimum-cost and epsilon alternatives to show exact allocations, cost, premium and exposure, so that I can explain my trade-off.
5. As a procurement buyer, I want stable results under the same input and configuration, so that repeated evaluation is understandable.
6. As a procurement buyer, I want input rejection, infeasibility, incomplete solver results and technical failure to be distinguished, so that I know what action is justified.
7. As a procurement buyer, I want each supported disruption to produce a separate result against the original base, so that I can compare assumptions without changing the saved case.
8. As a procurement buyer, I want changed-demand comparisons to be identified clearly, so that I do not mistake different totals for like-for-like savings.
9. As a procurement buyer, I want stored reopening and exact replay to preserve content without upstream reads or recalculation, so that I can recover my recorded decision context.
10. As a procurement buyer, I want explicit approval of a valid original-base plan with its required reason, so that my recorded choice is intentional.
11. As a procurement buyer, I want a reasoned No-award on a separate base, so that declining an order is a traceable human outcome.
12. As a procurement buyer, I want uncertain saves to retain the exact request and key for explicit retry, so that recovery does not create a different intent.
13. As a procurement buyer, I want conflicting or concurrent decisions to be handled safely, so that one immutable final decision remains authoritative.
14. As a procurement buyer, I want the viewed and downloaded PDF to match the approved snapshot, so that the document represents my saved choice.
15. As a procurement buyer, I want PDF failure and retry to preserve approval, so that a document problem does not lose the final decision.
16. As a procurement buyer, I want unavailable-backend and recovery states to be understandable, so that I do not confuse failure with successful saving.
17. As a first-time procurement buyer, I want the workflow's next action and current base/scenario context to be clear, so that I can complete a task without developer guidance.
18. As a first-time procurement buyer, I want to understand the exact plan I am approving, so that spatially separated comparison and approval controls do not lead to a mistaken choice.
19. As a procurement buyer using a keyboard or narrow screen, I want to complete the essential workflow and access exact values, so that interaction and layout do not block my decision.
20. As a procurement buyer, I want to locate and download the approved document on desktop and mobile, so that I can use it after finalization.
21. As a project evaluator, I want repeated measurements at supported supplier and epsilon sizes, so that performance conclusions are stronger than a single demonstration.
22. As a project evaluator, I want fresh computation, stored operations and first/cached PDF generation measured separately, so that caches do not disguise expensive work.
23. As a project evaluator, I want raw attempts, failures, timeouts and solver outcomes retained, so that summaries do not hide unsuccessful operations.
24. As a project evaluator, I want hashes, versions, hardware, configuration and preparation boundaries recorded, so that another evaluator can reproduce and interpret the results.
25. As a project evaluator, I want a committed smoke flow through real Reflex, FastAPI and disposable PostgreSQL, so that browser-to-backend regressions can be detected locally.
26. As a project maintainer, I want isolated fixtures, bounded startup and cleanup of owned processes, so that evaluation does not damage owner evidence or databases.
27. As a thesis author, I want canonical acceptance criteria, nonfunctional requirements and research questions mapped to evidence, so that every conclusion has a defensible scope.
28. As a thesis author, I want walkthrough observations separated from unfamiliar-participant evidence, so that I do not claim first-time usability from agent inspection.
29. As a project owner, I want prioritized UX/UI findings and bounded blocker fixes, so that later design work addresses observed buyer problems.
30. As a project owner, I want completion and remaining development gates stated explicitly, so that scoped T18 closure does not imply a finished modern UI or complete thesis acceptance.

## Implementation Decisions

- Preserve the existing ERP-independent core, adapter boundaries, FastAPI,
  PostgreSQL, Reflex and local Podman + Compose baseline. Python 3.11 remains
  the compatibility baseline; no new domain vocabulary or ADR is required.
- Evaluate the implemented one-product controlled hybrid. The fixed three-supplier
  live Odoo check remains separate from synthetic volume measurements. Never
  relabel generated history as observed evidence or promote the model implicitly.
- Extend existing evaluation/demo tooling only where required. Prefer existing
  HTTP contracts over new application interfaces; add no general benchmark
  framework, production telemetry, schema migration or public endpoint by default.
- Synthetic HTTP workloads comprise all six combinations of **3/5/10 suppliers**
  and **1/3 epsilon requests**, within the saved model's declared validity and
  current API bounds. Prepare fixtures/model offline. Record requested epsilons
  separately from returned distinct alternatives; deduplication is not a failure.
- Each workload has **two warm-up runs and 30 measured runs**. Measure operation
  latency from local HTTP request to response, including API/database/solver
  work. Fresh creation and scenarios use fresh keys; exact replay reuses the
  original request/key. Approvals and first PDFs use eligible fresh bases.
- Exercise all five supported stress types and a controlled infeasible outcome.
  Document each operation's sample count; do not pool different operations or
  workload sizes. Choose bounded scenarios that preserve model validity.
- Local observed p95 targets are **5 s** for fresh creation and each stress
  calculation; **1 s** for stored GET, exact replay, approval and cached PDF;
  **3 s** for first PDF rendering/storage. These are agreed PoC targets, not SLAs.
  Do not silently relax them after observing results.
- Report median, nearest-rank p95 and maximum with attempted/completed/failed
  counts. For 30 timed attempts, p95 is the 29th sorted elapsed time. Include
  failed/timed-out attempt latencies and separately report their outcomes;
  fast errors cannot establish success. Missing reliable elapsed measurements
  remain explicit incomplete observations. Retain warm-up records separately.
- Record raw measurements, response/solver outcomes, environment/hardware,
  tested SHA and working-tree status, dependency/solver versions, seeds,
  input/model/dataset/policy hashes and workload identity. Keep tokens and
  secrets out of reports and browser/service diagnostic artifacts.
- Distinguish warmed processes/model/fonts, first artifact generation, startup,
  offline preparation/training and browser task/display time. Sequential latency
  evidence and concurrent transaction correctness are separate claims. Existing
  safety timeouts, including the shared 30 s MILP budget, remain distinct from
  targets. Retain partial/unproven outcomes at the larger workload.
- Add optional `pytest-playwright` test dependencies and a **Chromium-only,
  local-first** suite under the existing E2E marker. Ordinary fast-test
  collection must not require optional browser packages. A deliberately selected
  E2E gate with missing prerequisites must fail clearly rather than silently skip.
- Run real FastAPI/Reflex against an explicitly identified disposable helper
  PostgreSQL database. Use the existing Podman machine. Never reset Odoo or an
  owner application database. Bound readiness and teardown; stop only owned
  processes. Isolate prepared synthetic inputs without overwriting owner artifacts
  or allowing browser-selected models. A test-only composition or verified
  backup/restore is acceptable; a new production artifact-selection feature is not.
- For unavailable-backend browser coverage, stop the harness-owned FastAPI
  process: Reflex calls it server-side, so browser request interception cannot
  establish this behavior. Check visible outcome and safe retry/recovery state.
- Walkthroughs cover creation, plan explanation, all supported disruption meanings,
  infeasibility, return to original base, alternative approval, separate No-award,
  reopening, uncertain-save/backend/PDF recovery and document access. Record
  actor type, completion, assistance, critical mistakes, task time, comprehension
  and comments; label agent and app-owner observations accurately.
- Investigate return journeys requiring a retained UUID, setup/result hierarchy,
  approval clarity, scenario context, uncertain-save explanation, PDF navigation,
  keyboard/mobile accessibility and developer-oriented guidance. These are
  candidates from prior inspection, not already measured novice failures.
- Fix observed blockers with the smallest complete change, preserving trust,
  idempotency and immutable content. Record nonblocking findings for the later
  substantial UX/UI increment. A fix cannot silently widen accepted product scope.

## Testing Decisions

- Test externally observable outcomes and business invariants rather than private
  implementation details. Reuse prior T13 independent reference optima,
  constraint/determinism/fault tests; T14 cutoff/split/artifact/metric tests;
  T15 API/provenance/replay/scenario tests; and T17 approval/PDF/full-flow tests.
  Add tests only for demonstrable gaps or defects, not duplicate coverage.
- Use the **HTTP seam** for integrated input, inference, allocation, scenarios,
  errors, stored retrieval/replay, human decisions and documents. Lower-level
  independent oracles remain appropriate for correctness; a larger HTTP workload
  does not replace proof against a small independently solved reference case.
- Use **real disposable PostgreSQL** for contention, atomicity, uniqueness,
  rollback and immutability claims. Existing creation, approval and PDF concurrency
  coverage is prior art. Mocks or sequential duplicates do not establish race safety.
- Use the **real browser** for one bounded create → compare → approve → reopen
  → PDF smoke flow plus backend-unavailable/recovery coverage. Inspect actual saved
  outcome and downloaded bytes/hash against the stored backend artifact, not just
  button presence. Cached download byte identity is distinct from arbitrary
  rerender binary equality; approved-content integrity remains mandatory.
- Manual desktop/mobile/keyboard, text zoom, focus/error announcement and visual
  assessment complement smoke tests. Automated smoke and compilation do not
  establish WCAG conformance or validated first-time-buyer usability.
- Run focused checks during fixes, required Python 3.11 fast gates once before
  handoff, and relevant available service/live/browser gates. CBC execution and
  ML runtime gates must execute rather than skip. Resolve the relevance of the
  two previously skipped T7-S live checks using their own contracts and retained
  evidence; report residual gaps rather than inventing a new Odoo setup requirement.
- Keep the existing required **Quality** check unchanged. Hosted browser CI and
  Ubuntu browser execution are deferred. Record hosted checks only for their exact
  published SHA; publication remains under user control.

Completion criteria for this specification:

- [ ] A reproducible evaluation contract and matrix cover **FR-V2-01–12,
  AC-V2-01–13, NFR-V2-01–08 and RQ-V2-01–07**, linking existing evidence and
  identifying genuine gaps without changing their canonical definitions.
- [ ] All six supported synthetic supplier/epsilon workloads have the agreed
  warm-ups and measured attempts, operation-specific raw/summary results,
  explicit errors/incomplete runs and target outcomes; the fixed live Odoo
  validation is reported separately with its provenance and prerequisites.
- [ ] Existing and missing correctness/negative/integrity coverage is assessed;
  selected real-database/live gates report actual execution, skips and blockers.
- [ ] The committed local Chromium smoke proves the real-stack saved workflow,
  downloaded artifact identity and backend-unavailable recovery, with documented
  prerequisites, isolation, startup, expected outcome and cleanup.
- [ ] Agent/user task, desktop/mobile/keyboard and recovery walkthroughs are
  recorded with assistance/errors/comprehension; unfamiliar-participant usability
  is explicitly **NOT ASSESSED** unless such sessions actually occur.
- [ ] Evidenced blocking defects are fixed and affected checks rerun. Unresolved
  defects and failed targets remain FAIL/BLOCKED, or carry an explicitly
  user-accepted limited conclusion; a report alone is not a passing gate.
- [ ] The controlled-scope report answers each RQ with evidence and limitations,
  links canonical AC/NFR outcomes and prioritizes subsequent UX/UI work and
  reassessment before final acceptance. No unfinished buyer validation is labelled
  complete merely because scoped T18 work closes.

## Out of Scope

Observed-history/model promotion or claims of real-world predictive superiority;
arbitrary quotation discovery; broader combined scenarios; multi-product planning;
Odoo writes, Purchase Order creation, GUI automation or direct database access;
production IAM/RBAC, legal approval/signatures or a legally complete external PO;
new online training; recalculation during stored retrieval/finalization/PDF;
cloud deployment, a general load-testing platform, production SLAs or new hosted
browser CI; whole-frontend redesign or silent roadmap renumbering; thesis closure.

Substantial modern UX/UI improvements and reassessment are a **required later
development stage**, not evidence that the current experience is finished.
External sessions with 3–5 unfamiliar participants remain pending, not mandatory
for scoped T18 closure. Their absence limits usability conclusions.

## Further Notes

The user confirmed the complete plan in Q9 on 2026-10-11 after agreeing the
scope, audience, measurement contract, walkthrough limits, browser deliverable
and local-first delivery. The HTTP/PostgreSQL/browser seams reuse those accepted
decisions. This invocation authorizes specification publication; delivery-ticket
granularity/dependencies are reviewed separately before child-ticket publication.

Traceability follows the official task's controlled history/input, Decision Tree,
MILP, frontend, scenarios, storage, human approval, final PDF and reproducible
evaluation obligations. FR-V2-01–12 and AC-V2-01–13 retain their existing meanings.
NFR-V2-01–08 respectively cover modularity, reproducibility, data integrity,
testability, least privilege, snapshot/approval integrity, replaceable frontend,
and local reproduction/runtime. RQ-V2-01–07 cover ERP/hybrid boundaries, controlled
ML, constraint/reference-optimum correctness, cost/exposure trade-offs, disruption
outcomes, decision/document traceability and local runtime/reproducibility limits.
Preserve accepted ADRs, particularly ADR-024–027; introduce no new requirement IDs.

Authoritative sources and baseline evidence:

- [Official task, reference 423.589/25/140](https://drive.google.com/file/d/1T4Fo_RsSFgs-zjV5NUPfF6_h7xOraog8/view).
- [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit).
- [03_ARCHITECTURE_DECISIONS](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit).
- [02_ROADMAP](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit).
- [04_RESEARCH_NOTES](https://docs.google.com/document/d/1wpglDSL8rMUCFADUhslrgtIRRcWVAdujoEncrDY9WmY/edit).
- [Merged T17 PR #24](https://github.com/SafarErik/odoo-procurement-decision-support/pull/24), baseline `ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`.
- [Full-flow handoff at the merged baseline](https://github.com/SafarErik/odoo-procurement-decision-support/blob/ed4be413b11dc469307fc1bb1ed4bd6c16c17b88/docs/T17_FULL_FLOW_HANDOFF.md).
- [Approval handoff at the merged baseline](https://github.com/SafarErik/odoo-procurement-decision-support/blob/ed4be413b11dc469307fc1bb1ed4bd6c16c17b88/docs/T17_HANDOFF.md).
- [PDF handoff at the merged baseline](https://github.com/SafarErik/odoo-procurement-decision-support/blob/ed4be413b11dc469307fc1bb1ed4bd6c16c17b88/docs/T17_PDF_HANDOFF.md).
- [Baseline Quality SUCCESS](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38150351508) and [Container/API SUCCESS](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38150351451).

Source reconciliation: refreshed Drive records retain pre-merge T17 publication
wording and the earlier T18 → T19 sequence. The merged baseline and user-confirmed
T18/follow-up decisions supersede those dated status statements; the accepted
requirements/ADRs are unchanged. The T19 thesis-closure milestone is preserved
after necessary development and reassessment. No Drive update is performed here.

Baseline limitations remain explicit: synthetic ML is not calibrated operational
forecasting; actor attribution is not authenticated identity; PDF/font/size limits
remain as recorded; historical browser acceptance is manual/local; two T7-S live
checks were skipped; prior 5.605/5.671 s timings are descriptive. No T18 runtime or
participant result is claimed by this specification.

Thesis evidence follows problem → decision → implemented behavior → evidence →
limitation → chapter relevance. Chapter 7 owns measurements and assessment;
chapters 3/4/6 receive only changed requirements interpretation, behavior or
architecture evidence; conclusions/further work follow actual RQ outcomes.
Repository artifacts remain English and Drive living documents Hungarian.
Commit, push, merge and Drive synchronization remain separate user-controlled work.
