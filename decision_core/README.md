# Decision Core

This package contains the ERP-independent T2 procurement decision pipeline:

```text
canonical purchase requirement and supplier offers
  -> minimum-order-quantity constraint
  -> eligible alternatives only
  -> cost normalization for unit price and lead time
  -> optional direct delivery-adherence normalization when the complete set is usable
  -> Weighted Sum Model contributions and total
  -> score-descending, offer-ID-ascending ranking
```

The immutable result preserves each criterion's raw value, normalized value, weight,
and weighted contribution. Excluded offers and their reasons are returned separately.
If every offer is excluded, the result has no recommendation.

All decision numerics use `Decimal`. Public inputs must therefore supply quantities,
prices, lead times, and weights as finite `Decimal` values. The built-in
`StrategicProfile.cost_focused()`, `.urgent()`, and `.balanced()` constructors expose
the unchanged two-criterion reference profiles. `evaluate_decision()` remains the
default and does not inspect history.

T10 adds the separate `evaluate_historical_decision()` opt-in. Its ERP-neutral
`SupplierHistoricalPerformanceInput` contains only stable supplier identity, metric,
percentage value, sample size, and availability. MOQ is applied first. The criterion
activates only when every eligible offer's supplier has a usable finite value in
`[0, 100]` with `sample_size >= 3`; multiple offers may share one supplier result.
The active normalization is exactly `value / 100`. If the eligible set is incomplete,
the `HistoricalScoringResult` wraps the exact legacy `DecisionResult` from the
profile's fallback and lists affected identities in deterministic order. Missing
history is never converted to zero and never excludes an offer.

The versioned PoC policies are:

- `cost_focused_history_v1`: price `0.60`, lead time `0.25`, history `0.15`;
- `urgent_history_v1`: price `0.25`, lead time `0.60`, history `0.15`; and
- `risk_averse_history_v1`: price `0.30`, lead time `0.30`, history `0.40`.

Active historical contributions include the raw percentage, sample size, direct
normalized value, policy weight, weighted contribution, and deterministic text.
These weights are transparent PoC policy choices, not empirically optimized or
production validated.

The package does not import Odoo, the Odoo adapter, FastAPI, Reflex, HTTP,
environment configuration, a database framework, provenance, or any external
service. Historical scoring is mapped explicitly by the application layer and is not
wired into the public decision API, existing RFQ API, or frontend.
