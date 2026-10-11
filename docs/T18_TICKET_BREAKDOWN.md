# T18 evaluation delivery tickets — approved and published

Status: **APPROVED AND PUBLISHED — #26–#30 remain open; [#26 is implemented/verified locally](T18_26_HANDOFF.md), other slices have not started.**
Prepared 2026-10-11 from [specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25)
and the [confirmed plan](T18_EVALUATION_PLAN.md). The parent specification remains
unchanged. The user approved all five slices and dependencies before publication.
Slice identifiers below distinguish delivery order from the linked issue numbers.

## Recommended delivery and dependency graph

| Slice / GitHub issue | End-to-end outcome | Blocked by |
| --- | --- | --- |
| 1 / [#26](https://github.com/SafarErik/odoo-procurement-decision-support/issues/26) | Repeated three-supplier procurement-to-PDF HTTP evaluation with usable evidence | None |
| 2 / [#27](https://github.com/SafarErik/odoo-procurement-decision-support/issues/27) | Full supported workload/stress measurements and separate controlled live validation | #26 |
| 3 / [#28](https://github.com/SafarErik/odoo-procurement-decision-support/issues/28) | Reproducible real-stack Chromium smoke and unavailable-backend recovery | None |
| 4 / [#29](https://github.com/SafarErik/odoo-procurement-decision-support/issues/29) | Buyer-task, keyboard/mobile and recovery assessment with bounded blocker fixes | None |
| 5 / [#30](https://github.com/SafarErik/odoo-procurement-decision-support/issues/30) | Consolidated controlled-scope AC/NFR/RQ assessment and UX/UI follow-up | #27, #28, #29 |

Recommended practical order is 1 → 2 → 3 → 4 → 5. This is a convenient execution
order, not a claim that measurements gate browser or manual evaluation. Slices
1, 3 and 4 can begin independently using the existing controlled fixtures.
Slice 5 depends transitively on 1 through 2, so no redundant blocker is added.

The earlier four-area plan is refined into five delivery slices: the initial
measurement ticket includes a complete working tracer flow instead of a
documentation-only contract task; browser automation and usability assessment
are separate to keep each bounded. No prefactoring ticket is justified by current
evidence. Reuse existing contracts and components, without new infrastructure,
public API, schema migration or production artifact-selection capability.

## Shared contract for every published child

- Part of specification #25; preserve its scope, canonical requirement meanings,
  accepted ADRs and test boundaries. Repository engineering material is English.
- Keep read-only Odoo quotations, explicit terms and synthetic ML provenance
  separate. Training/preparation remains offline. Stored retrieval, exact replay,
  human finalization and PDF must not acquire sources or recalculate plans.
- Use only a separately identified disposable helper database for reset-based
  checks, the existing Podman machine and owned processes. Do not overwrite
  owner-prepared evidence, reset application/Odoo data or automate Odoo UI.
- Run focused checks for changes and required fast gates once before handoff;
  record actual service/live/browser scope and any skipped/blocked gates. Keep
  Quality unchanged and hosted browser CI deferred. Do not repeat unchanged
  successful gates without a relevant reason.
- Fix evidenced blockers within the slice's bounded behavior and verify the fix.
  If a discovery cannot fit a fresh context window, describe a concrete follow-up
  and its real blocking edge for review; never turn a ticket into an unlimited
  cleanup task. Unresolved failures remain explicit, not implied PASS.
- Handoffs state changes, evidence, remaining gaps, needed user action and the
  next capability; thesis notes follow problem → decision → behavior → evidence
  → limitation → chapter relevance. Preserve user control of commit/push/merge.
- Unfamiliar-participant usability remains NOT ASSESSED. Substantial UX/UI
  improvement and affected reassessment remain later development before final
  acceptance and T19 thesis closure. No Drive writes are authorized here.

## 1 — Measure a complete three-supplier procurement-to-PDF workflow

### Parent

Part of [#25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).

### What to build

Let an evaluator repeatedly run a real synthetic three-supplier, one-epsilon
HTTP flow from fresh planning through a supplier-outage comparison, stored
retrieval/exact replay, explicit base approval and first/cached approved PDF.
Produce raw and summarized operation evidence that can be interpreted and rerun.
This proves the evaluation mechanism on one complete workflow before scaling it.

### Acceptance criteria

- [ ] Freeze the already agreed workload/operation/percentile contract and create
  an initial FR/AC/NFR/RQ evidence inventory using existing tests and reports.
  Distinguish retained historical evidence from new executed measurements.
- [ ] Prepare valid controlled synthetic inputs and a matching saved model
  offline; run the real FastAPI/CBC/PostgreSQL path for 3 suppliers and 1 epsilon
  with two warm-ups and 30 measured run attempts. Keep the model's validity
  bounds, fresh write keys and exact replay intent explicit.
- [ ] Measure fresh creation, supplier-outage calculation, stored GET, exact
  replay, approval, first PDF and cached PDF separately. Verify allocations,
  original-base immutability, decision/content identity and exact cached document
  bytes; do not benchmark a replay as fresh inference/optimization.
- [ ] Retain raw warm-up/measured observations, failures/timeouts/partial solver
  outcomes and operation sample counts. A failed prerequisite produces an
  explicit unmeasured downstream operation, not a fabricated latency or success.
- [ ] Summarize median, nearest-rank p95 and maximum: targets 5 s fresh/scenario,
  1 s stored GET/replay/approval/cached PDF, 3 s first PDF. Include timed failures
  and separate outcome counts; missing elapsed times remain incomplete evidence.
  A fast error cannot satisfy a successful-operation gate.
- [ ] Record SHA/working-tree status, environment/hardware, dependency/CBC versions,
  hashes/configuration/seeds and warm/cold boundaries. Startup, offline training
  and browser task time are separate; exclude secrets from artifacts.
- [ ] Add a small meaningful test for measurement/report accounting, including
  failed/incomplete observations and percentile handling; retain existing
  business-rule and stored-only checks rather than duplicating them.
- [ ] Document prerequisites, disposable-service startup, commands, expected
  outcomes, evidence location and owned-process cleanup. Report executed gates
  and any evidenced blocker fix with affected checks.

### Blocked by

None (can start immediately).

Traceability: FR-V2-04–08/10–12; AC-V2-04–08/10–13;
NFR-V2-02/04/06/08; RQ-V2-03–07. The initial inventory also routes the remaining
canonical FR-V2-01–12, AC-V2-01–13, NFR-V2-01–08 and RQ-V2-01–07.

## 2 — Evaluate supported workload sizes and all stress outcomes

### Parent

Part of [#25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).

### What to build

Extend the working HTTP evaluator to report how the procurement workflow behaves
at all supported evaluation sizes and disruptions, with live quotation evidence
kept separate. Give the buyer and thesis author defensible cost/exposure,
feasibility and runtime comparisons rather than one descriptive demo timing.

### Acceptance criteria

- [ ] Cover all six 3/5/10-supplier × 1/3-epsilon synthetic workloads, each with
  two warm-ups and 30 measured attempts and the parent's operation-specific
  targets. Reuse slice 1's result if the evaluated code/configuration is unchanged;
  otherwise retain its history and remeasure affected workloads.
- [ ] Exercise supplier outage, capacity reduction, demand increase, price
  increase and the supported bounded demand-plus-one-supplier combination,
  including controlled infeasibility. Record operation/workload-specific counts
  without pooling; distinguish requested epsilons from deduplicated alternatives.
- [ ] Verify integer-demand/hard-constraint invariants, cost/premium/exposure,
  original-base links, saved scenario deltas and immutable input provenance.
  Distinguish different-demand totals from like-for-like savings. Reuse small
  independent optimum tests rather than claiming optimality from runtime alone.
- [ ] Retain failures, partial/unproven solver results and shared-budget timeouts;
  keep the accepted thresholds unchanged. Diagnose evidenced blockers with
  bounded fixes and affected reruns, never hiding them through retries or pooling.
- [ ] Independently reproduce the fixed three-supplier controlled live Odoo chain
  through stored results, approval/PDF and a separate No-award, reusing the
  existing full-flow demonstration. Keep its actual quotation provenance,
  synthetic ML context, prerequisites and results outside the volume matrix.
- [ ] Link existing negative, replay, concurrency, rollback and immutability
  evidence; execute relevant available real-database/live checks and add only
  genuine missing tests. Resolve relevance of the two skipped T7-S live gates
  without silently requiring new Odoo configuration or waiving the history claim.
- [ ] Produce raw/summary workload evidence, exact environment/hash identity and
  a reproducible runbook with outcomes, incomplete measurements and limits.
  A failed target remains a failed target pending a fix or explicit limited
  conclusion; it is not a passing performance assessment.

### Blocked by

[#26](https://github.com/SafarErik/odoo-procurement-decision-support/issues/26) — reuses its complete HTTP evaluator and observation/report contract.

Traceability: FR-V2-01–08/10–12; AC-V2-01–08/10–13;
NFR-V2-02–06/08; RQ-V2-01–07. Synthetic model metrics remain controlled evidence.

## 3 — Automate the real buyer workflow and backend-unavailable recovery

### Parent

Part of [#25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).

### What to build

Provide a repeatable local Chromium smoke suite that creates a case, compares
saved plans, approves an original-base plan, reopens it and downloads its approved
PDF through real Reflex, FastAPI and disposable PostgreSQL. Also prove the
buyer's visible failure and safe recovery when the backend is unavailable.

### Acceptance criteria

- [ ] Add optional pytest-playwright/Chromium tooling using the existing E2E marker
  and Python 3.11 baseline. Fast-test collection remains independent of optional
  packages; explicitly selected E2E with missing prerequisites fails clearly.
- [ ] Start real owned FastAPI/Reflex services with bounded readiness/teardown and
  a separately identified disposable helper database. Isolate offline-prepared
  synthetic inputs and owner artifacts; do not add browser-selected models or
  reset application/Odoo data. Document startup, expected outcome and cleanup.
- [ ] Exercise create → compare → explicit valid base approval → stored reopen
  → PDF view/download; assert saved outcome, allocation/decision context and
  downloaded bytes/hash against the backend artifact, not only control presence.
- [ ] Stop only the harness-owned FastAPI for backend-unavailable coverage;
  browser request interception is insufficient for Reflex's server-side client.
  Check visible error, absence of false success and safe explicit recovery after
  restoration. Preserve exact intent/key where a write outcome is uncertain.
- [ ] Retain useful failure traces, screenshots and service logs with secrets
  excluded. Record actual local execution and fix evidenced blockers with
  focused regressions; compilation alone is not browser acceptance.
- [ ] Keep hosted browser CI, Ubuntu browser execution, visual/accessibility
  conformance and unfamiliar-buyer validation outside this smoke-suite claim.
  Required Quality remains unchanged; no broad automated visual suite is added.

### Blocked by

None (can start immediately from the existing controlled workflow and fixtures).

Traceability: FR-V2-07/09–12; AC-V2-09–13;
NFR-V2-02/04–08; RQ-V2-06/07. No measurement-tool dependency is required.

## 4 — Assess buyer tasks and fix evidenced interaction blockers

### Parent

Part of [#25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).

### What to build

Assess the existing workflow against tasks a procurement-aware first-time buyer
needs to complete. Record agent/user desktop, mobile, keyboard and recovery
observations, fix bounded defects that prevent safe task completion, and produce
prioritized evidence for the later substantial UX/UI improvement increment.

### Acceptance criteria

- [ ] Use the running controlled workflow for creation, plan/cost/exposure
  explanation, disruption interpretation, infeasibility, return to original base,
  alternative approval with reason, separate No-award, stored reopening and
  approved document access. Retain actual synthetic/live source distinctions.
- [ ] Examine uncertain-save, backend-unavailable and PDF failure/retry behavior
  without losing the final decision, altering retry intent or presenting false
  success. Use controlled faults and owned processes; record outcomes accurately.
- [ ] Walk through desktop, narrow/mobile viewport and keyboard-only interaction,
  including focus, labels/error announcements, text zoom, exact values and
  PDF access. Retain screenshots/task evidence; do not claim formal WCAG conformance.
- [ ] Record actor type, task completion, assistance, critical mistakes, task
  time, comprehension and comments separately from API latency. Agent inspection
  and an app-owner walkthrough are identified as such; any pending user-run
  task remains pending rather than being invented by the agent.
- [ ] Evaluate retained-UUID reopening, setup/result hierarchy, approval clarity,
  scenario context, uncertain-save explanation, PDF navigation and developer
  guidance as hypotheses; distinguish new observed defects from earlier source
  observations and accepted scope limitations.
- [ ] Fix evidenced safe-completion/accessibility blockers with bounded changes,
  regression coverage where appropriate and affected task rechecks. Preserve
  approval/PDF identity, base-only rules, exact retry and server-side token handling.
  Larger redesign or API expansion remains separately scoped follow-up work.
- [ ] Deliver prioritized UX/UI findings with buyer impact, reproduction/evidence,
  proposed improvement and reassessment task. External sessions with 3–5 unfamiliar
  participants remain pending and unfamiliar-participant usability NOT ASSESSED;
  T18 task reports must not claim validated first-time-buyer usability.

### Blocked by

None (manual tasks can be assessed against the already implemented workflow;
slice 3's automation is useful regression coverage but does not gate starting).

Traceability: FR-V2-07–12; AC-V2-08–13; NFR-V2-04–08;
RQ-V2-04–07. Modern UI and first-time-user validation remain later development.

## 5 — Report controlled acceptance and prioritize UX/UI reassessment

### Parent

Part of [#25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).

### What to build

Give the project owner and thesis author one defensible assessment of the
controlled system: what passed, failed, remains limited or was not assessed,
with exact evidence and the next buyer-visible UX/UI improvements. Consolidate
completed measurements, browser and walkthrough results without changing their
scope or treating T18 as the end of development.

### Acceptance criteria

- [ ] Complete the canonical FR-V2-01–12 / AC-V2-01–13 / NFR-V2-01–08 matrix:
  scope, defined acceptance outcome, evidence link/date/SHA, executed gate and
  limitation. Distinguish historical, new local, live, service, browser and hosted
  results; no blanket PASS is inferred from a test count or merged PR.
- [ ] Answer RQ-V2-01–07 from actual evidence: ERP/hybrid boundaries, controlled
  ML integrity/metrics, reference-optimum/constraint correctness, cost/exposure
  alternatives, stress outcomes, approval/document traceability and local runtime.
  Synthetic metrics/exposure imply neither calibrated risk nor business superiority.
- [ ] Consolidate raw and summarized workload outcomes against unchanged p95
  targets, including failed/missing attempts and partial solver results. Explain
  the sample/hardware/warm-state limits and separate live Odoo and browser task evidence.
- [ ] Ensure relevant results still describe the assessed revision after blocker
  fixes. Rerun affected measurements/tasks/smoke as justified; retain earlier
  evidence rather than replacing history or rerunning every unchanged gate.
- [ ] Record outstanding defects and thresholds as FAIL/BLOCKED or explicitly
  user-accepted limited conclusions. Do not mark a corresponding AC/NFR satisfied
  merely because the report is written; describe any needed user action.
- [ ] Prioritize the next substantial UX/UI increment using observed buyer impact
  and reassessment tasks. Retain external novice sessions as NOT ASSESSED and
  require further usability evidence before validating the buyer experience.
  Preserve T19 thesis closure after necessary development, without renumbering it.
- [ ] Deliver a dated engineering handoff, reproducible evidence links and concise
  current README/index status. Map thesis-useful findings to chapter 7 and affected
  chapters/conclusions; leave Hungarian Drive synchronization and issue closure
  to separately authorized stages. Do not close or modify parent #25 in this ticket.

### Blocked by

- [#27](https://github.com/SafarErik/odoo-procurement-decision-support/issues/27) — supported workload, stress and controlled live evidence.
- [#28](https://github.com/SafarErik/odoo-procurement-decision-support/issues/28) — real-stack browser smoke and recovery evidence.
- [#29](https://github.com/SafarErik/odoo-procurement-decision-support/issues/29) — task assessment, bounded fixes and UX follow-up evidence.

Traceability: all FR-V2-01–12, AC-V2-01–13, NFR-V2-01–08 and RQ-V2-01–07.

## Review and publication record

The user approved all five tickets and their blocking edges. Published #26–#30
in dependency order with `ready-for-agent`. Independent readback verified each
exact body, title, open state, label and intended blocker references. Available
connector metadata exposes no native relationship mutation, so each child
records its parent and explicit real issue blockers in its body. These are text
relationships, not claimed native GitHub sub-issues or dependency edges.

The user-invoked to-tickets skill prohibits modifying or closing the parent.
Independent readback confirms #25's body/state are unchanged; no parent task list
was added. The runnable frontier is #26, #28 and #29. Recommended next work is
#26, proving one complete measurement flow before expanding to #27.

Subsequent implementation update: the user authorized #26 and its
[local handoff](T18_26_HANDOFF.md) records the complete measurement flow and
passing three-supplier targets. Issue closure/publication are not performed
by this local implementation update; #27 can reuse the evaluator after review.

No application implementation, dependency installation, service startup, Drive
edit, stage, commit, push, merge or issue closure was performed in this stage.
