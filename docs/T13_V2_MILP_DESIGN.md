# T13 — V2 domain and MILP planning design

## Authority and entry decision

Live reads of 00_THESIS_STATUS, 02_ROADMAP, ADR-024–027,
06_REQUIREMENTS_BASELINE and 07_DEVELOPMENT_STATUS on 2026-10-01 confirmed the
accepted V2 baseline. Official task assignment remains TO BE DRAFTED. T0/V1-only
scope and the former T13 Reflex-only roadmap are historical; architectural,
read-only Odoo and immutable V1 snapshot rules remain binding.

Entry **GO for implementation**, not acceptance: remote main verified by ls-remote
and fetch as `71396e8924f6a1f60daf8b45f02861adf21a25e5`; clean detached-main
regression 271 passed / 37 deselected on Python 3.14.7; Ruff format/lint,
compileall and pip check PASS. T12 PR #13 head `e074e2e` hosted Quality
35782454967 and Container/API 35782454981 success. Those are pre-merge head
checks; no status was returned for the squash main commit itself. PR #14 remains
open/unmerged at `b65347bc1fb7a2877e005b1b42baf75acb7ef0a2`; hosted runs
36756499541/36756499578 success, but omitted optional solver/ML dependencies.
Python 3.11 initially UNVERIFIED; service-dependent checks SKIPPED unless available.

Current branch `feature/t13-v2-milp-core` starts from verified main. Two apparent
pre-existing frontend lockfile changes were preserved in named stash
`bb904d26d5e85d6775187ac59f6940881566f493`; their content diff was empty after
line-ending normalization. The stash remains preserved. No spike merge, user
commit, push or PR is part of T13 authorization.

## Boundaries

- `decision_core/planning/`: immutable ERP-neutral V2 contracts, eligibility,
  exact validation, deterministic explanations and planning orchestration/solver port.
- `optimization_adapter/`: replaceable PuLP/CBC adapter; no ERP/HTTP/database access.
- `application/procurement_planning.py`: thin use-case boundary; attribution remains
  application-owned, without new assembler/API/persistence/ML/UI work.
- Existing WSM exports, API, T11/T12 version-1 serialization, stored GET/retry and
  snapshots remain unchanged. New contracts are not retrofitted into stored V1 data.

Selectively reuse integer/binary model, exact post-checks, zero-gap configuration,
external scores and sequential tie-breaking from the **latest** cumulative spike.
Do not reuse implicit availability/MOQ/deadline defaults, 50-supplier limits,
fixed cents/four-decimal business precision, history fallback or optional tiers.

## Supported business and numeric contract

One product, approved positive integer Q, one named indivisible quantity unit and
one currency; exactly one commercial offer per supplier. Every offer explicitly
supplies matching product/unit/currency, positive finite Decimal unit price,
nonnegative integer capacity, Boolean availability, typed hard MOQ or explicit
absence, inclusive positive-integer price and delivery quantity ranges and a
promised date applying to the delivery range. Required date is explicit. No inferred
conversion, taxes/freight, quantity tiers, split deliveries or unbounded conditions.
Missing/unknown critical inputs are invalid input, not excluded-by-default suppliers.

Domain Decimal inputs have no fixed cent/four-place precision or spike magnitude
limit. Exact Fraction conversion is used for comparisons and common objective
scales (LCM denominators, GCD reduction). The provisional adapter rejects models
whose integer coefficient/RHS/objective envelope exceeds its documented configured
exact-numeric budget (default 2^40), as invalid numeric support, not infeasibility.
Decimal representations are also bounded by the adapter to 64 digits and absolute
exponent 64 before conversion/scaling; this is configurable infrastructure support,
not required business precision. The same limit applies to epsilon cap encoding.
This is an adapter limit, not a permanent business rule. Ratios expose exact
Fractions; monetary totals retain exact Decimal values without ambient-context
rounding. Quantity integers are not rounded at the domain boundary.

Risk inputs are external, finite Decimal coefficients in [0,1], higher means more
undesirable schedule-risk exposure. They are not calibrated probabilities. Each
coefficient declares a quantity range in which it may be treated as constant.
Risk optimization requires that range to cover every commercially feasible positive
allocation for its supplier; incompatible coverage is invalid input, not a silent
restriction of the business feasible set. It never extends a quantity-100 score to
arbitrary allocation quantities. Score definition/model
context and validity decision are explicit application-side records. T14 must
decide whether quantity-independent features or another separately authorized
mapping provides defensible range validity; T13 does not approve a new ML schema.
Missing scores are never zero. Cost-only runs have no exposure when complete valid
scores are absent; requesting epsilon alternatives requires usable scores for all
otherwise usable suppliers and explicit risk context.

## Model and policies

For sorted supplier IDs, integer x_i and binary y_i:

```text
sum x_i = Q
L_i*y_i <= x_i <= U_i*y_i
sum y_i <= max_suppliers
U_i <= capacity_i, Q, floor(concentration*Q), price_max, delivery_max
L_i = max(1, explicit MOQ if any, price_min, delivery_min)
U_i = 0 if unavailable, promise after required date, or L_i > U_i
```

Risk-enabled requests validate coefficient-range coverage without changing L/U,
so the minimum-cost reference and alternatives retain the same business feasible set.
Capacity below Q does not itself exclude a supplier. Policy fields max suppliers,
concentration (explicit None means no limit) and epsilon tuple are required.

Minimum cost is proven first, then lexicographically maximize allocation by ascending
supplier ID, preserving the exact cost optimum. Each requested epsilon minimizes
sum r_i*x_i under C <= floor(C_min*(1+epsilon)) in exact reduced cost units; then
minimizes cost at the risk optimum, then applies the same lexicographic tie-break.
Reference cost is never replaced with an alternative's cost. Exposure is sum r_i*x_i/Q.
Epsilon can exceed 100%; finite/nonnegative is the business constraint. Sort/deduplicate
epsilon values, return stable alternatives, alias identical allocations rather than
inventing distinct plans. Cost-only tie-breaking does not secretly optimize risk.

## Solver behavior and explanations

Use pinned PuLP 3.3.0 and its bundled CBC as provisional starting point. Runtime
dependency/solver smoke becomes mandatory in the existing Python 3.11 quality job.
Single thread, fixed seeds, zero relative/absolute gap; configurable total request
wall-clock budget shared across all solve phases, not reset for each supplier.
Require both solver problem and solution optimal statuses. Validate every integer
primal/binary variable, model constraint, objective lock and output business bound
exactly after rounding only values within configured small integrality tolerance.
Never accept an incumbent as a proven optimum or an invalid numerical plan.

Default configuration: seed 17 for CBC and CLP, one thread, elapsed time mode,
30-second shared budget, zero absolute/relative gap, integrality tolerance 1e-6.
The local runtime gate confirmed PuLP 3.3.0 / CBC 2.10.3 on Python 3.11.16.

Statuses: invalid_input, optimal, infeasible, no_proven_optimum and solver_error.
Only necessary-capacity/count proofs or original feasible-set solver proof imply
business infeasibility. A later objective-lock/tie-break infeasible phase is solver
failure, since a feasible minimum was already proved. A request can retain an
already verified minimum reference while alternative work is unproven/failed;
failed/unproven stages themselves emit no plan and overall status is not optimal.

Explanations distinguish hard exclusion from zero in the objective solution;
record effective bounds/slack/binding, allocation, max-count/concentration and exact
cost premium. Interacting MOQ/count infeasibility has a generic solver-proof reason,
not a fabricated IIS/minimal conflict set or causal sensitivity result.

## Verification and downstream handoff

Use hand calculations and independent exhaustive small-instance optima, genuine
three-supplier splits, eligibility/MOQ/capacity/count/concentration/commercial/risk
validity boundaries, missing critical inputs, interacting infeasibility, explicit
timeout/failure/noninteger/constraint-corruption tests, deterministic permutations,
epsilon distinctness/deduplication and legacy architecture/snapshot/API regressions.
Run Python 3.11 with actual CBC if obtainable locally in an ignored project-local
environment; otherwise acceptance remains UNVERIFIED. No global dependencies.

FR-V2-04–06/AC-V2-04–07 target this bounded core. FR-V2-07 remains PARTIAL because
tree-path explanations belong to T14. Full workflow, Odoo assembly, scenario API,
V2 snapshot lifecycle, frontend, approval and PDF remain later increments.
