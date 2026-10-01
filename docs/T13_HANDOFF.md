# T13 — V2 domain and application-ready MILP core handoff

## Result and repository state

**LOCAL IMPLEMENTED / VERIFIED; HOSTED UNVERIFIED; NOT MERGED.** The bounded
one-product core is ready for application composition. It is not a completed V2
workflow or a validated ML predictor. Official thesis task assignment remains
TO BE DRAFTED. Live Drive status, roadmap, ADR-024–027, requirements and development
sections were read before design and implementation. See
[design](T13_V2_MILP_DESIGN.md) for authoritative semantics and entry evidence.

- Branch: `feature/t13-v2-milp-core`.
- Verified remote main, starting base and current HEAD:
  `71396e8924f6a1f60daf8b45f02861adf21a25e5`.
- T13 changes are local and uncommitted. No push, PR, merge or hosted T13 run.
- PR [#14](https://github.com/SafarErik/odoo-procurement-decision-support/pull/14)
  remains experimental and unmerged. Its latest combined head `b65347b` was used
  as reference, including the ML increment's external-score extension.
- Pre-existing apparent Reflex lockfile changes remain preserved in stash
  `bb904d26d5e85d6775187ac59f6940881566f493`; content diffs were empty after
  line-ending normalization. No stash drop/pop was performed.

Entry **GO for local implementation** followed explicit remote, working-tree,
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

## Executed verification on 2026-10-01

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
| Hosted T13 Quality / Container/API | UNVERIFIED: local uncommitted implementation, no remote run |

The required quality workflow now installs the solver as a required dependency and
executes its runtime gate on Python 3.11; no import-or-skip fallback. Configuration
is implemented, not a claim of a completed hosted run. The legacy suite includes
WSM, HTTP contracts, T11/T12 serialization, stored-only replay/retrieval and error
masking regressions. It does not substitute for unavailable PostgreSQL/Odoo live tests.

## Acceptance mapping

Statuses below describe the implemented local core on this branch, not merged or
hosted acceptance and not completion of the entire V2 system.

| Requirement / criterion | Status | Evidence and limit |
| --- | --- | --- |
| FR-V2-04 hard eligibility/constraints | IMPLEMENTED / LOCAL PASS | Explicit unknown-input rejection; availability/date, MOQ, capacity, max count, concentration and both commercial ranges; no silent relaxation |
| FR-V2-05 MILP planning | IMPLEMENTED / LOCAL PASS | Integer x/binary y, exact demand and output verification, actual CBC and independent oracle |
| FR-V2-06 comparable alternatives | IMPLEMENTED / LOCAL PASS | Verified reference, epsilon caps, exact cost/premium/exposure/allocation, distinct/deduplicated runs |
| FR-V2-07 deterministic explanation | PARTIAL | Allocation/exclusion/bounds/premium/infeasibility implemented; ML tree path belongs to T14; no claimed probability/IIS |
| AC-V2-04 controlled split/reference | LOCAL PASS | Three-supplier 6/4/0 plus independent exhaustive optima and hard-boundary cases |
| AC-V2-05 distinct/no-distinct alternatives | LOCAL PASS | Two distinct epsilon results and equal-score deduplication fixtures |
| AC-V2-06 determinism | LOCAL PASS | All six input permutations, equal-objective ties, fixed config and equal explanations |
| AC-V2-07 reasons/error separation | LOCAL PASS | Hard vs optimal-zero reasons, binding bounds, MOQ interaction, invalid/timeout/executable/incumbent/corrupt-output tests |

FR-V2-02–03, ML-specific FR-V2-07 and the complete API/UI/scenario/approval/PDF
workflow remain open. T13 does not close AC-V2-01–03 or AC-V2-08–13.

## Authorized Drive synchronization

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
point; deployment/hosted checks and later complete-system acceptance remain pending.
