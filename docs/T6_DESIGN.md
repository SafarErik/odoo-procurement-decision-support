# T6 hybrid decision-input assembly design

## Status and boundary

T6 implements a narrow application path that combines semantically validated,
read-only Odoo facts with explicitly supplied, source-attributed terms. It is not a
production Odoo adapter and is not exposed through a new HTTP endpoint.

```text
Odoo JSON-2 -> OdooComparisonCaseFacts --+
                                           +-> assemble_decision_input()
supplemental terms + profile -------------+            |
                                                        +-> canonical input
                                                        +-> provenance manifest
```

Only `AssembledDecisionInput.canonical` is accepted by the unchanged
`evaluate_procurement_decision()` use case. The manifest remains in `application/`
and never enters `decision_core`.

## Immutable contracts

- `OdooComparisonCaseFacts` contains the explicit `purchase_group_id` identity, the
  complete bounded RFQ set, and the observation time.
- `OdooComparisonOfferFacts` contains stable order and commercial-supplier
  identities, state, company, currency, and all candidate lines.
- `OdooOrderLineFacts` contains exact product variant, UoM, quantity, quotation unit
  price, discount, taxes, currency, and company.
- `SupplementalOfferTerms` contains an explicitly supplied hard MOQ and
  supplier-promised lead time, each paired with `field_name`, `source_type`,
  `source_reference`, and timezone-aware `observed_at`.
- `CanonicalDecisionInput` groups the existing `PurchaseRequirement`,
  `SupplierOffer[]`, and `StrategicProfile` without changing them.
- `ProvenanceManifest` records a source for every canonical field.

Source attribution records who or what supplied a value and when it was observed.
It does not make a supplemental value verified, true, or authoritative.

## Mapping matrix

| Canonical field | Accepted source | Transformation | T6 status |
| --- | --- | --- | --- |
| Requirement ID | `purchase.order.purchase_group_id` | `odoo:purchase.order.group:<id>` | Validated Odoo fact |
| Requested quantity | Equal `purchase.order.line.product_qty` on every RFQ | Exact `Decimal` after equality check | Validated Odoo fact |
| Offer ID | `purchase.order.id` | `odoo:purchase.order:<id>` | Validated Odoo fact |
| Supplier ID | Order partner's `commercial_partner_id` | `odoo:res.partner:<id>` | Validated Odoo fact |
| Unit price | `purchase.order.line.price_unit` | Exact `Decimal`; no total-price derivation | Validated Odoo fact |
| Lead time | Explicit supplemental supplier promise | Exact `Decimal` plus required attribution | Supplemental, source-attributed |
| Hard MOQ | Explicit supplemental hard MOQ | Exact `Decimal` plus required attribution | Supplemental, source-attributed |
| Strategic profile | Caller/application configuration | Existing immutable profile plus attribution | Application input |

The following remain explicitly rejected as canonical fallbacks:

- `product.supplierinfo.min_qty` for hard MOQ;
- `product.supplierinfo.delay` for supplier-promised lead time; and
- `purchase.order.line.date_planned` for supplier-promised lead time.

The comparison reader deliberately does not request those three fields.

## Supported subset and explicit invariants

The assembler accepts only a complete case with at least three RFQs, one non-empty
common `purchase_group_id`, exactly one line per RFQ, one product variant, one UoM,
one currency, one company, one comparison quantity, supported open RFQ states,
zero discount, and no line taxes. Every Odoo and supplemental offer identity must be
unique, and the two identity sets must match exactly. All source references must be
non-empty and all observation timestamps timezone-aware.

The adapter first calls `search_count` and refuses a group larger than 20 offers or
40 total order lines. It then reads the exact persisted line-ID set and
commercial-partner identities through
JSON-2 with the existing read-only integration credential. Unsupported values are
preserved for the assembler to reject; they are not silently filtered.

## Stable fail-closed errors

`DecisionInputAssemblyError.code` distinguishes missing or unstable comparison
identity, insufficient or duplicate offers, unsupported line count or RFQ state,
missing/duplicate/unknown supplemental joins, missing MOQ or lead time, invalid
attribution, inconsistent product/UoM/currency/company/quantity, unsupported
discount or taxes, invalid Odoo numerics, and canonical domain validation failures.
The assembler never drops an offer or partially evaluates a malformed case.

## Fixture decision

An automated administrator writer was not implemented. The current repository has
read-only evidence for grouping and line reads, but it has no validated JSON-2 write
contract for the alternative-creation wizard, product defaults, tax defaults, or
safe teardown. Guessing those mutations would violate the evidence-first boundary.
The specification's approved fallback is therefore used: a controlled,
administrator-only Odoo UI procedure in `docs/T6_FIXTURE_SETUP.md`.

Normal application code cannot import that procedure. The dedicated integration
identity remains read-only and does not receive the alternatives feature group.
Live T6 contracts require `RUN_T6_LIVE_CONTRACTS=true`; without that explicit opt-in
they skip before looking for fixture records.

## Deliberate exclusions

T6 adds no Decision Core model, scoring, constraint, normalization, API, persistence,
frontend, Odoo write, conversion, aggregation, or supplier-selection behavior.
Historical supplier performance remains a later increment and must use separately
validated receipt and quality data rather than this provenance manifest.
