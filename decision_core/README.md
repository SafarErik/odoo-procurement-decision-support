# Decision Core

This package contains the ERP-independent T2 procurement decision pipeline:

```text
canonical purchase requirement and supplier offers
  -> minimum-order-quantity constraint
  -> eligible alternatives only
  -> cost normalization for unit price and lead time
  -> Weighted Sum Model contributions and total
  -> score-descending, offer-ID-ascending ranking
```

The immutable result preserves each criterion's raw value, normalized value, weight,
and weighted contribution. Excluded offers and their reasons are returned separately.
If every offer is excluded, the result has no recommendation.

All decision numerics use `Decimal`. Public inputs must therefore supply quantities,
prices, lead times, and weights as finite `Decimal` values. The built-in
`StrategicProfile.cost_focused()`, `.urgent()`, and `.balanced()` constructors expose
the reference profiles.

The package does not import Odoo, the Odoo adapter, FastAPI, Reflex, HTTP,
environment configuration, a database framework, or any external service. It is not
wired into the existing RFQ API or frontend.
