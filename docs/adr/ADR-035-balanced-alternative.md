# ADR-035 (proposal): Balanced alternative by min–max supplier quantity

Status: **proposal** — repository draft, to be registered in Drive
03_ARCHITECTURE_DECISIONS by the owner. It extends, and does not replace, the accepted
ε-constraint alternative decision recorded there.

## Context

The cost–risk alternatives minimise the linear exposure Σrᵢxᵢ/Q within (1+ε)·C*. A
weighted average does not reward splitting an order (L5 in
[LIMITATIONS_AND_FUTURE_WORK.md](../LIMITATIONS_AND_FUTURE_WORK.md)). Together with the
few distinct Decision Tree scores, most demonstration cases produced one alternative,
and none that limits dependence on a single supplier.

## Decision

Add an optional, separate alternative stage. With an integer `m` and `xᵢ ≤ m` for every
supplier, minimise `m` subject to the existing constraints, `C(x) ≤ (1+ε_d)·C*` and
`R(x) ≤ R(x_min)`; then minimise exposure, then cost, then apply the existing tie-break.

- Policy gains `diversification_epsilon` (ε_d); the Odoo preview default is 0.2.
- Each recorded run gains `kind` (`risk` | `diversified`); the balanced run is last.
- Fields at their default (`None`, `risk`) are not written, so every snapshot saved
  before this change keeps byte-identical JSON and hashes.
- The core verifies the plan exactly (cost cap, exposure not above the minimum plan,
  largest share not above the minimum plan). Approval re-verification checks the
  stage sequence including the balanced run.
- The UI names a plan proved only by this stage "Kiegyensúlyozott terv" / "Balanced
  plan" and shows "largest share of one supplier" for every plan. The PDF names it.

## Alternatives considered

- Convex piecewise-linear share penalty: general, but breakpoints and weights would be
  arbitrary parameters to justify.
- Outage scenarios with binary indicators (expected or worst-case shortfall): larger
  model; kept as future work.
- Herfindahl index Σ(xᵢ/Q)²: quadratic, not a MILP.
- Raising K: changes the buyer's policy rather than offering an alternative.

## Consequences

- One more MILP stage (three solves plus the tie-break) per case and scenario.
- The measured interpretation is simple: `m` is the most one supplier's outage can
  take from the demand. It ignores correlation between suppliers.
- With K = 2 the best attainable split is 50/50.
- Old cases keep their results; only new cases and their scenarios use the stage.
