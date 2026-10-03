# T13 — V2 domain and application-ready MILP core handoff

## Result and repository state

**IMPLEMENTED; LOCAL AND HOSTED CHECKS VERIFIED; PR #15 OPEN / NOT MERGED.** The bounded
one-product core is ready for application composition. It is not a completed V2
workflow or a validated ML predictor. Current Drive 00/02/06/07 were read live on
2026-10-03. They record the official thesis task assignment as completed and
recorded in the issued, approved task sheet (dated 2026-09-22, reference
423.589/25/140); it is no longer TO BE DRAFTED. Subsequent implementation and
evaluation must remain traceable to that assignment and the accepted V2 baseline.
The original pre-implementation Drive/ADR reads and entry evidence remain in the
[design](T13_V2_MILP_DESIGN.md).

- Branch: `feature/t13-v2-milp-core`.
- Entry base and remote main, reverified on 2026-10-03:
  `71396e8924f6a1f60daf8b45f02861adf21a25e5`.
- Implementation commit: [`eae712fb47e66e0dbbbb7eda1c091849ffb4bbcc`](https://github.com/SafarErik/odoo-procurement-decision-support/commit/eae712fb47e66e0dbbbb7eda1c091849ffb4bbcc),
  `Add T13 V2 MILP planning core`, committed and pushed on 2026-10-01.
  Local HEAD, remote branch and PR head matched this commit before this correction.
- PR [#15](https://github.com/SafarErik/odoo-procurement-decision-support/pull/15),
  `Add T13 V2 MILP planning core`, is open, non-draft and unmerged, targeting `main`.
  Implementation Quality and Container/API runs succeeded; evidence is below.
- This 2026-10-03 documentation-only follow-up changes only `docs/T13_HANDOFF.md`.
  Its commit follows the implementation commit; after publication the branch/PR
  HEAD identifies this documentation revision, not the entry base or new core code.
  The implementation evidence below remains attributed to `eae712f`; subsequent
  documentation-head CI must be reported separately rather than assumed green.
- PR [#14](https://github.com/SafarErik/odoo-procurement-decision-support/pull/14)
  was experimental and unmerged at the 2026-10-01 entry check. Its combined head
  `b65347b` was used as reference, including the ML external-score extension.
- Pre-existing apparent Reflex lockfile changes remain preserved in stash
  `bb904d26d5e85d6775187ac59f6940881566f493`; content diffs were empty after
  line-ending normalization. No stash drop/pop was performed.

Historical entry on 2026-10-01: **GO for local implementation** followed remote, working-tree,
legacy and existing hosted checks. Detached-main fast baseline was 271 passed /
37 deselected on Python 3.14.7. T12 PR #13 pre-merge head `e074e2e` had Quality
35782454967 and Container/API 35782454981 success; the squash main commit itself
returned no hosted status. PR #14's runs 36756499541 and 36756499578 succeeded but
omitted optional optimization/ML dependencies, so did not prove full V2 runtime.

## Implemented boundaries and files

| Files | Responsibility |
| --- | --- |
| `decision_core/planning/models.py`, `__init__.py` | Frozen/slotted one-product requirement, supplier terms, policies, external coefficient validity, allocations, plans, explanations and statuses |
| `decision_core/planning/rules.py` | Exact business bounds, risk coverage, necessary infeasibility proofs, output checks and deterministic explanations |
| `decision_core/planning/planner.py` | ERP-neutral solver port, minimum/epsilon orchestration, deduplication, shared time budget, partial results |
| `optimization_adapter/__init__.py`, `pulp_cbc.py` | Provisional pinned PuLP/CBC model, sequential objectives, runtime checks, integer encoding and exact primal verification |
| `application/procurement_planning.py` | Thin application entry point and separate external-score definition/assessment/validity context |
| `tests/test_t13_planning.py` | Business/oracle/reference, invalid-input, alternative, determinism and orchestration tests |
| `tests/test_t13_solver_runtime.py` | Required actual executable/version/solve gate and solver fault tests |
| `tests/test_t13_architecture.py` | Solver/domain/application dependency separation and mandatory Python 3.11 CI contract |
| `pyproject.toml`, `.github/workflows/quality.yml` | Required `pulp==3.3.0`, packaged adapter, compilation and explicit runtime smoke in `quality` |
| `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_LOG.md`, this handoff and design | Narrow scope reconciliation, usage, evidence and downstream handoff |

Reusable spike portions: integer/binary activation, minimum-cost reference,
external risk coefficients, epsilon cost cap, exact output checks and sequential
deterministic tie-breaking. The full spike branches, UI, ML training and reports
were not merged/copied into runtime. Historical reports remain in their original
commits/branches and PR #14. No existing WSM exports, API schemas/routes, Odoo
adapter, persistence models/migrations or snapshot serializers were changed.

## Input and solver contract

One product and approved positive integer demand Q; common explicit currency and
indivisible quantity unit; one offer per unique supplier. Every supplier supplies
known price, capacity, Boolean availability, hard MOQ or `MinimumOrder(None)` for
explicit absence, required/promise dates, and inclusive positive-use price/delivery
quantity ranges. Unknown critical fields fail closed even for unavailable suppliers.
Capacity below Q allows a partial allocation. No currency/unit conversion, price
tiers, multiple products, periods or delivery slices are inferred.

Use `PlanningCommand` and `create_procurement_plans(command, solver)` from
`application.procurement_planning`; compose `PulpCbcSolver` outside that module.
The core also exposes `plan_procurement(request, solver)` for ERP-independent use.
No backend endpoint or concrete solver dependency was added to the application.
Typed invalid inputs raise `InvalidPlanningInput` during construction; use-case
validation and solver outcomes return explicit `PlanningResult` statuses.

External coefficients are finite Decimal [0,1], higher means less desirable risk
exposure, not failure probability. Weighted exposure is exactly `sum(r_i*x_i)/Q`.
Epsilon alternatives require complete coefficients for otherwise usable suppliers;
each validity range covers that supplier's entire allowed positive allocation
range. T13 neither extrapolates a quantity-100 ML score nor narrows the physical
feasible set to fit its score. Application context records definition, assessment,
validity reference and controlled-fixture labeling. These references are assertions
to audit, not proof of predictive validity.

Explicit cost-only requests use an empty epsilon tuple. Missing/partial scores
never produce zero exposure; exposure is absent unless the applicable scores are
complete. Cost-only does not secretly optimize risk. The minimum-cost reference is
stable; alternatives minimize exposure under its epsilon cap, then cost, then
lexicographically maximize quantities by ascending supplier ID. Repeated epsilons
and allocations deduplicate; `plan_index=0` aliases the reference and later indices
refer to distinct alternatives. No invented "balanced" recommendation is returned.

Money is exact Decimal; ratios/premiums/exposure are exact Fraction. No permanent
cents/four-decimal or 50-supplier business rule. The adapter dynamically scales
objectives to reduced integers and applies an infrastructure budget of 2^40 for
integer RHS/coefficient/objective envelopes and a 64-digit/absolute-exponent Decimal
representation limit. Unsupported numeric encoding is INVALID_INPUT, not
infeasibility. These configurable limits are detailed in the design.

PuLP 3.3.0 bundles CBC 2.10.3. Config: one thread; both seeds 17; zero relative and
absolute gap; elapsed time; integrality tolerance 1e-6; default shared 30-second
request budget across all solver phases. Both problem and solution must report
optimality. Every variable, business bound, integer model constraint and objective
lock is checked exactly; infeasible or nonintegral incumbents never become plans.

| Status | Meaning |
| --- | --- |
| `invalid_input` | Missing/incompatible business context, invalid score coverage or unsupported numeric encoding |
| `optimal` | All requested phases proved optimal and returned verified canonical allocations |
| `infeasible` | Necessary capacity/count proof or CBC proof for the original business feasible set |
| `no_proven_optimum` | Budget exhausted or solver did not prove optimum; no plan for that phase |
| `solver_error` | Missing/failed executable, corrupt output, or contradictory later infeasibility |

A failed alternative can retain an already verified reference and earlier verified
alternatives; overall status remains non-optimal and the failed run has no plan
index. Remaining epsilons are unattempted after that failure. Explanations separate
hard exclusion from zero due to optimization/tie-breaking and show allocations,
effective bounds, slack/binding, concentration/count and premium. Interacting
infeasibility is a solver proof, without a claimed IIS or causal sensitivity analysis.

## Reproducible reference results

`tests/test_t13_planning.py` supplies explicit controlled facts and an independent
small-instance exhaustive oracle. In its three-supplier Q=10 fixture, prices
2/3/4 and capacities 6/6/10 give A=6, B=4, C=0 and minimum cost 24. A cannot cover
Q alone and remains usable. Commercial and policy constraints are also checked
against the oracle, including valid input with interacting MOQ infeasibility.

The latest spike's external-score fixture is retained without training: Q=100,
prices 10/10.5/11, capacities 60/80/100, concentration 0.8, coefficients
0.2921/0.2921/0. Controlled fixture validity covers all allowed quantities; this is
not an assertion that the old quantity-dependent ML model has this validity.

| Run | A/B/C | Cost | Premium | Weighted exposure |
| --- | --- | --- | --- | --- |
| Minimum cost | 60/40/0 | 1020 | 0 | 0.2921 |
| Epsilon 0.02 | 60/0/40 | 1040 | 1/51 | 0.17526 |
| Epsilon 0.05 | 29/0/71 | 1071 | 0.05 | 0.084709 |

These are synthetic score demonstrations. Equal-score cases deliberately return
no distinct alternatives. Input permutations preserve plans and explanations.

## Historical local verification on 2026-10-01

This records the original local handoff before the implementation commit was
published and PR #15 opened. The earlier draft-assignment and uncommitted/hosted
unverified observations were historical state, superseded by the current record
above. Local results and limitations below are preserved, not rerun or relabeled
by this documentation correction.

Python 3.11 was initially unavailable. A managed Python 3.11.16 runtime was installed
under ignored `.venv/t13-python` with uv `--no-bin --no-registry`; the isolated
`.venv/t13-check` environment installed `.[frontend,dev]`. No global dependencies,
PATH or registry changes. The original Python 3.14.7 environment remains available.

```powershell
.\.venv\t13-check\Scripts\python.exe --version
.\.venv\t13-check\Scripts\python.exe -m ruff format --check .
.\.venv\t13-check\Scripts\python.exe -m ruff check .
.\.venv\t13-check\Scripts\python.exe -m compileall -q application backend frontend decision_core odoo_adapter optimization_adapter persistence migrations infra/odoo/addons/t7s_inventory_history_projection
.\.venv\t13-check\Scripts\python.exe -m pytest -m "not integration and not e2e" -v -o cache_dir=.venv/t13-check/pytest-cache
.\.venv\t13-check\Scripts\python.exe -m pip check
git diff --check
```

| Gate | Actual evidence |
| --- | --- |
| Python 3.11 MILP runtime | PASS: Python 3.11.16, PuLP 3.3.0, executable CBC 2.10.3, actual reference solve |
| Fast suite incl. legacy | PASS: 328 passed, 37 deselected in 10.47s; one upstream Starlette deprecation warning |
| Targeted T13 on existing Python 3.14.7 | PASS: 57 passed in 7.24s; sandbox cache warning, no test failures |
| Formatting / lint | PASS: final check reported 114 Python files formatted; Ruff 0.16.9 |
| Compilation / dependency consistency / whitespace | PASS; no broken requirements |
| Local Podman Compose | FAILED: running-machine socket at 127.0.0.1:64087 refused connection; `config --quiet` could not complete |
| Service-dependent integration / controlled Odoo fixtures / browser E2E | SKIPPED: unavailable services; no service start or Odoo mutation |
| Hosted T13 Quality / Container/API at the original local handoff | UNVERIFIED at that stage: before the implementation commit and PR publication; later hosted results are recorded separately below |

The required quality workflow now installs the solver as a required dependency and
executes its runtime gate on Python 3.11; no import-or-skip fallback. The legacy
suite includes WSM, HTTP contracts, T11/T12 serialization, stored-only replay/retrieval
and error masking regressions. The local fast suite did not substitute for the
unavailable local PostgreSQL/Odoo service tests.

## Hosted implementation evidence, reverified on 2026-10-03

GitHub PR metadata, workflow conclusions, job steps and decoded logs were read
for implementation commit `eae712fb47e66e0dbbbb7eda1c091849ffb4bbcc`. Both runs
executed on 2026-10-01; this is a later evidence read, not a new local test run.

| Gate | Actual hosted evidence |
| --- | --- |
| [Quality run 36835570151](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/36835570151), job 110282045586 | SUCCESS on Python 3.11.16: 328 passed, 37 deselected, one warning in 2.64s |
| Required actual solver gate in the same Quality run | PASS: 5 passed in 0.08s, including `test_required_pulp_and_actual_cbc_runtime`; required PuLP 3.3.0/CBC runtime execution, no dependency skip |
| Formatting / lint / compilation / dependencies / whitespace in Quality | PASS: 114 files already formatted, lint passed, compile step succeeded, no broken requirements, `git diff --check` step succeeded |
| Hosted Docker Compose configuration in Quality | PASS for Odoo and isolated persistence configuration with synthetic credentials; separate from the earlier FAILED local Podman check |
| [Container/API run 36835570266](https://github.com/SafarErik/odoo-procurement-decision-support/actions/runs/36835570266), job 110282046528 | SUCCESS: 17 passed, 20 skipped, 328 deselected, one warning in 2.22s |
| Service and persistence scope of that integration run | PASS: isolated T11/T12 PostgreSQL schema/snapshot/idempotency/concurrency/HTTP-flow tests plus FastAPI health/decision and Odoo HTTP service checks |
| Reflex frontend export and technical named-volume persistence | PASS as job steps; compilation and synthetic volume-marker survival, not browser E2E or an Odoo business-scenario persistence proof |
| Controlled live Odoo contracts in that integration run | SKIPPED: all 20 cases in `tests/integration/test_live_odoo_contract.py`, including RFQ/read-only/schema/T5, controlled T6, T7-S and T8 contracts |

CodeRabbit reported SUCCESS for the same implementation commit. The successful
workflow conclusions do not turn their 20 skipped tests into passes. The original
local Podman socket failure and local service/browser skips remain unchanged;
hosted Linux/Docker checks ran in a different environment. A complete controlled
Odoo V2 E2E flow, ML training/inference on Python 3.11 and the full V2 workflow
remain OPEN.

This documentation correction verifies existing evidence and uses local
`git diff --check`; it does not rerun local runtime/services or change code,
Drive or Odoo. Its commit and latest CI state are reported separately after push.

## Acceptance mapping

Statuses below describe the bounded core verified locally and by hosted checks on
implementation commit `eae712f`, still in open/unmerged PR #15. They do not signify
completion of the entire V2 system or execution of skipped live contracts.

| Requirement / criterion | Status | Evidence and limit |
| --- | --- | --- |
| FR-V2-04 hard eligibility/constraints | IMPLEMENTED / VERIFIED | Explicit unknown-input rejection; availability/date, MOQ, capacity, max count, concentration and both commercial ranges; no silent relaxation |
| FR-V2-05 MILP planning | IMPLEMENTED / VERIFIED | Integer x/binary y, exact demand and output verification, actual CBC and independent oracle |
| FR-V2-06 comparable alternatives | IMPLEMENTED / VERIFIED | Verified reference, epsilon caps, exact cost/premium/exposure/allocation, distinct/deduplicated runs |
| FR-V2-07 deterministic explanation | PARTIAL | Allocation/exclusion/bounds/premium/infeasibility implemented; ML tree path belongs to T14; no claimed probability/IIS |
| AC-V2-04 controlled split/reference | PASS IN BOUNDED CORE | Three-supplier 6/4/0 plus independent exhaustive optima and hard-boundary cases |
| AC-V2-05 distinct/no-distinct alternatives | PASS IN BOUNDED CORE | Two distinct epsilon results and equal-score deduplication fixtures |
| AC-V2-06 determinism | PASS IN BOUNDED CORE | All six input permutations, equal-objective ties, fixed config and equal explanations |
| AC-V2-07 reasons/error separation | PASS IN BOUNDED CORE | Hard vs optimal-zero reasons, binding bounds, MOQ interaction, invalid/timeout/executable/incumbent/corrupt-output tests |

FR-V2-02–03, ML-specific FR-V2-07 and the complete API/UI/scenario/approval/PDF
workflow remain open. T13 does not close AC-V2-01–03 or AC-V2-08–13.

## Historical authorized Drive synchronization on 2026-10-01

After verification, the current V2 sections of these existing documents were
updated and independently read back through the connector:

- [00_THESIS_STATUS](https://docs.google.com/document/d/1X2WGVVYn0j1ymX0cv5kQQGIaJiEc7pcLSZYDIrXA3VU): local T13 implementation, exact evidence, next T14 and open ML/workflow scope.
- [02_ROADMAP](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4): T13 local status/results and concrete T14 score-validity entry gate.
- [06_REQUIREMENTS_BASELINE](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig): FR/AC acceptance mapping with LOCAL PASS/PARTIAL/OPEN distinguished; requirement meanings preserved.
- [07_DEVELOPMENT_STATUS](https://docs.google.com/document/d/1Xgphr_FEurdFlK651s2DTJWlubwt9vii1c5st9iO6E8): component status, T13 implementation/test record, limitations and T14 handoff.

Readback verified document/tab identity, inserted/replaced text, paragraph/list
roles and unchanged out-of-scope content, including historical V1/spike sections.
Existing native date fields were outside edited paragraphs. ADR-024–027 were not
changed because this implements their accepted boundaries without a new
architectural decision. ML/full V2 completion was not claimed.

On 2026-10-03, 00/02/06/07 were read again for this repository-only correction.
Their current baseline records PR #15 and hosted implementation success, bounded
FR/AC acceptance, a completed official task assignment, and the open T14 dataset,
leakage, score-validity and Python 3.11 ML gates. No Drive write was performed in
this documentation update; the earlier synchronization above remains a dated record.

## T14 handoff

1. Decide and document how quantity-feature predictions can produce coefficients
   constant across the entire allowed allocation range. Do not extend the old
   quantity-100 scores by assumption or change the feature schema silently.
2. Specify target, direction/scale, feature/dataset/model versions, prediction
   cutoff, sample/source metadata, controlled-vs-observed labels, leakage-safe
   splits and reproducible Decision Tree training/inference/tree-path reporting.
3. Build the separately authorized bounded Odoo+supplemental input/dataset boundary.
   Keep company/context/provenance outside the core. Verify capacity, availability,
   hard MOQ absence and commercial/delivery validity explicitly; standard quote
   quantities, Expected Arrival and supplierinfo thresholds are not substitutes.
4. Map validated inference into `RiskCoefficient` plus `ExternalRiskContext` without
   importing training/ERP infrastructure into the core. Missing, stale or incompatible
   coefficients must fail closed for risk alternatives; explicit cost-only is separate.
5. Execute T14 dependencies and actual training/inference on Python 3.11. The T13
   CBC proof does not verify scikit-learn or the full end-to-end ML workflow.
6. Preserve this minimum-cost reference and exact result meaning. Define versioned
   V2 snapshot/serialization/lifecycle separately in T15; do not retrofit V1 stored
   records, run solvers during retrieval/retry, or imply approval from a plan.

Performance scaling, real dataset validation, native price tiers and broader solver
numeric support remain unverified. T13 provides a bounded, documented composition
point; deployment and later complete-system acceptance remain pending. The T13
hosted implementation checks passed, while PR merge and the open T14 work remain
separate actions.
