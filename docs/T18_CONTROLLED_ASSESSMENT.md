# Controlled procurement-system assessment — T18 / #30

Date: 2026-10-11. Branch: `feature/T18-implementation`.
Assessed implementation: **`65acfbe9bf31d89f6ed5e3c94812ecf65a82764b`** (#29).
This report is an uncommitted documentation increment for
[issue #30](https://github.com/SafarErik/odoo-procurement-decision-support/issues/30),
part of [specification #25](T18_EVALUATION_SPEC.md). No runtime behavior changes.

## Conclusion and acceptance boundary

The implemented **controlled** system meets the functional AC-V2-01–13 outcomes
within their defined one-product, bounded read-only Odoo / explicit-terms /
separately synthetic-model scope. Independent small-instance allocation checks,
real persistence contracts, the fixed live chain, local browser flow and repeated
HTTP measurements support that conclusion. Each criterion below has its own
evidence and limits; neither the test count nor CI success is blanket acceptance.

All 72 local workload/operation p95 targets passed, with no measured failure,
missing timing or partial solver result. Source-informed agent tasks and bounded
feedback fixes passed their recorded checks. **Unfamiliar-buyer usability remains
NOT ASSESSED.** Owner sessions are PENDING; actual 200% browser text zoom is
NOT VERIFIED; screen-reader output is NOT ASSESSED. The current UI still has
observed navigation, hierarchy and focus defects/friction, and decision-context
risks that need participant assessment. Modern buyer-experience acceptance is
**OPEN**, and final product/thesis acceptance is **BLOCKED by the required later
UX/UI development and reassessment**. T19 remains thesis closure after that work.

The scoped T18 evidence/report can be reviewed independently of those later
gates, as agreed by the user. This does not waive an unverified interaction check,
validate novice usability or authorize issue closure, publication, Drive edits,
broader Odoo discovery, observed-model promotion or production deployment.

## Sources, revisions and executed gates

Canonical meanings were refreshed read-only from
[06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit)
(modified 2026-10-11 14:05:58 UTC) and
[04_RESEARCH_NOTES](https://docs.google.com/document/d/1wpglDSL8rMUCFADUhslrgtIRRcWVAdujoEncrDY9WmY/edit)
(14:06:30 UTC). Tables paraphrase their definitions in English, without redefining
identifiers. The official task remains reference **423.589/25/140**, routed through
[project alignment](agents/project-baseline.md). Drive still describes T17 PR #24
as open and retains earlier future-T18/user-PostgreSQL gate wording. Merged T17
and the following dated evidence supersede those status statements; their history
and canonical definitions are preserved. Drive was not changed.

The evidence codes used by every matrix row below resolve to dates, revisions,
executed gates and detailed artifacts here. All T18 executions occurred on
2026-10-11; historical component results retain their original dates.

| Code | Evidence / date / assessed revision | Actual executed gate and boundary |
| --- | --- | --- |
| E1 | [T13 handoff](T13_HANDOFF.md), [independent oracle and fault tests](../tests/test_t13_planning.py); implementation `eae712fb47e66e0dbbbb7eda1c091849ffb4bbcc`, 2026-10-01 | Historical actual CBC, constraints, deterministic ties, small exhaustive reference optima; these tests execute again in E7. Larger HTTP cases are not independent optimum proofs |
| E2 | [T14 handoff](T14_HANDOFF.md), [metrics/split/model record](T14_EVALUATION.json), [dataset](../tests/test_t14_dataset.py), [model](../tests/test_t14_model.py), [runtime](../tests/test_t14_runtime.py) tests; `32e117242b1dbdf58f2e38897942e13c6507e12a`, 2026-10-04 | Historical synthetic metrics; real offline training/reload/inference and leakage/artifact rejection recur in E7. No observed-history or calibration validation |
| E3 | [T15](T15_HANDOFF.md), [T17 full flow](T17_FULL_FLOW_HANDOFF.md), [approval](T17_HANDOFF.md), [PDF](T17_PDF_HANDOFF.md); cumulative merged baseline `ed4be413b11dc469307fc1bb1ed4bd6c16c17b88`, 2026-10-11 | Historical controlled API/live/manual-browser/approval/PDF proof; dates inside handoffs govern individual runs. Not a new #30 execution |
| E4 | [#27 handoff](T18_27_HANDOFF.md), [six-workload raw/summary export](T18_27_EVALUATION.json), [runbook](T18_27_EVALUATION_RUNBOOK.md); committed as `6082741e016c2e82dba3a5573e289a3bf8f76380` | Actual served HTTP/disposable PostgreSQL: 2,160 measured + 144 warm-up operations, exact business/lineage/provenance checks and database reconciliation. Runs began at `97afe03` with then-uncommitted code; report source hashes, not the entry SHA alone, bind what ran |
| E5 | [#27 separate live record](T18_27_LIVE_VALIDATION.json) and E4 handoff; same source hashes/commit as E4 | Fixed three-supplier read-only Odoo chain, alternative approval/PDF, separate No-award, stored-only reopening; 36 helper-PostgreSQL and 18 primary live contracts passed. Two initial history/security 401 failures retained; a separate user-key-renewal rerun passed both. Not one 56-pass execution |
| E6 | [#28](T18_28_HANDOFF.md), [browser evidence](T18_28_BROWSER_EVIDENCE.json), [#29 tasks/fixes](T18_29_BUYER_ASSESSMENT.md), [bound evidence](T18_29_BUYER_EVIDENCE.json); commits `b3cf8f351f69c2dbef095288137fb1ef213dad68` / `65acfbe9bf31d89f6ed5e3c94812ecf65a82764b` | Local real Reflex/FastAPI/PostgreSQL Chromium flow, immutable approval, actual PDF download, genuine GET/create/PDF outages/recovery; post-fix smoke 1 passed in 87.51 s. Informed-agent desktop/390/320-pixel and keyboard tasks; not human usability or hosted-browser proof |
| E7 | [#30 reconciliation and gate record](T18_30_CONSOLIDATION_EVIDENCE.json); current assessed SHA `65acfbe9bf31d89f6ed5e3c94812ecf65a82764b` | New read-only raw/summary/hash verification and 591 fast tests, 60 deselected in 103.93 s; Ruff 0.17 format (213 files)/lint, compileall, pip check and both credential-suppressed Compose configurations passed. No new service/live/browser execution |
| E8 | Exact E7 SHA: [Quality run 38172043161](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38172043161), [Container/API run 38172043167](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/38172043167) | Connector-verified successful jobs and steps: Python 3.11 fast gates; integration execution, Reflex compilation, technical named-volume persistence and cleanup. Job metadata is not evidence of every optional live fixture, browser execution or business-data volume persistence. This new report revision has not been published |

## Canonical functional / acceptance matrix

**PASS (controlled)** means the stated canonical outcome is supported within the
bounded implemented input/runtime. It does not mean every production instance,
UI quality attribute, observed prediction or arbitrary Odoo configuration passes.
E1–E8 supply the evidence link/date/revision and executed gate for each row.

| Functional / acceptance ID | Defined outcome and assessed scope | Evidence and executed gate | Outcome / limitation |
| --- | --- | --- | --- |
| FR-V2-01 / AC-V2-01 | At least three known Odoo suppliers plus explicit supplemental terms produce complete ERP-neutral input and field provenance; company/read-only boundary and fail-closed critical data | E3; E5 live group 2, context/identity/price/missing-term contracts; E7 negative API/input tests | PASS (controlled). Q is explicit, not RFQ quantity. Separate synthetic history; arbitrary discovery/native tiers and observed promotion remain outside validated scope |
| FR-V2-02 / AC-V2-02 | Interpreted historical metric with count/reference time; versioned target/features and leakage-safe reproducible split/training | E2 dataset/time/group/receipt tests; E5 separate history mapping; E7 actual pipeline gates | PASS (synthetic ML pipeline). Schedule adherence references Expected Arrival, not verified supplier promise. Live history is separately verified, not promoted into this fitted model |
| FR-V2-03 / AC-V2-03 | Saved Decision Tree produces class/score, versions, metrics and interpretable path; ML does not allocate or finalize | E2 measured held-out metrics/artifact/tree tests; E4 actual saved inference; E7 actual training/reload | PASS (controlled synthetic). No calibrated probability, real predictive superiority or operational validity claim |
| FR-V2-04 / AC-V2-04 | Eligibility separated from hard MOQ/absence, availability/capacity, dates, quantity-validity, count and concentration; constraints never silently relaxed | E1 independent small references/negative cases; E4 every returned allocation checked; E7 CBC gates | PASS (bounded numeric/quantity contract). Unsupported precision/context is rejected rather than relabelled infeasible |
| FR-V2-05 / AC-V2-04 | Integer multiple-supplier allocations sum to approved Q; output validated with honest solver status | E1 exhaustive optimum; E4 exact sums/constraints/metrics and DB readback; E7 | PASS (controlled). Larger feasible workloads supplement rather than replace independent small optimum evidence |
| FR-V2-06 / AC-V2-05 | Minimum-cost reference plus distinct epsilon-bounded alternatives with exact cost/premium/exposure/quantities; honest no-distinct result | E1 alternative/deduplication oracle; E4 1/3-epsilon workloads; E6 displayed quantities | PASS (controlled). Three epsilon requests can yield two distinct alternatives; a duplicate is not an invented plan or failure |
| FR-V2-07 / AC-V2-06 | Same input/configuration gives stable plan/explanation, input-order independence and documented tie/tolerance policy | E1 permutations/ties; E2 reproducible tree/path/artifact; E4 repeated fixture outcomes; E7 | PASS (fixed runtime/configuration). Different saved timestamps/UUIDs are not deterministic plan failures; cross-solver/version binary equality not asserted |
| FR-V2-07 / AC-V2-07 | Proven exclusions/binding constraints/infeasibility explanations; invalid input, technical failure and unproven optimum never become false plans/infeasible claims | E1 invalid/numeric/solver/partial fault tests; E4 saved capacity shortfall; E6 infeasible UI; E7 | PASS (bounded). Measured runs contained no partial proof; fault tests supply that boundary. Infeasible comparison currently obscures the preserved base cost (UX29-07) |
| FR-V2-08 / AC-V2-08 | All five explicit disruptions rerun same MILP against immutable original base; compare allocation/cost/exposure/status | E4 all scenario cells and lineage/delta/provenance checks; E5 fixed live chain; E6 all-five agent tasks | PASS (controlled). Combined change is demand plus one supplier's capacity/price. Changed-demand totals are not like-for-like savings; simulated price is not fresh Odoo fact |
| FR-V2-09 / AC-V2-09 | API-only Reflex displays inputs, evaluation/tree, plans/allocations/chart, stress/infeasible/loading/errors, human decision and PDF | E3 controlled manual hybrid browser; E6 real local Chromium plus desktop/narrow/keyboard tasks and feedback recheck; E8 compilation only | PASS (controlled functional UI); interaction assessment LIMITED. Owner/novice, browser text zoom and screen-reader claims remain pending/unverified; modern UX still OPEN |
| FR-V2-10 / AC-V2-10 | Versioned immutable V2 base/child plus compatible V1 retrieval; exact GET/replay stored-only; safe conflict/contention/rollback | E5 36 real helper-DB contracts, unavailable-upstream/unconfigured-model reopening; E4 exact stored identity/readback; E6 reopening; E7 | PASS (technical persistence). Concurrency proof is transactional correctness, not a load SLA. Database-reset tests use disposable helper storage, never owner/Odoo data |
| FR-V2-11 / AC-V2-11 | One explicit saved valid original-base plan finalized once with audit; different choice/reason and separate No-award; replay consistent, conflicting/concurrent intent protected | E3 approval; E5 actual PG contention/rollback and separate No-award; E6 alternative reason validation, keyboard No-award/reopen; E7 | PASS (controlled technical decision). Actor text does not authenticate identity. No manual allocation editing is offered; child scenarios cannot be approved |
| FR-V2-12 / AC-V2-12 | Backend PDF matches immutable approved content, required terms/identities/quantities/cost/audit/provenance; stable view/download without upstream work; ineligible states denied | E3 PDF content/Unicode/fault proof; E4 first/cached bytes/hash; E5 content/PG gates and No-award 422; E6 real download/PDF fault/retry; E7 | PASS (approved-document contract). No automatic Odoo PO/legal order. Cached byte identity is not arbitrary fresh-render byte equivalence; recorded font/size limits remain |
| Cross-cutting / AC-V2-13 | Reproducible local Podman/Compose chain: read-only Odoo + terms → saved synthetic evaluation → MILP alternatives → stress → approval → reopen/PDF, with runtime/data limits | E3 complete hybrid manual browser; E5 fresh live HTTP chain/storage; E4 repeated synthetic HTTP; E6 separate browser/tasks; E7/E8 | PASS (defined controlled chain), not one new #30 all-environment execution. First-time/operational/production acceptance remains separate |

## Canonical nonfunctional matrix

| ID | Defined outcome / assessed scope | Evidence and executed gate | Outcome / limitation |
| --- | --- | --- | --- |
| NFR-V2-01 | Separate ERP, assembly/provenance, ML, ERP-neutral model/MILP, solver, storage, PDF and API-only UI | E1/E2/E3 documented ports/adapters, E7 source-diff review and existing runtime/import checks | PASS (implemented structural boundary). No framework/solver/library replacement experiment was performed |
| NFR-V2-02 | Retained inputs/versions/seeds/configuration/tolerances/ties and stable explanation; immutable saved state | E1/E2 determinism, E4 input/model/policy/CBC/source hashes plus exact DB readback, E6 identity/replay, E7 hash reconciliation | PASS (controlled reproducibility). Hardware/version/order and local artifacts matter; timing is not expected to be identical |
| NFR-V2-03 | Reference times, counts, sources/split; train-only learning; synthetic/observed distinction, no leakage | E2 time/group/receipt split and held-out isolation tests; E4 explicit synthetic manifests; E5 separate live history/provenance; E7 | PASS (synthetic integrity). No observed prediction validity or empirically established quantity independence |
| NFR-V2-04 | Independently testable core/ML/solver; contract/integration/full-flow tests with reference optima and invariants | E1 independent oracle, E2 actual model tests, E4 HTTP, E5 real PG/live, E6 browser, E7 fast, E8 hosted steps | PASS (bounded tested seams). One local Chromium smoke, not exhaustive browsers/UI coverage; participant evidence absent |
| NFR-V2-05 | Bounded company-scoped read-only Odoo access, separate secrets, stable errors and honest state distinctions | E5 primary live + renewed dedicated projection/direct-access-denial tests; E6 server-only credentials/real faults; E7 trust/negative tests | PASS (verified PoC identities/configuration). Initial 401 was a real failure, later resolved; no production IAM/RBAC or indefinite credential availability claim |
| NFR-V2-06 | Immutable snapshots, atomic finalization, replay/contention protection, readable V1/V2, approved-document equality | E5 actual PG races/post-flush rollback/immutability; E4 exact case/decision/document reconciliation; E6 downloaded bytes; E7 | PASS (technical integrity). Caller attribution is not legal/authenticated approval; race correctness is not a throughput benchmark |
| NFR-V2-07 | Python web UI is replaceable HTTP client; no client-side ERP/DB/training/solver logic | E3 architecture, E6 real Reflex HTTP flow, E7 unchanged backend/source boundary and frontend contracts | PASS (current architecture). Replacement is supported by interface separation, not proved by implementing a second UI |
| NFR-V2-08 | Documented local Podman/Compose/runtime/dependencies and measured interactive operations at pre-agreed sizes/thresholds | E4 six workloads/72 p95 targets, E5 live reproduction, E6 browser runbook, E7 configs/runtime, E8 hosted steps | PASS (bounded warmed local protocol). No cold-start, concurrent-load, physical mobile, hosted browser, production SLA or human-task-time result |

## Reconciled measurements and failures

E7 read all six bound **original raw reports**, verified their SHA-256, compared
every exported timing/outcome/method/path/key/status and full-value template hash,
and independently recomputed medians, maxima and nearest-rank p95. All 2,304
observations match the earlier exports: **144 warm-up and 2,160 measured**.
Each of 72 cells has exactly 30 timed successful measurements, zero pending,
not-attempted, failed or untimed operations. The 29th sorted sample is p95;
warm-ups are excluded and no unsuccessful timing is discarded. Expected
`infeasible` is a proven result, not a failed request. There were no partial,
timeout or technical solver results in this population; existing fault tests
and the evaluator's failure-accounting tests cover their handling, not their
performance under real large-instance failure.

The targets are unchanged: create/all scenarios ≤5 s, stored GET/exact replay/
approval/cached PDF ≤1 s, first PDF ≤3 s. No pooled percentile across operations
or sizes is reported. Requested epsilons are `0.1` or `0.05/0.1/0.2`.

| HTTP operation / observed p95 seconds | 3/1 | 3/3 | 5/1 | 5/3 | 10/1 | 10/3 | Target s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Create | 0.613187 | 1.094228 | 0.822461 | 1.401238 | 1.326263 | 2.453291 | 5 |
| Supplier outage | 0.643561 | 1.032736 | 0.861725 | 1.426288 | 1.317848 | 2.411778 | 5 |
| Capacity reduction | 0.566386 | 1.050906 | 0.831972 | 1.529521 | 1.374312 | 2.416080 | 5 |
| Demand increase | 0.543678 | 1.024415 | 0.838110 | 1.431405 | 1.527524 | 2.405865 | 5 |
| Price increase | 0.601633 | 1.004679 | 0.818616 | 1.461800 | 1.333048 | 2.791729 | 5 |
| Combined | 0.658635 | 1.118114 | 0.846259 | 1.535536 | 1.319815 | 2.544175 | 5 |
| Infeasible | 0.285847 | 0.274829 | 0.282883 | 0.304503 | 0.231848 | 0.263184 | 5 |
| Approval | 0.250270 | 0.237032 | 0.275900 | 0.301873 | 0.288199 | 0.241109 | 1 |
| Stored GET | 0.209078 | 0.222418 | 0.191020 | 0.264684 | 0.238886 | 0.260503 | 1 |
| Exact replay | 0.272189 | 0.260915 | 0.289521 | 0.274940 | 0.414181 | 0.362967 | 1 |
| First PDF | 0.232733 | 0.210357 | 0.313802 | 0.289403 | 0.367502 | 0.372053 | 3 |
| Cached PDF | 0.212172 | 0.198034 | 0.212448 | 0.212160 | 0.232481 | 0.231284 | 1 |

The largest p95 is 2.791729 s for 10/3 price increase; its observed maximum is
2.816472 s. Other medians/maxima remain in E4, all independently reproduced.
This is descriptive success at six fixtures on one local runtime, not a
population confidence guarantee or a randomized scaling experiment.

Python 3.11.16/FastAPI 0.142.2, PuLP 3.3.0/CBC 2.10.3, scikit-learn 1.8.0,
PostgreSQL 16.15 and ReportLab 4.4.10 ran on a Windows host with 14 logical CPUs
and 33,765,654,528 bytes RAM; existing WSL Podman VM 7 CPUs/2 GiB. Existing Odoo
containers were co-resident. Workloads ran sequentially in fixed 3/1 → 3/3 →
5/1 → 5/3 → 10/1 → 10/3 order on the same warmed API/accumulated database;
no competing agent-initiated training/tests/solves. Two full warm-ups preceded
30 flows per workload. Offline preparation, service startup, validation/checkpoint
IO and browser display are outside HTTP timing; first PDF is a fresh artifact
in a warm process. Windows forwarding used an owned localhost SSH tunnel.

E5's fixed live chain took **7.481893 s in one descriptive HTTP demonstration**,
not a percentile or part of the synthetic timing pool. E6's 87.51 s smoke includes
setup/compilation/teardown. Its six agent-task clocks include tool/reasoning/fault
setup and are not human task times. E4/E5 reconciled all 1,352 evaluation cases,
194 decisions and 193 documents with actual helper PostgreSQL; three earlier
integration-fixture cases and one decision/document were identified separately.

Earlier failures remain evidence: E5's two real HTTP 401 history/security failures
were resolved only after user key renewal and a separate two-test PASS; E6's first
fast attempt had 183 temp-fixture setup errors/408 passes and its complete local-temp
rerun passed. #28 development assertions and #27 harness corrections remain in
their dated handoffs. Before the six-workload execution, a focused #27 test caught
an incorrect evaluator source-type literal; the existing synthetic constant fixed
it before measurements. Those unit/development runs are not the agreed 2+30 HTTP
workload population. None was silently removed from the measured population or
counted as a successful initial run. The existing Starlette TestClient warning
remains in E7; no dependency upgrade was introduced.

## Research-question answers

These answers use the refreshed canonical RQ wording, not a new research scope.

| RQ | Evidence-based answer | Limit / defensible thesis statement |
| --- | --- | --- |
| RQ-V2-01: bounded read-only ERP input versus ERP-neutral ML/planning | Yes within the controlled interface: E3/E5 read selected quotations, validate company/context/expectations and keep explicit terms/provenance outside the core; stored-only sentinels and source rejection protect the seam | Implemented side-by-side separation, not tested arbitrary Odoo discovery or another ERP. Live quotations do not turn generated ML history into observations |
| RQ-V2-02: reproducible, interpretable tree on leakage-safe controlled data | E2/E7 use 240 synthetic observations, 160 train / 80 test, disjoint supplier groups/unique receipt evidence and a 2026-02-15 split. Seed 17 model exposes class/leaf/path and trusted versioned reload. Held-out confusion matrix `[[23,1],[0,56]]`; accuracy 0.9875, macro precision 0.991228, recall 0.979167, F1 0.984937; class support 24/56 | Metrics describe an intentionally constructed noisy synthetic label mechanism; no KPI superiority, observed prediction accuracy, calibrated risk or empirical quantity independence. Metrics are E2's retained result, not newly measured by #30 |
| RQ-V2-03: correct integer constraints and small-reference optimum | E1's exhaustive small cases agree with actual CBC minimum/epsilon plans, including constraint variants/ties; E7 re-executes them. E4/E5 independently validate returned sums, eligibility/bounds/count/share and exact metrics | Bounded numerical correctness with honest unsupported/partial states. Larger measured cases do not supply an independent optimum proof or unlimited solver scalability |
| RQ-V2-04: allocation/cost/exposure trade-off | In E6's synthetic demand 10, EUR 102 allocates S184 4/S226 6 with exposure `24661/25000`; EUR 109 allocates S161 8/S184 2 with `9661/50000`, premium `7/102`. E4 one epsilon yields one distinct alternative; three yield two, with 20% deduplicated to the 10% plan. E5 live-quotation hybrid gives USD 1,850 versus 2,200 (+350, ≈18.9%) with separately synthetic exposure | Descriptive cost/exposure trade-offs under explicit constraints, not real procurement savings or risk reduction. Distinct-plan count is fixture-specific |
| RQ-V2-05: response to defined disruptions/infeasibility | E4/E5 exercise all five types plus infeasible, unchanged original-base lineage, exact deltas/provenance. E6's EUR 102 base becomes 106 outage, 103.5 capacity, 123 demand, 106 price, 128 combined; demand 1000 yields no plan | Simulated facts must be labelled; changed-demand totals differ in quantity. Invalid input/solver failure is not infeasible. Infeasible UI baseline visibility needs UX29-07 improvement |
| RQ-V2-06: tree → plan → human choice → document traceability | E3–E7 preserve model/path, snapshot and selected-plan/content hashes, one-time audit/No-award, stored-only GET/replay, stable PDF reference, actual downloaded byte/hash identity and fault recovery. Real PG transactions cover conflicts/races/rollback | Technical audit attribution, not authenticated/legal authority; no Odoo order write. PDF representation limits remain; cached bytes equal saved artifact, arbitrary new renders need not be binary-identical |
| RQ-V2-07: complete local PoC runtime and reproduction limits | E4/E7 reproduce 72 passing operation/workload p95 cells; E5 separately reproduces the fixed live chain; runbooks bind prerequisites/configuration/model/input/runtime/hardware/ownership/cleanup | Warm sequential loopback evidence with 30 samples per cell; no cold-start/concurrent throughput/production SLA, hosted-browser or novice-task performance. Owner setup and available fixtures remain prerequisites |

## Outstanding gates and the next buyer-visible increment

| Gate / finding | Current status and needed action |
| --- | --- |
| Controlled HTTP target failures / partial proofs | None in E4 population; no threshold relaxation. Future failures must remain FAIL with their missing/failed sample accounting |
| Dynamic PDF error/save feedback | UX29-01/02 FIXED and affected E6 DOM/tasks/real-stack smoke rechecked; speech is not established by roles alone |
| Keyboard focus after completed save | UX29-06 OPEN observed defect: focused control removed, focus falls to body. Keyboard completion was possible, but continuity needs repair and recheck |
| Infeasible baseline presentation | UX29-07 OPEN observed defect/friction: original cost hidden as “Not comparable”. Preserve original facts and separate absent scenario metrics from undefined deltas |
| Actual browser text zoom / screen reader | NOT VERIFIED / NOT ASSESSED. Owner follows [#29's run sheet](T18_29_BUYER_ASSESSMENT.md#owner-and-unfamiliar-buyer-sessions--pending-run-sheet), in a regular browser at 200%, and records outcome/focus/reflow; PDF zoom is separate. Keep gate open until actual evidence exists |
| Owner and novice task sessions | Owner PENDING; 3–5 unfamiliar procurement participants PENDING, novice usability NOT ASSESSED. Record completion, assistance, mistakes, human time and comprehension. User accepted their absence as a scoped T18 limitation, not validated usability |
| Modern UI/UX and final acceptance | OPEN / BLOCKED respectively by required design/development/reassessment. Plan next increment; do not treat #30 report completion as product closure |
| Observed model, arbitrary quotation selection, broader combinations, production IAM/deployment | Separate scope/data-readiness decisions, not hidden T18 implementation blockers or implied approval to build |
| Publication, Drive and issue closure | This documentation revision needs user review/publication/new-SHA CI. No parent #25 mutation/closure, merge or Hungarian Drive write is performed here |

The next substantial increment should enable a procurement buyer to **find or
reopen a recognizable case, understand a plan and its alternatives, test a
disruption and deliberately record a choice**, with a coherent modern responsive
visual system. Use [#29's evidence-backed backlog](T18_29_BUYER_ASSESSMENT.md#observed-findings-and-prioritized-uxui-follow-up)
for reproduction details; the following proposed order preserves buyer impact.
It is a planning recommendation, not newly published tickets or accepted ADRs.

| Proposed slice / priority | Buyer-visible outcome and reassessment |
| --- | --- |
| Entry, return journey and responsive hierarchy / P1 (UX29-03/04/10) | Recognizable saved-case navigation and clear next action; purposeful typography/spacing/hierarchy, less developer-oriented guidance, concise visible synthetic boundaries. A novice finds/opens the intended case without a supplied UUID or developer assistance. Any new list/search API needs its own scoped contract |
| Compare → deliberate choice / P1 (UX29-05) | Chosen quantities, exact cost/premium/exposure and irreversible decision context stay near explicit approval/No-award. Buyer explains the chosen trade-off and declines on a separate base without unintended approval |
| Scenario context, keyboard continuity and safe recovery / P2 (UX29-06/07/08) | Original base facts stay visible, demand-change semantics clear, focus/announcements purposeful; pending/retry wording understandable while exact intent/key stays fixed. Reassess feasible/infeasible and genuine GET/create/PDF outage tasks with keyboard/200% zoom/narrow width |
| Document access/navigation / P2 (UX29-09) | Approved summary and navigation make the selected allocation/date/audit easy to find; retain exact approved content/provenance and real artifact download. Reassess desktop/narrow/zoomed/keyboard PDF tasks |

Agree workflow/design and explicit completion criteria, implement bounded slices,
then run owner and unfamiliar-participant tasks and repeat affected smoke/integrity
checks. Validate physical mobile/touch and assistive technology separately where
needed. Record findings and fixes instead of substituting screenshot preference
for evidence. Preserve Plans/What-if/Suppliers/Audit, exact values, original-base
semantics, read-only Odoo and explicit synthetic/approval limits. Do not renumber
T19; necessary UX development/reassessment precedes thesis closure.

## Reproduction, thesis use and handoff

Use [#27's runbook](T18_27_EVALUATION_RUNBOOK.md) for offline preparation, the
six served HTTP workloads and separate live check, [#28's current browser runbook](T18_28_BROWSER_RUNBOOK.md)
for optional Chromium tooling/isolated service lifecycle, and [#29's run sheet](T18_29_BUYER_ASSESSMENT.md)
for pending human/interaction checks. Every reset/runtime test uses an owned
disposable helper project. Preserve owner models, application cases, Odoo/data,
`.env` and the existing Podman machine; never use broad process kills or reset
tests against owner storage. Large raw snapshots/traces stay ignored locally;
repository records and E7 hashes bind selected artifacts without duplicating them.

E7 established current relevance: only `frontend/planning/page.py` and
`decision.py` changed in production since E4/E5, adding feedback roles. Evaluator,
fixture/live tools and current post-fix browser/task source hashes match retained
evidence; installed measured dependency versions and the actual CBC binary hash
also match E4. HTTP/model/solver/DB/PDF behavior is unchanged. E6 already reran the
affected interaction and smoke; E7 reran fast gates. Repeating all timed, live and
browser workloads in #30 would add no justified evidence, so none was started.
Existing source/artifact history remains intact. No new dependency, migration,
CI, runtime code, service start, Odoo access, GitHub mutation or Drive edit.

Thesis structure follows **problem → decision → implemented behavior → evidence
→ limitation → chapter relevance**: chapter 7 owns the matrices, measurements,
RQ answers, faults and validity limits; chapters 3/4/6 may use supported
requirements/integration/modularity/decision/document behavior; chapter 5 retains
the validated small MILP and controlled tree interpretation. Conclusions/further
work derive from the RQ rows and open UX/observed-model gates. Institutional
literature/writing/submission work remains T19, not delivered by passing software.

**Handoff:** #30's consolidated report and source/raw/summary reconciliation are
delivered for review. No new controlled functional AC or latency failure was
found; interaction and human-evidence limits remain open exactly as recorded.
The user controls commit/push/merge, issue closure and separately authorized
Hungarian Drive synchronization. Next product work is the substantial buyer
UX/UI increment with reassessment, before final acceptance and T19 closure.
