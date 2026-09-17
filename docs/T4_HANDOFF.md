# T4 handoff — Odoo decision-input mapping spike

## Status

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

The renewed API key restored the dedicated integration identity and enabled live
T4 discovery. The adapter gate still failed for two independently sufficient
reasons:

1. no explicit alternative-RFQ or shared-requirement relationship was available in
   the probed `purchase.order` schema; and
2. `purchase.order.line` read access is denied for the integration user.

No adapter, automatic evaluation flow, Decision Core change, frontend change,
public endpoint, mapping fixture, permission change, module install, or Odoo write
was introduced.

## Prerequisites and branch

- Branch: `codex/t4-odoo-decision-input-spike`.
- Base: fetched T3 merge commit
  `f123446dac7994d9ea4727225c5fe4a9d0a39cd5`.
- `docs/T3_HANDOFF.md` and
  `POST /api/v1/procurement/decisions/evaluate` were present.
- Focused Decision Core/application/API baseline: 62 passed.

## Models inspected

Live JSON-2 `fields_get`, access introspection, and bounded reads covered
`purchase.order`, `purchase.order.line`, `product.product`, `product.template`,
`product.supplierinfo`, `res.partner`, `res.currency`, `uom.uom`, and
`ir.module.module` for the narrow installed-module check.

Purchase and Inventory were installed. `purchase_requisition` was not returned as
installed. Candidate grouping fields `alternative_po_ids`, `source_po_id`, and
`requisition_id` were not returned by `purchase.order/fields_get`.

## Dedicated-user access

The user authenticated as non-admin `Procurement Integration`, user ID 7, company
ID 1 only. `purchase.order`, products, product templates, supplier information,
partners, currencies, UoMs, and the bounded module metadata are readable but cannot
be created, written, or unlinked. `purchase.order.line` returned read `False` and
HTTP 403 for `search_read`; create, write, and unlink are also denied.

The smallest permission requiring separate approval is read-only
`purchase.order.line` access for the existing custom group, with company-scoped
record behavior. No broader Purchase or Inventory role was assigned.

## Mapping decisions

Accepted in isolation:

- `purchase.order.id` as source offer identity;
- `res.partner.commercial_partner_id[0]` as stable supplier identity for observed
  company vendors;
- stable `currency_id` equality as a same-currency guard;
- the existing open-state mapping; and
- exact schema meanings for supplier-information `delay` and `min_qty`, without a
  canonical transformation.

Rejected:

- grouping RFQs by reference, origin, timestamps, currency, product coincidence,
  or inferred supplier relationships;
- display names as stable identifiers;
- order total or supplier master-data price as quoted unit price;
- line quantity as MOQ;
- conflating configured lead time, expected arrival, supplier promise, order date,
  and actual receipt; and
- silent defaults, conversion, or multi-line aggregation.

Unresolved or unavailable:

- procurement-case and requirement identity;
- requested quantity and all live order-line values;
- exact product variant, quotation UoM, quoted price, discount/tax result, and
  multi-line cardinality;
- supplier-information tier selection for MOQ; and
- canonical lead-time transformation and promised-date semantics.

## Grouping, lead time, MOQ, and data sufficiency

Alternative grouping is **not available** in the probed schema. Empty `origin`
values and similar timestamps do not replace an explicit relationship.

Lead time is **unresolved**. Supplier information exposes configured integer
`delay`; purchase orders expose `date_planned` as Expected Arrival and `date_order`
as Order Deadline. No supplier-promise field was validated, and the inaccessible
quotation line cannot be matched to a product-specific supplier row.

MOQ is **unresolved**. Supplier information exposes required float `min_qty`, but
multiple tiers can match and observed values include zero. Product, quantity, date,
company, currency, and UoM selection cannot be completed without quotation lines.
Zero cannot be passed to the current positive-MOQ domain model without inventing a
repair rule.

The data set is **insufficient and not fully inspectable**. Eleven non-cancelled
purchase documents were observed—seven open RFQs and four confirmed orders—all in
company 1 and USD. Supplier master data contains lead-time and MOQ values, but no
valid grouping or readable comparable line set exists.

## Verification classification

| Check | Result |
| --- | --- |
| Fetch and T3 ancestry | Passed. |
| Focused T2/T3 baseline | 62 passed. |
| Renewed-key existing live contract | 2 passed. |
| Focused T4 live contract | 11 passed, including access and schema/grouping checks. |
| Ruff format and lint | Passed. |
| Python compilation | Passed for all five source packages. |
| Fast tests | 80 passed, 14 integration/E2E tests deselected. |
| Dependency consistency | Passed. |
| Whitespace check | Passed. |
| Podman Compose configuration | Passed with the project-local `podman-compose` provider. |
| Live Odoo authentication | Passed as the dedicated user. |
| Live mapping evidence | Partial; grouping unavailable and lines blocked by permissions. |
| Fixture-only mapping evidence | None; no speculative fixture was added. |
| Odoo writes | None. |
| Google Drive changes | None. |

GitHub Actions was not executed because no pull request was created from this local
handoff and branch pushes do not trigger the repository's quality workflow.

## Security observations

The renewed key remained only in the ignored `.env`. No administrator credential,
database query, module install, ACL or record-rule change, or business-data write was
used. All probed mutation rights were denied. The temporary tunnel stayed bound to
localhost.

## Exact next step

Under separate approval, grant only company-scoped read access to
`purchase.order.line` for the existing custom group and choose an Odoo-supported
explicit requirement/alternative grouping mechanism. Revalidate both through the
database `/doc` page and bounded JSON-2 probes before creating controlled comparison
data or implementing an adapter. Do not begin T5.
