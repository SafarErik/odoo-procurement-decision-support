# T2 handoff — ERP-independent Decision Core

## Increment objective

T2 answers one bounded question on synthetic canonical input: given a purchase
requirement, supplier offers, and a strategic weighting profile, which eligible
offer ranks highest, and how did every criterion contribute?

The implemented pipeline is:

```text
hard constraints
  -> eligible offers
  -> normalization over eligible offers only
  -> Weighted Sum Model
  -> deterministic ranking
  -> criterion-level contribution explanation
```

## Domain concepts

- `PurchaseRequirement`: requirement identifier and requested quantity.
- `SupplierOffer`: offer and supplier identifiers, unit price, lead time in days,
  and minimum order quantity.
- `StrategicProfile`: a name plus unit-price and lead-time weights. Built-in
  constructors provide cost-focused (0.7/0.3), urgent (0.3/0.7), and balanced
  (0.5/0.5) profiles.
- `DecisionResult`: immutable ranked eligible offers and separately represented
  excluded offers. `recommended_offer` is the first ranked offer or `None` when no
  offer is eligible.
- `CriterionContribution`: criterion, direction, raw value, normalized value,
  applied weight, and weighted contribution.

All decision numerics use `Decimal`. Inputs must provide finite Decimal values; the
core does not silently coerce or repair invalid values. Supported weights may be at
most 1 in total and may fall below 1 by no more than `0.000001`. This one-sided
tolerance admits a small rounding shortfall while ensuring scores remain within
`[0, 1]`.

## Validation

The domain rejects non-positive requested quantities, prices, and MOQs; negative
lead times and weights; empty identifiers; duplicate offer identifiers; empty offer
sets; unsupported weight totals; and NaN or infinite numeric values. Failures raise
`DomainValidationError` with a stable, relevant message.

## Hard constraint

An offer is eligible exactly when:

```text
requested quantity >= minimum order quantity
```

An ineligible offer is excluded before scoring. Its result records the offer, the
`minimum_order_quantity` constraint, requested quantity, MOQ, and an explanation.
If all offers are excluded, the result contains no ranked offer and
`recommended_offer` is `None`; it never fabricates a recommendation.

Constraint evaluation is kept separate from WSM scoring so another explicit hard
constraint can be added later without changing the normalization formula. T2 does
not introduce a generic rules engine.

## Normalization

For a cost criterion, where lower is better:

```text
normalized(x) = (max_value - x) / (max_value - min_value)
```

For a benefit criterion, where higher is better:

```text
normalized(x) = (x - min_value) / (max_value - min_value)
```

Unit price and lead time are cost criteria in T2. Benefit normalization is also
implemented and tested for later validated criteria.

Only eligible offers determine the minimum and maximum. When all eligible offers
have the same raw value for a criterion, each receives `1`. The criterion cannot
differentiate them, so this avoids division by zero without penalizing every offer.

## Weighted Sum Model and explanation

For every eligible offer:

```text
score(offer) = sum(weight(criterion) * normalized_value(offer, criterion))
```

The result does not expose only a total. Each contribution preserves this trace:

```text
raw value -> normalized value -> weight -> weighted contribution
```

The total is the exact Decimal sum of the recorded contributions. Normalized values,
contributions, and totals remain in the inclusive `[0, 1]` range for valid input.

## Deterministic ranking

Eligible offers are ordered by:

```text
total score descending
-> offer identifier ascending (lexicographic)
```

The implementation sorts explicitly. Repeated evaluations and permutations of the
same input produce the same complete result, including exclusion order.

## Manually calculated reference scenario

Requested quantity is 100.

| Offer | Supplier | Unit price | Lead time | MOQ | Constraint result |
| --- | --- | ---: | ---: | ---: | --- |
| Offer A | Supplier A | 10 | 10 days | 50 | Eligible: 100 >= 50 |
| Offer B | Supplier B | 12 | 5 days | 100 | Eligible: 100 >= 100 |
| Offer C | Supplier C | 9 | 8 days | 150 | Excluded: 100 < 150 |

Offer C is absent from both normalization ranges. Among A and B:

- Price range is 10–12. A normalizes to `(12 - 10) / (12 - 10) = 1`;
  B normalizes to `(12 - 12) / (12 - 10) = 0`.
- Lead-time range is 5–10. A normalizes to `(10 - 10) / (10 - 5) = 0`;
  B normalizes to `(10 - 5) / (10 - 5) = 1`.

Cost-focused profile:

| Offer | Price contribution | Lead-time contribution | Total | Rank |
| --- | ---: | ---: | ---: | ---: |
| Offer A | 1 x 0.7 = 0.7 | 0 x 0.3 = 0.0 | 0.7 | 1 |
| Offer B | 0 x 0.7 = 0.0 | 1 x 0.3 = 0.3 | 0.3 | 2 |

Urgent profile:

| Offer | Price contribution | Lead-time contribution | Total | Rank |
| --- | ---: | ---: | ---: | ---: |
| Offer B | 0 x 0.3 = 0.0 | 1 x 0.7 = 0.7 | 0.7 | 1 |
| Offer A | 1 x 0.3 = 0.3 | 0 x 0.7 = 0.0 | 0.3 | 2 |

Balanced profile gives A and B `0.5` each. Lexicographic offer-ID ordering places
Offer A first.

## Tests and verification

Local verification on 2026-09-17 used the existing Python 3.14.7 environment; the
project and CI compatibility baseline remains Python 3.11.

| Check | Result | Meaning |
| --- | --- | --- |
| `ruff format --check .` | Passed | All tracked Python files match project formatting. |
| `ruff check .` | Passed | Configured lint rules pass. |
| `python -m compileall application backend frontend decision_core odoo_adapter` | Passed | All source packages compile. |
| `pytest -m "not integration and not e2e" -v` | 57 passed, 4 deselected | Decision Core and existing T0/T1 fast behavior pass. |
| `python -m pip check` | Passed | Installed dependencies are consistent. |
| `git diff --check` | Passed | No whitespace errors were detected. |
| `podman compose ... config --quiet` | Passed | Current Compose configuration remains valid. |
| `pytest -m "integration and not e2e" -v` | Not executed | Containers were stopped and the known Windows forwarding helper failed at machine start. |
| GitHub Actions | Not yet executed | Remote CI evidence is pending the branch push/PR. |

The new unit coverage verifies every requested validation category, MOQ boundary and
all-excluded behavior, cost and benefit normalization, endpoints and intermediate
values, equal-value handling, eligible-only bounds, contribution reconstruction,
three reference profiles, score ranges, deterministic ties, repeated evaluation,
and input-order independence.

## Architectural boundary confirmation

`decision_core/` imports only Python standard-library modules and its own package.
It does not import Odoo names, `odoo_adapter`, `application.RfqSummary`, FastAPI,
Reflex, PostgreSQL/ORM code, HTTP, Docker, environment variables, or external
services. T2 changes no Odoo adapter, FastAPI route, Reflex component, database
layer, Compose definition, or Google Drive document.

## Known limitations and deferred functionality

T2 evaluates synthetic canonical objects only. It does not establish an Odoo mapping
for offers or connect recommendation output to the current RFQ API/UI. It supports
only MOQ eligibility and unit-price/lead-time scoring. It does not implement
purchase lines, products, receipts, historical supplier performance, delivery
reliability, quality or confidence scores, currencies, taxes, total cost, split
awards, optimization, TOPSIS, LLM explanations, persistence/history, new endpoints,
frontend pages, authorization changes, Odoo writes, or deployment.

## Review state

- Branch: `codex/t2-decision-core`
- Base: latest fetched `origin/main` at `f2494489f0d0b9970067cf8769c4843307c28a34`
- Final commit SHA: use `git rev-parse HEAD` after the handoff commit; a commit cannot
  contain its own final content-derived SHA. The exact SHA is included in the
  external final handoff and pull request.
- Merge state: not merged into `main`; intended to remain open for review.
