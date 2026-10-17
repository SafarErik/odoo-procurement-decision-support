# Supported workload, stress and live evaluation — #27

Date: 2026-10-11. Branch: `feature/T18-implementation`.
Scope: [issue #27](https://github.com/SafarErik/odoo-procurement-decision-support/issues/27),
part of [specification #25](https://github.com/SafarErik/odoo-procurement-decision-support/issues/25).
Baseline: committed #26 at `97afe03`; this increment's source changes are
uncommitted and identified by hashes in the reports, not mislabelled as HEAD.
Status: **LOCAL #27 GATES COMPLETE — all synthetic targets, the fixed live
quotation flow and current T7-S/T8 checks pass.** The user renewed the dedicated
key; both affected checks passed in a separate rerun. The initial 54-pass/2-fail
run remains recorded. Overall T18, publication and final thesis acceptance
remain separate; this is not one 56-pass service execution.

## Problem → decision → implemented behavior

The initial repeated measurement covered only one supplier/epsilon combination
and outage. Extend the same offline preparation and served HTTP evaluator to
3/5/10 suppliers × 1/3 requested epsilons, all five supported stress types and
a bounded infeasible case. Reuse the existing synthetic ML, CBC, PostgreSQL,
approval/PDF and controlled live demo contracts. No production endpoint,
business rule, migration, frontend, dependency or infrastructure design changed.

[The evaluator](../tools/t18_evaluation.py) records 12 operations per fresh flow.
It independently checks the returned hard constraints/exact metrics with the
existing validator, verifies every requested epsilon's saved plan reference/cap,
and validates changed terms, original-base lineage, saved deltas, retained facts/
assessments and field provenance. Stored cost/exposure/allocation differences
must match exact arithmetic, with changed-demand meaning explicit. Deduplicated
alternatives are accepted; partial/unproven solver outcomes remain failures of
the complete-optimality gate. A successful infeasible operation means a saved,
explained capacity shortfall with no plan, not a solver failure.

The shared [offline fixture helper](../tools/t15_demo.py) accepts only the three
supported supplier counts; its default three-supplier behavior is preserved for
existing synthetic/live demos. Larger inputs add distinct held-out synthetic
profiles and explicit simulated prices/capacities. Demand/other policy terms
stay fixed. The [runbook](T18_27_EVALUATION_RUNBOOK.md) defines the fixture shape,
preparation, timed operations, independent live stage and cleanup.

Each workload gets two full warm-ups and 30 measured attempts. Fresh keys and
eligible original bases are used; no automatic retry, pooling or threshold
relaxation is introduced. All POST intents are checkpointed before submission.
Timed errors remain in percentiles, missing samples stay explicit, and ambiguous
writes/artifacts stop that workload. The earlier [#26 report](T18_26_EVALUATION.json)
is preserved; its smaller protocol is historical and is not substituted for
the extended 3/1 execution.

## Synthetic HTTP measurements

The authoritative local reports are under
`.artifacts/t18-27-63d402b5/synthetic-<suppliers>-<epsilon-count>/evaluation-<UUID>.json`.
[Repository evidence](T18_27_EVALUATION.json) preserves observations, result/run/solver outcomes,
saved comparisons, identities, hashes and prepared inputs while referencing
repeated values through per-report SHA-256 templates and omitting verbose explanations.
Template keys bind full raw values, including omitted explanations. Every timing,
outcome, request key and response identity remains recorded; no sample is pooled
or discarded. Repeated final decisions reference the same attempt's approval.
Full snapshot equality and exact business checks happen on actual responses.

Runtime: Python 3.11.16, served FastAPI on loopback 8002, actual scikit-learn saved
inference, PuLP 3.3.0/CBC 2.10.3, disposable PostgreSQL 16.15. The existing Podman
WSL machine has 7 CPUs/2 GiB; Windows host has 14 logical CPUs and 33,765,654,528
bytes physical memory. A new project `procurement-t18-27-63d402b5` binds database
VM port 55435; failed Windows `win-sshproxy` forwarding required a task-owned
localhost SSH tunnel on 55436. Existing Odoo containers also remain running.
No competing test/training/solver workload is initiated. The same served process
and database retain earlier cases in the fixed order 3/1 → 3/3 → 5/1 → 5/3 →
10/1 → 10/3; differences are descriptive, not a randomized causal size comparison.
Actual dependency/model/dataset/input/policy/CBC/source hashes accompany each
report. Startup/offline work, verification/checkpoint IO and browser display
time are excluded; first PDF is a fresh artifact in a warmed process.

All **2,160 measured operations** and **144 warm-up operations** succeeded, with
no HTTP/transport/validation failure, partial solver proof or missing timing.
Each of 72 operation/workload cells has 30 measurements and passes its unchanged
target. Nearest-rank p95 is the 29th sorted latency; warm-ups are excluded.
The highest p95 is **2.791729 s** for 10 suppliers/3 epsilons price increase,
below 5 s. The raw JSON also retains separate medians and maxima for every cell.

| Operation / p95 seconds | 3/1 | 3/3 | 5/1 | 5/3 | 10/1 | 10/3 | Target |
| --- | --- | --- | --- | --- | --- | --- | --- |
| create | 0.613187 | 1.094228 | 0.822461 | 1.401238 | 1.326263 | 2.453291 | 5 |
| supplier outage | 0.643561 | 1.032736 | 0.861725 | 1.426288 | 1.317848 | 2.411778 | 5 |
| capacity reduction | 0.566386 | 1.050906 | 0.831972 | 1.529521 | 1.374312 | 2.416080 | 5 |
| demand increase | 0.543678 | 1.024415 | 0.838110 | 1.431405 | 1.527524 | 2.405865 | 5 |
| price increase | 0.601633 | 1.004679 | 0.818616 | 1.461800 | 1.333048 | 2.791729 | 5 |
| combined | 0.658635 | 1.118114 | 0.846259 | 1.535536 | 1.319815 | 2.544175 | 5 |
| infeasible | 0.285847 | 0.274829 | 0.282883 | 0.304503 | 0.231848 | 0.263184 | 5 |
| approval | 0.250270 | 0.237032 | 0.275900 | 0.301873 | 0.288199 | 0.241109 | 1 |
| stored get | 0.209078 | 0.222418 | 0.191020 | 0.264684 | 0.238886 | 0.260503 | 1 |
| exact replay | 0.272189 | 0.260915 | 0.289521 | 0.274940 | 0.414181 | 0.362967 | 1 |
| first pdf | 0.232733 | 0.210357 | 0.313802 | 0.289403 | 0.367502 | 0.372053 | 3 |
| cached pdf | 0.212172 | 0.198034 | 0.212448 | 0.212160 | 0.232481 | 0.231284 | 1 |

The original three-supplier minimum remains EUR 102 at every size. One epsilon
returns one distinct alternative; three requests return two distinct alternatives
and a duplicate 20% run referring to the same plan as 10%. These are descriptive
outcomes of this fixture, not guarantees of the number of alternatives generally.

Read-only helper-database reconciliation verified every recorded case ID, key,
created time, parent, snapshot/request/provenance hash and exact result, plus
decision-record hashes and PDF bytes/reference/content binding. It found all
**1,352 evaluation cases, 194 decisions and 193 documents** (matrix plus separate
live flow). Database totals were 1,355/195/194: three explicitly identified
integration-fixture cases and their one decision/document predated measurement.
They are not hidden benchmark creations. The reconciliation is embedded in
both evidence exports; no Odoo database was accessed.

## Separate fixed live reproduction and history relevance

[Separate live evidence](T18_27_LIVE_VALIDATION.json) reproduces the fixed group-2 fixture,
read-only primary identity, explicit demand/capacity/MOQ/date terms and a newly
prepared **synthetic** matching model. This is not observed-model promotion or
part of the synthetic timing population. The existing T17 full-flow CLI covers
five stress types plus infeasible demand 500, alternative approval/PDF and
separate No-award. The complete HTTP demonstration took 7.482 s descriptively;
it is not a percentile or pooled sample. USD minimum 1,850 and alternative 2,200
remain the controlled expected outcomes. Independent #27 plan/delta/provenance/
comparison checks passed on all live snapshots.

After restarting the owned API with `T15_TRUSTED_MODEL_DIRECTORY` empty and both
Odoo containers stopped, stored GET, every exact POST replay and identical cached
PDF passed; No-award PDF returned 422. This establishes stored-only reopening of
the actual PostgreSQL cases, alongside existing forbidden-upstream/solver tests.

The initial service run executed the two previously disabled T7-S/T8 gates:
**54 passed, 2 failed**, with both failures caused by HTTP 401 from the configured
dedicated projection key. Other selected PostgreSQL and primary Odoo contracts
passed. The failed run is retained at `.artifacts/t18-27-63d402b5/integration.txt`;
a rejected credential is not evidence of a projection/algorithm defect or a PASS.

[T7-S](T7S_HANDOFF.md) and [T7/T8](T7_HANDOFF.md) preserve earlier controlled
history/security acceptance, including bounded method-only access, direct stock
denials and controlled adherence semantics. Those claims remain relevant to
the thesis's controlled-history obligation even though this evaluation's V2
model uses synthetic history. They are not waived, relabelled as fresh evidence,
or made into an observed-model prerequisite for the quotation/synthetic flow.
After the user confirmed renewal in local `.env`, both affected tests passed
in a focused rerun: **2 passed in 2.21 s, no failures or skips**. The renewed
dedicated key is accepted. The security test confirms bounded same-company
projection access, false generic CRUD rights, denied direct stock/cross-company
access and rejected invalid bounds. The history test confirms production adapter/
KPI assembly, controlled adherence **33.33% with sample size 3**, backorder
relationships and excluded supplier returns. Expected arrival remains the
operational scheduled date, not a validated supplier promise. The V2 Decision
Tree remains synthetic. No new user/role/fixture or broader ACL was imposed.

The rerun log/JUnit XML and source hashes are bound in the live export under
`service_contracts.credential_renewal_rerun`; full local artifacts remain at
`.artifacts/t18-27-key-rerun-ddf1b043/`. Gate flags and the reachable loopback URL
were set only for the test process. Podman/Odoo and the owner's existing 8069
listener were already running; no helper service/process was started or stopped.
The earlier measurement cleanup remains historical, separate from this rerun.

## Verification, limitations and next capability

Focused checks passed **27 tests**: all six real inference/CBC/API/stress/approval/
PDF flows with memory persistence, provenance/delta/comparison and epsilon-run
tampering rejection, plus existing default fixture/Odoo assembly regressions.
Ruff formatting/lint passed on changed Python files. An initial focused test
caught a wrong evaluator source-type literal; using the existing SYNTHETIC
constant fixed it before measurements. Initial Compose startup lacked the
provider on PATH; selecting the installed provider resolved startup. A pytest
cache permission warning did not prevent assertions; retain its actual scope.

Final gates passed: **591 fast tests, 59 deselected**, including the independent
T13 exhaustive oracle and actual required ML/CBC execution; Ruff 0.17.0 format
(208 files)/lint, compileall (required packages plus tools/document adapter),
pip check, both credential-suppressed Compose config checks and whitespace.
The remaining fast-suite warning is the existing Starlette TestClient deprecation;
no dependency upgrade was added. Existing T14 leakage/
artifact/runtime checks, T15 auth/negative/scenario/replay, real PostgreSQL
concurrency/rollback/immutability and T17/T21 approval/PDF fault/content evidence
are reused rather than replaced by large synthetic timing cases. Real PostgreSQL
contracts passed **36 checks** across T11/T12/T15/T17/T21; primary live Odoo checks
passed **18** in the initial run; both dedicated projection/history checks
passed in the later focused rerun, with the original two failures retained.
These include negative trust/input behavior, stored-only sentinels, genuinely
contending creation/finalization/rendering transactions, post-flush rollback and
database-enforced immutable records. See their linked tests in the inventory.

The first API stop guard correctly halted on a task-owned Windows `conhost.exe`
child; after identifying that console host and the actual Python child, only
the owned API was stopped. A local invariant command initially used the wrong
report filename; correcting it to `t17-run-*.json` passed against the already
completed live flow, without repeating POSTs. These are harness setup corrections,
not concealed workflow retries. The failed focused evaluator report and initial
integration failure log are retained; these setup corrections are recorded here.

Export verification reproduces every raw observation/summary and template
reference against its bound local report; evaluator/helper/model/input hashes
match the tested files. Documentation links and secret checks pass. Cleanup
stopped only owned API/tunnel processes, removed this disposable project and
generated secret file, verified no task listeners remained, and restored Odoo/
Podman's initially stopped state. Owner artifacts, `.env` and Odoo volumes were
preserved. Evidence exports retain cleanup results. Hosted CI, Reflex export,
new browser acceptance and participant assessment were not executed here.

| #27 acceptance area | Result |
| --- | --- |
| Six supported workloads, fixed counts/targets | PASS: fresh extended measurements, historical #26 retained |
| Five stress types and bounded infeasibility | PASS: separate operations/counts and requested versus distinct alternatives |
| Hard/exact constraints, lineage, provenance, comparison and small oracle | PASS: response checks, independent oracle and actual DB readback |
| Failures/partial/timeout retention; fixed thresholds | PASS: reporting/negative tests; none occurred in these measured flows; no retries/relaxation |
| Separate fixed live quotation/synthetic flow, approval/PDF and No-award | PASS, including unavailable-Odoo/unconfigured-model stored reopening |
| Relevant transactional/live/history contracts | PASS: 54 initial passes plus 2 focused passes after user key renewal; original 401 failures and historical proof retained |
| Raw/summary/environment/runbook and explicit limitations | PASS: linked exports and this handoff; publication/browser/participant gates remain |

This evaluates deterministic controlled fixtures and sequential local warmed
latency. It does not establish arbitrary-instance scaling, concurrent-load SLA,
cold-start behavior, observed prediction accuracy, calibrated risk or real
business savings. Actor attribution remains a technical demonstration rather
than authenticated buyer identity; PDF does not create an Odoo PO. Historical
browser evidence remains separate. Unfamiliar-buyer usability is NOT ASSESSED.

Traceability: FR-V2-01–08/10–12, AC-V2-01–08/10–13, NFR-V2-02–06/08,
RQ-V2-01–07; see [evidence routing](T18_EVIDENCE_MATRIX.md). Chapter 7 owns measured
assessment; chapters 3/4/6 and conclusions retain only supported integration,
provenance/decision-flow findings and explicit limitations.

Review and publication remain user-controlled. No Drive edit, GitHub issue
mutation, commit, push, PR or merge is performed. The next independent capability
is [#28's real-stack Chromium smoke/recovery](https://github.com/SafarErik/odoo-procurement-decision-support/issues/28),
followed by #29 buyer/keyboard/mobile assessment and #30 consolidated conclusions.
Substantial modern UX/UI work and reassessment still precede final acceptance.
