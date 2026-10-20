# Supplier selection and order allocation model (MILP)

Source: `decision_core/planning/` (model, bounds, verification, explanations) and
`optimization_adapter/pulp_cbc.py` (PuLP/CBC encoding). Thesis chapter 5.

## 1. Input

One product, one approved integer demand `Q`, suppliers `i = 1..N`. Per supplier:
unit price `p_i`, capacity `cap_i`, availability, hard MOQ or explicit "no MOQ",
quantity ranges in which the quoted price and the delivery promise are valid,
promised date. Policy: maximum number of suppliers `K`, optional concentration
limit `c` (share of `Q`), list of cost tolerances `ε`, optional balanced-plan
tolerance `ε_d`. Risk coefficient
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
3. **Balanced alternative** (when `ε_d` is set; ADR-035 proposal): with an extra
   integer `m`,

   ```text
   x_i ≤ m                         for every supplier
   C(x) ≤ (1+ε_d)·C*               same kind of cost cap
   R(x) ≤ R(x_min)                 never more exposure than the minimum-cost plan
   ```

   `min m`, then `min R(x)`, then `min C(x)`. `m` is the largest quantity that
   depends on one supplier, i.e. the most that one supplier's outage can take from
   `Q`; the plan reports it as `largest_share = m/Q`. It is a separate run with
   `kind = "diversified"`, recorded after the `ε` runs.
4. **Deterministic tie-break**: fix quantities one by one in supplier-id order
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
same model with the base case's saved supplier scores (no new Odoo read, no
re-scoring). The base case and any approved decision stay unchanged.

| Kind | Change (each relative to the stored base) |
| --- | --- |
| `supplier_outage` | an available supplier becomes unavailable |
| `capacity_change` | a supplier's capacity becomes any other integer `≥ 0` |
| `demand_change` | the approved demand `Q` becomes any other integer `≥ 1` |
| `price_change` | a supplier's unit price becomes any other positive decimal |
| `combined` | at least two of the above in one scenario |

**Changed in P2 (2026-10-17).** Until P1 the changes were one-directional
(`capacity_reduction`, `demand_increase`, `price_increase`): only stricter
conditions could be tested. The official task asks for stress tests with capacity,
demand and price *change*, and a buyer also needs the opposite questions (a
supplier offers more capacity, a lower price arrives, demand is cut). The model,
bounds and solver are unchanged; only the input validation now accepts both
directions and rejects a "change" equal to the stored value. Stored scenarios keep
their original kind; the library shows `capacity_reduction`, `demand_increase` and
`price_increase` as `capacity_change`, `demand_change` and `price_change`.

Reading results: a lower demand or a higher capacity can make an infeasible base
feasible; a higher demand can make a feasible base infeasible (recorded, never
invented); totals across different demands are not like-for-like savings.

## 7. Known limitations (state in chapter 5)

- **Linear exposure does not reward diversification.** `R(x)/Q` is a weighted
  average of supplier scores, so splitting an order between two equally scored
  suppliers has the same exposure as buying from one. Capacity limits and the
  concentration limit `c` can make several suppliers necessary; the supplier-count
  limit `K` is only an upper bound on how many suppliers may be used and never
  forces a split. The balanced alternative (objective 3) offers a split explicitly;
  it does not change the exposure measure, and with `K = 2` its best is 50/50.
- The score is an uncalibrated ranking signal, not a failure probability.
- Single period, single product; no transport cost or lead-time dimension beyond
  the date eligibility rule.
