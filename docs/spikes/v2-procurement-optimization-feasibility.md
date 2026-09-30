# V2 single-product procurement optimization feasibility spike

Date: 2026-09-30. Recommendation: **GO WITH CONDITIONS** for a proposed V2
research direction. This is not acceptance of a new thesis baseline or a production
architecture decision.

Branch: `spike/v2-procurement-optimization`.
Base/HEAD: `71396e8924f6a1f60daf8b45f02861adf21a25e5` (merged T12 / PR #13).
The spike is uncommitted at handoff; that hash identifies its base, not its changes.
No push, PR, merge, Google Drive update, or live Odoo operation was performed.

## 1. Proven technical facts

The isolated `tools/v2_optimization/` package executes against synthetic immutable
input without Odoo, HTTP, a database, or a frontend. It solves integer allocation
and binary supplier-use decisions with all six requested constraints. Existing WSM
and runtime source files are unchanged. The only dependency declaration is an
optional `optimization-spike` extra, pinned to PuLP 3.3.0.

The local environment is Windows AMD64, Python 3.14.7, PuLP 3.3.0, bundled CBC
2.10.3 (build dated 2019-12-15). Python 3.11 remains the project compatibility/CI
baseline. Static parsing with Python 3.11 grammar passed; Python 3.11 runtime and
hosted CI execution were not verified in this spike.

The post-change fast suite passed with **314 passed, 37 deselected**, including 41
optimization tests and two independent architecture tests. The pre-change suite
had 271 passed, 37 deselected. Existing dependency deprecation warnings remain.

Files:

- [Contracts](../../tools/v2_optimization/models.py)
- [MILP and explanations](../../tools/v2_optimization/solver.py)
- [Synthetic experiments](../../tools/v2_optimization/experiments.py)
- [Reference and oracle tests](../../tests/test_v2_optimization.py)
- [Boundary tests](../../tests/test_v2_optimization_architecture.py)
- [Recorded experiment inputs, plans, deltas, settings and raw timings](v2-procurement-optimization-results.json)

## 2. Mathematical and model assumptions

There is one product, one common indivisible unit, one currency, and one offer per
supplier. Product/UoM/currency normalization belongs outside this engine. Demand
`Q` is a positive integer; no overbuying, fractional units, currency conversion,
taxes, freight, fixed order fees, stock reservations, or multiple delivery dates are
modeled. Capacity is an explicitly supplied upper bound for this requirement, not
an inference from an RFQ quantity or a supplier's past deliveries.

For each supplier `i`, `x_i` is a nonnegative integer quantity and `y_i` is binary:

```text
sum_i x_i = Q
x_i <= capacity_i * y_i
x_i >= max(1, MOQ_i) * y_i
sum_i y_i <= max_suppliers
x_i <= concentration_limit * Q            (when supplied)
x_i = 0                                  (unavailable or deadline-ineligible)
```

The positive-use lower bound prevents empty selected suppliers when MOQ is absent
(represented as zero). An optional concentration bound has its original rational
meaning; integer quantities naturally impose `floor(limit * Q)`. A ceiling below a
supplier's MOQ makes that supplier unusable. No constraint is silently relaxed.
Deadline eligibility is an explicit synthetic Boolean: it assumes the entire
allocated order can meet the hard delivery condition. A future application would
need to establish it from validated, quantity-dependent promise/date semantics.
Historical adherence never substitutes for this hard condition.

Baseline objective: `C = sum_i unit_cost_i * x_i`, minimized. Money has at most two
decimal places and is represented as integer cents. Adherence, concentration and
epsilon have at most four decimal places. The PoC accepts 1–50 suppliers, quantities
up to 1,000,000, unit prices up to 1,000,000 currency units, and a maximum total
cost bound of `10^12` cents. Unsupported precision, nonfinite/negative values,
duplicate identities and invalid types fail before solving. These numerical limits
are spike assumptions, not a general procurement-domain contract.

Risk coefficients are integer basis points: `r_i = 1 - adherence_i`. The reported
historical proxy is `sum_i x_i*r_i / Q`; its numerator is the equivalent linear
objective because `Q` is constant. It is neither a future delay probability nor a
joint probability of delivery failure. It does not model correlated suppliers,
uncertainty, quantity-specific performance, confidence intervals, or consequences
of delay. Reported ratios use Decimal division with 40 significant digits; objective
locks and cost caps use integer arithmetic.

Risk optimization requires adherence and sample size >=3 for **every usable
supplier**, including currently unselected ones. Missing/withheld history returns
`history_unavailable`, without inventing a risk or excluding an otherwise usable
supplier. Cost-only optimization remains available, with an unavailable risk proxy.
The threshold of three preserves the existing PoC withholding convention; it is not
evidence of statistical confidence.

The epsilon approach first proves `C_min`, then minimizes risk subject to
`C <= floor((1+epsilon)*C_min)` in cents. Equal-risk optima minimize cost as a
secondary objective, avoiding weakly dominated plans. Final ties sequentially
maximize each `x_i` in sorted supplier-ID order while locking the preceding exact
objectives and allocations. This yields one canonical allocation without relying
on solver tie order or adding tiny objective perturbations. It is a technical tie
policy, not a business preference for a supplier's identity.

CBC uses one thread, fixed random seeds, zero relative/absolute optimality gap,
and a ten-second limit **per phase**. Both problem and solution status must prove
optimality. An incumbent, timeout, missing executable, or failed post-solve check
returns no plan. Every returned solution is checked against exact integer variable
bounds and every model constraint, including tiers and objective locks. This reduces
floating-point acceptance risk; it is not a formal rational-arithmetic optimality
certificate or a guarantee about all solver/platform versions.

## 3. Successful experiments

### Cost-risk plans

Synthetic requirement: Q=100, maximum two suppliers, concentration <=0.80.

| Supplier | Unit cost | Capacity | Adherence | Sample size |
| --- | ---: | ---: | ---: | ---: |
| A | 10.00 | 60 | 0.60 | 20 |
| B | 10.50 | 80 | 0.95 | 20 |
| C | 11.00 | 100 | 0.99 | 20 |

| Epsilon | Allocation A/B/C | Cost | Actual cost premium | Historical proxy | Largest share | Supplier count |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 60 / 40 / 0 | 1,020 | 0% | 0.2600 | 60% | 2 |
| 0.02 | 20 / 80 / 0 | 1,040 | 1.9608% | 0.1200 | 80% | 2 |
| 0.05 | 0 / 58 / 42 | 1,071 | 5.0000% | 0.0332 | 58% | 2 |
| 0.10 | 0 / 20 / 80 | 1,090 | 6.8627% | 0.0180 | 80% | 2 |

These are four distinct useful cost-risk trade-offs in this controlled example.
The cap is an allowance, not a target: the 10% allowance consumes only 6.8627%.
Reducing this proxy can increase concentration; no resilience claim follows. Other
inputs can yield identical plans for several epsilon values. The experiment reports
unique allocation count; presentation-level deduplication remains future work.
The four caps sample alternatives, not the complete efficient frontier.

### What-if re-optimization

Each row changes exactly one baseline input and runs the same minimum-cost model.
All remain feasible; the quantity-increase row is a different-sized requirement.

| Change | New allocation A/B/C | New cost | Cost difference | Allocation difference A/B/C | Proxy difference | Feasibility changed |
| --- | --- | ---: | ---: | --- | ---: | --- |
| A unavailable | 0 / 80 / 20 | 1,060 | +40 | -60 / +40 / +20 | -0.2180 | No |
| A capacity reduced to 30 | 30 / 70 / 0 | 1,035 | +15 | -30 / +30 / 0 | -0.1050 | No |
| Q increased to 120 | 60 / 60 / 0 | 1,230 | +210 | 0 / +20 / 0 | -0.0350 | No |
| A price increased to 11.50 | 0 / 80 / 20 | 1,060 | +40 | -60 / +40 / +20 | -0.2180 | No |

### Infeasibility and explanations

Increasing baseline Q to 300 produces `infeasible` with no plan. Effective supplier
ceilings sum to 240, below demand. A separate manual test with Q=10, two capacities
of six and maximum one supplier identifies a count/capacity shortfall. With maximum
two suppliers and MOQ=6 for both, total capacity passes the early check but the
solver proves infeasibility: one supplier supplies at most six and two require at
least twelve. No artificial allocation is returned.

The post-solve layer reports hard availability/deadline exclusions, unusable MOQ
floors, capacity/MOQ/concentration equality, an integer concentration ceiling, zero
allocation in an optimal plan, and exact extra cost/relative premium. For the 2%
plan, B reaches both capacity and concentration; the additional cost is 20. Zero
allocation for an otherwise usable supplier is explained only as a fact of the
objective/tie-break result. It is not a causal counterfactual, an exclusion decision,
or a claim that the supplier is universally inferior. Solver-proven interacting
infeasibility is distinguished from an identified deterministic shortfall; there is
no IIS/minimal-conflict explanation or MILP sensitivity/dual-price claim.

### Quantity-pricing proof

For all-units tiers, introduce binary `z_ik` and integer quantity `q_ik`:

```text
sum_k z_ik = y_i
x_i = sum_k q_ik
L_ik*z_ik <= q_ik <= U_ik*z_ik
C_i = sum_k price_ik*q_ik
```

Exactly one tier is active for a used supplier. Its upper bound is one below the
next inclusive threshold, bounded by capacity, concentration and demand. A tier
above the usable quantity range cannot activate. This removes the price-times-
binary-times-quantity product through linear constraints with natural finite bounds.

A has capacity 1,000 and prices 1,000 HUF/unit for quantities 1–499, 920 for
quantities >=500. B costs 950 throughout. With maximum one supplier:

| Q | Selected supplier | Cost HUF |
| ---: | --- | ---: |
| 499 | B | 474,050 |
| 500 | A | 460,000 |
| 600 | A | 552,000 |

The discount applies to **every unit in that supplier's order**, not only units
above 499. The lower total at 500 than at 499 is an intended all-units discontinuity.
Marginal block pricing would require a different contract/formulation; it was not
implemented. No overbuying to reach a tier is possible because demand equality is
hard. This is a small formulation proof, not validation of an ERP pricelist.

### Automated coverage

Cases A–J have hand-calculated assertions: split, insufficient cheapest capacity,
hard deadline, concentration, MOQ, outage, demand/capacity changes, epsilon plans,
infeasibility, and all-units tiers. Additional tests cover price increases,
input-order-independent ties, equal-risk cost minimization, missing/withheld history,
fractional-cent caps, integer concentration, invalid inputs, nonoptimal/error solver
statuses, a constant zero-risk objective, unreachable tiers, and precision/context
independence. Decimal-to-integer conversion uses exact fractions rather than ambient
Decimal rounding. Twelve seeded tiny
cases enumerate every allocation independently and compare both cost and capped-
risk optima including tie policy. Architecture checks prohibit external runtime
dependencies and any runtime import of this experiment.

## 4. Failed or problematic experiments

- A zero-risk objective initially exposed PuLP's fixed `__dummy` variable in a
  locked constant objective. Exact post-solve validation now handles that fixed-zero
  variable; the regression passed in the final suite.
- The 50-supplier canonical solution needs 51 separate CBC processes. Tie-breaking
  overhead is material, despite a quick primary solve. A per-phase time limit is
  not an overall response-time guarantee.
- General interacting infeasibility has no minimal conflict set. The explanation
  wording states this limit rather than guessing which constraint to remove.
- The bundled CBC build is old. Its successful local run does not establish the
  suitability of that build/version for a future production engine.
- Python 3.11 runtime, hosted CI, live services and the full trade-off workflow at
  larger supplier counts remain unverified. Optional solver tests skip when PuLP
  is absent; the existing CI installation does not install this extra. Two boundary
  tests still run without it. No hosted pass is claimed.
- Podman is unavailable on this session's PATH, and the usual
  `C:\Program Files\RedHat\Podman\podman.exe` path was absent. Compose validation
  was attempted but could not run. No infrastructure change depends on this spike.

## 5. Open questions and conditions for baseline acceptance

1. Validate or explicitly govern per-requirement capacity, supplier availability,
   hard deadline/promises, MOQ and all-units tier applicability. Distinguish a quote
   from a commitment; do not infer capacity from quotation quantity.
2. Decide the authoritative demand, integer-unit suitability, currency/precision,
   price-validity, supplier-count, concentration, and complete-history policies.
3. Agree what historical proxy should mean across products/time windows and sparse
   samples. Establish whether its business relevance justifies the extra cost;
   sample >=3 is not statistical validation.
4. Execute Python 3.11 and a chosen supported solver build on the intended platform,
   set a response-time budget, and profile ties/full epsilon runs with tiers and
   tighter combinatorial constraints. Warm starts, fewer tie phases, or an embedded
   backend may help; none was substituted silently in the spike.
5. Define a deterministic explanation policy for admissible zero allocations and
   conflicting constraints before exposing recommendations to a buyer.
6. Obtain human approval for the V2 thesis scope/baseline in the living documentation.
   This repository experiment does not perform that approval or documentation edit.

## 6. Solver/library trade-offs

| Option | MILP and local execution | Dependency/testing/status trade-off | Spike decision |
| --- | --- | --- | --- |
| PuLP 3.3.0 + CBC | Direct linear algebra model, integer/binary variables; this pinned release bundles CBC | Pure Python modeler plus local executable; simple status/value inspection. Process startup and two-level optimality status need care | Chosen and executed; one optional dependency, no change to runtime stack |
| OR-Tools MPSolver | Official Python example uses SCIP for MIP; pip installation available | Embedded solver interface and objective/value/status inspection are attractive. Broader binary/dependency footprint and environment compatibility would need checking | Realistic alternative, not installed/benchmarked; no speed comparison claim |
| Pyomo + separate MILP solver | Expressive MILP modeler with several solver backends | Official installation guide states solvers are installed separately. Extra solver setup and result handling are unnecessary for this small proof | Useful for broader modeling; not installed/benchmarked |

This choice is a temporary spike conclusion, not a permanent ADR. Integer
quantities do not make this CP-SAT-specific: the implemented model is MILP with
binary supplier/tier selection. No proprietary solver or remote service is used.

Primary library sources checked on 2026-09-30:

- [PuLP 3.3.0 release documentation](https://pypi.org/project/PuLP/3.3.0/)
  describes MILP and bundled CBC for this exact release. Newer PuLP versions have
  changed solver installation, so this spike intentionally pins the tested release.
- [OR-Tools MIP example](https://developers.google.com/optimization/mip/mip_example)
  and [Python installation](https://developers.google.com/optimization/install/python).
- [Pyomo installation](https://pyomo.readthedocs.io/en/stable/getting_started/installation.html).

## 7. Odoo data-requirement audit

This is an audit of repository evidence, **not a new live capability probe**. T6
supersedes earlier T4 read/mapping blockers within its accepted subset. T8 documents
the controlled history slice. Their existing tests exercise those contracts; no
new Odoo mapping or V2 adapter was added.

| V2 input | Classification | Existing evidence and remaining boundary |
| --- | --- | --- |
| Required quantity | Already validated within T6 subset | Equal RFQ-line quantities with exact Decimal semantics; not yet an independent authoritative split-allocation demand source |
| Product identity | Already validated within T6 subset | Exact common variant with one line per RFQ; the neutral optimizer assumes one normalized product and does not need an ERP identifier |
| Supplier identity | Already validated within T6 subset | Stable commercial-supplier joins; this experiment supports one offer per unique neutral supplier |
| Unit price | Already validated within T6 subset | Quotation-line unit price, common currency/UoM, zero discount/no taxes; no guarantee of validity for every allocated quantity |
| Price tiers | Not yet validated | T4/T6 reject vendor-pricelist minimum quantity as hard MOQ; applicability/validity/all-units vs marginal semantics need a separate spike |
| Supplier capacity / available quantity | Not yet validated | No documented mapping for per-requirement available supply; synthetic in this spike; supplemental input is a possible future policy |
| Delivery / deadline condition | Currently supplemental / explicitly supplied | T6 accepts attributed supplier-promised lead time; it rejects planned-date/vendor-delay fallbacks. Hard deadline eligibility and quantity-specific promises are not yet validated |
| Minimum order condition | Currently supplemental / explicitly supplied | T6 requires attributed hard MOQ; no automatic `product.supplierinfo.min_qty` mapping |
| Historical delivery performance | Already validated in bounded T7-S/T8 subset | Expected Arrival schedule adherence through the approved projection; not supplier-promise adherence or a future probability |
| Sample size | Already validated in bounded T8 subset | Separate eligible completed-line count; values below three withheld. Normalizing percent to [0,1] is arithmetic, not new data-source validation |
| Maximum supplier count / concentration | Explicitly supplied application policy | New synthetic business constraints here; not assumed Odoo facts |
| Forecast / inventory target / safety stock | Not required for initial V2 core | No multi-period planning or forecasting requirement |

Evidence: [T6 mapping/invariants](../T6_DESIGN.md),
[T6 controlled live acceptance](../T6_HANDOFF.md),
[T8 KPI/withholding/controlled live result](../T8_HANDOFF.md),
[historical mapping spike and later T8 status](odoo-historical-supplier-performance.md),
`tests/test_decision_input_assembly.py`,
`tests/test_odoo_comparison_case_adapter.py`,
`tests/test_historical_performance.py`,
`tests/test_odoo_historical_performance_adapter.py`, and the opt-in T6/T7/T8 contracts
in `tests/integration/test_live_odoo_contract.py`. No undocumented standard Odoo
field is asserted as a source for capacity, tiers or deadline eligibility.

## 8. Performance observations

Three repeated runs at each size use Q=1,000, distinct linear prices,
approximately 1.5Q aggregate capacity, maximum supplier count equal to supplier
count, no MOQ or tiers, and no concentration limit. Each run asserts identical
allocations. Timings below are medians from the recorded JSON. The first phase
includes CBC process start/solve/readback; total time also includes model creation,
all lexicographic phases, exact checks and explanation construction.

| Suppliers | Initial minimum-cost phase ms | Complete canonical result ms | Solve phases |
| ---: | ---: | ---: | ---: |
| 3 | 113.69 | 446.14 | 4 |
| 10 | 126.03 | 1,371.12 | 11 |
| 25 | 117.45 | 2,945.15 | 26 |
| 50 | 158.32 | 7,932.34 | 51 |

The primary MILP is quick on these easy instances. The complete deterministic
service is suitable for small local research experiments, with a visible wait at
50 suppliers. Calling this universally fast enough for an interactive product
would be premature: 7.9 seconds needs an explicit latency budget or tie-policy
optimization. Full risk-cap generation at 50 suppliers, difficult MOQ combinations,
tiers, cold machines, concurrent requests, and production scalability were not
benchmarked. An earlier exploratory run had a 50-supplier median of about 8.6 s;
process overhead and local contention visibly affect these observations.

## 9. Architectural impact and deliberately excluded work

```text
ProcurementOptimizationInput -> optimize -> OptimizationResult / ProcurementPlan
```

The new contracts do not force allocation into the ranking-oriented `SupplierOffer`
or replace WSM. All optimizer imports are standard library, PuLP or its own
experimental package. Runtime packages do not import the spike. Packaging remains
development tooling invoked with `python -m`, like existing T9 evaluation tooling;
the experiment is not added to the distributed runtime packages. No endpoint,
persistence schema, scoring profile, historical adapter, Odoo mapping or UI changes
were introduced. Returned plans are evidence for human inspection; they create no
business action. README and implementation log identify the experiment separately.

Deliberately not implemented: multi-product/multi-period optimization, forecasting,
safety-stock optimization, automated purchase orders, write-back, feedback loops,
split-delivery/time-indexed scheduling, frontend/Reflex work, LangGraph, LLMs,
SharePoint/Excel/other ERP adapters, authentication redesign, cloud deployment,
or a production selection workflow. Google Drive documents remain untouched.

### Commands and verification record

The commands below were executed from the repository in PowerShell using the
existing ignored project `.venv`. Network installation and Git branch creation
required sandbox escalation; both succeeded without an approval rejection.

```powershell
git status --short
git branch --show-current
git log -1 --format='%H %s'
codegraph explore "assemble_decision_input HistoricalPerformance ProcurementRequirement SupplierOffer tests/test_architecture.py"
git switch -c spike/v2-procurement-optimization
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install 'pulp==3.3.0'
.\.venv\Scripts\pytest.exe -m 'not integration and not e2e' -q
.\.venv\Scripts\pytest.exe tests/test_v2_optimization.py -q -p no:cacheprovider
.\.venv\Scripts\pytest.exe tests/test_v2_optimization.py -q -p no:cacheprovider -k 'zero_risk'
.\.venv\Scripts\python.exe -m tools.v2_optimization.experiments | Out-File -LiteralPath docs/spikes/v2-procurement-optimization-results.json -Encoding utf8
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m compileall application backend frontend decision_core odoo_adapter persistence migrations tools/v2_optimization
.\.venv\Scripts\python.exe -m compileall -q application backend frontend decision_core odoo_adapter persistence migrations tools/v2_optimization
.\.venv\Scripts\pytest.exe -m 'not integration and not e2e' -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pip check
$env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path .\.venv\Scripts\podman-compose.exe).Path
podman compose --env-file .env -f infra/odoo/compose.yaml config --quiet
git diff --check
```

For a fresh environment, install the optional dependency with
`python -m pip install -e ".[frontend,dev,optimization-spike]"`, then run the same
tests and experiment. Installing only `[frontend,dev]` leaves solver tests skipped;
that is not successful verification of this spike.

| Check | Result |
| --- | --- |
| Pre-change fast suite | PASS: 271 passed, 37 deselected |
| Initial focused suite | PASS: 39 passed before adding the zero-risk regression |
| Expanded suite before fixing constant objective | FAIL: 1 failed, 39 passed; fixed as described above |
| Focused zero-risk regression after repair | PASS: 1 passed, 39 deselected |
| Final full fast suite, optional solver installed | PASS: 314 passed, 37 deselected; 41 solver tests and 2 boundary tests |
| Ruff format and lint | PASS |
| Compileall including experimental sources | PASS |
| Dependency consistency | PASS: no broken requirements |
| Experiment script | PASS: four unique epsilon allocations, what-if deltas, explicit infeasibility, tier thresholds and scaling data recorded |
| Git whitespace check | PASS; normal LF/CRLF warnings only |
| Odoo Compose config | NOT RUN SUCCESSFULLY: executable unavailable |
| Integration/live Odoo/E2E/frontend export | SKIPPED: no running-service or frontend change in this isolated task |
| Python 3.11 runtime / hosted CI | UNVERIFIED; no workflow changed, no push/PR |

## 10. Final evaluation and recommendation

1. **Clean MILP representation? Yes.** Single-product integer quantities and
   supplier-use binaries express the requested hard constraints directly.
2. **Deterministic minimum-cost sourcing? Yes within the tested model/toolchain.**
   Proven objective locks plus canonical lexicographic ties produced repeated,
   input-order-independent results. Cross-version/platform execution is unverified.
3. **Epsilon cost-risk alternatives? Yes.** Four requested caps produced four
   nondominated cost/proxy points in the reference case; other cases can collapse.
4. **Deterministic what-if re-optimization? Yes.** Outage, capacity, demand and price
   changes are input substitutions, with explicit deltas/status and no special ERP
   dependency.
5. **Useful explanations without an LLM? Yes, with limits.** Hard reasons, active
   bounds and premiums are deterministic. General causal explanations and minimal
   infeasibility conflicts are not established.
6. **Quantity pricing without unreasonable complexity? Yes for all-units tiers.**
   One binary/quantity pair per tier is sufficient; actual source applicability and
   marginal pricing remain separate questions.
7. **Fast enough for local PoC? Conditionally.** Initial solves took about 114–158 ms
   at the measured sizes; complete canonical results took about 0.45–7.93 s. Small
   cases are practical; 50 suppliers need a latency decision before product claims.
8. **Independent from Odoo/FastAPI/persistence/frontend? Yes.** Import boundary tests
   and unchanged runtime source establish the isolated architecture.
9. **Supported inputs versus gaps?** Controlled T6 supports quantity, identity and
   quote price; bounded T8 supports adherence/sample size. MOQ and promised lead
   time remain supplemental. Capacity/availability, tier applicability, independent
   demand semantics and hard delivery commitments still need validation/governance.
10. **Strong enough to become the next thesis baseline? GO WITH CONDITIONS.** The
    mathematics and isolation are demonstrated. Approve the narrowed business/data
    policies, validate the missing inputs, verify Python 3.11/solver portability,
    resolve latency/explanation expectations, and explicitly accept the thesis scope
    before promoting this experiment. Mathematical feasibility is not end-to-end
    procurement readiness.

Stop here: no production implementation or baseline promotion is authorized by
this spike's conclusion.
