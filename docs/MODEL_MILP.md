# Supplier selection and order allocation model (MILP)

Source: `decision_core/planning/` (model, bounds, verification, explanations) and
`optimization_adapter/pulp_cbc.py` (PuLP/CBC encoding). Thesis chapter 5.

## 1. Input

One product, one approved integer demand `Q`, suppliers `i = 1..N`. Per supplier:
unit price `p_i`, capacity `cap_i`, availability, hard MOQ or explicit "no MOQ",
quantity ranges in which the quoted price and the delivery promise are valid,
promised date. Policy: maximum number of suppliers `K`, optional concentration
limit `c` (share of `Q`), list of cost tolerances `ε`. Risk coefficient
`r_i ∈ [0,1]` comes from the supplier evaluation (higher = worse).

## 2. Bounds (eligibility before optimization)

For each supplier the rules compute a positive-use range `[L_i, U_i]`:

- `L_i = max(1, MOQ_i, price_min_i, delivery_min_i)`
- `U_i = min(cap_i, ⌊c·Q⌋, price_max_i, delivery_max_i)`
- `U_i = 0` (excluded, with a recorded reason) if the supplier is unavailable, its
  promise is later than the required date, or `L_i > U_i`.

A capacity below `Q` alone is not an exclusion: the supplier can cover a part.

## 3. Formulation

Variables: `x_i ∈ ℤ, 0 ≤ x_i ≤ U_i` (ordered quantity), `y_i ∈ {0,1}` (supplier used).

```text
Σ_i x_i = Q                       demand is met exactly
Σ_i y_i ≤ min(K, N)               supplier count
x_i ≤ U_i · y_i                   no quantity without activation
x_i ≥ L_i · y_i                   an activated supplier gets at least L_i
```

Objectives (lexicographic, each solved to proven optimality):

1. **Minimum cost plan**: `min C(x) = Σ p_i x_i` → optimum `C*`.
2. **Alternatives**, for every `ε`: `min R(x) = Σ r_i x_i` subject to
   `C(x) ≤ (1+ε)·C*`, then minimum cost among those. Reported risk exposure is
   `R(x)/Q`.
3. **Deterministic tie-break**: fix quantities one by one in supplier-id order
   (maximize each in turn) so equal-cost optima always yield the same plan.

Prices and scores are scaled to exact integers (rational arithmetic), so the solver
works on integer coefficients and results are checked exactly afterwards.

## 4. Verification and statuses

Every solver answer is re-verified in the core (sum, bounds, supplier count,
cost recomputation). Distinct outcomes: `optimal`, `infeasible` (proven, with
a bound-based explanation where provable), `no_proven_optimum` (time limit) and
`solver_error`. A duplicate alternative is reported as such, never invented.

## 5. Explanations

Per supplier: exclusion reason, positive-use range and slack, binding price/delivery
validity limits, binding concentration limit, zero allocation despite eligibility.
Per plan: cost premium over `C*` and exposure. No LLM is involved.

## 6. Stress scenarios

A scenario copies the stored base request, applies explicit changes and runs the
same model: supplier outage, capacity reduction, demand increase, price increase,
or a combination. The base case and any approved decision stay unchanged.
(P2 extends changes to both directions.)

## 7. Known limitations (state in chapter 5)

- **Linear exposure does not reward diversification.** `R(x)/Q` is a weighted
  average of supplier scores, so splitting an order between two equally scored
  suppliers has the same exposure as buying from one. Diversification is only
  enforced by the concentration limit `c` and the supplier-count limit `K`.
- The score is an uncalibrated ranking signal, not a failure probability.
- Single period, single product; no transport cost or lead-time dimension beyond
  the date eligibility rule.
