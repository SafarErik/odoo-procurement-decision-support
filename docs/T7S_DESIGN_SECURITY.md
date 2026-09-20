# T7-S company-scoped read-only inventory-history projection

## Scope and decision

T7-S is a separate security prerequisite for the T7 historical supplier-performance
capability spike. It does not implement a historical KPI, change the Decision Core,
or make historical facts available through the public application API.

The selected mechanism is a narrowly bounded public model method,
`procurement.inventory.history.projection.read_bounded_history`, implemented by the
local Odoo addon `t7s_inventory_history_projection`. The model is an
`AbstractModel`: it has no database table, generic record collection, menu, view, or
model ACL. A dedicated non-internal caller receives only the custom projection group
and invokes the method through Odoo 19 JSON-2.

The original `Procurement Integration` identity and its T6 API key remain unchanged.
They must not be reused for T7-S because the standard internal-user role inherits
generic `stock.move.line` mutation access. T7-S therefore uses a separate key in
`ODOO_T7S_API_KEY` for a portal/non-internal technical caller.

## Odoo-native alternatives

| Mechanism | Security and complexity assessment | Decision |
| --- | --- | --- |
| Minimal read-only `_auto = False` projection model | Avoids a synchronized copy, but normally presents generic `search`, `read`, export, domain, ordering, and pagination surfaces. Enforcing a mandatory date window, exact relationship identifiers, and a strict count on every generic ORM path would require overriding several ORM operations. A SQL view would also add raw SQL and a database-shaped schema where a fixed method result is sufficient. | Rejected |
| Bounded custom model method returning sanitized dictionaries | Accepts a closed parameter set, validates every caller-controlled bound before reading, fixes the result schema, and exposes no generic records. It remains on Odoo ORM/JSON-2 and needs no persistence or synchronization. | **Selected** |
| Stored projection model | Adds synchronization, retention, write paths, stale-copy risk, cleanup, and another persistence schema without demonstrated need. | Rejected |
| `TransientModel` | Still creates writable temporary rows and cleanup behaviour while offering no security advantage for an on-demand query. | Rejected |
| Custom HTTP controller | Could sanitize output but would create an authentication and routing surface outside the requested Odoo JSON-2 model-method contract. | Rejected |
| Direct ACL access to stock models | Odoo ACLs are additive; the existing internal identity already inherits move-line mutation rights. Broad Inventory access would expose more fields and operations. | Prohibited |

The selected method is safer and simpler because it has one callable operation, one
fixed request contract, one fixed response schema, and no stored or generically
searchable projection records.

## Identity and authorization boundary

The caller must satisfy all of the following:

1. it is a dedicated non-internal Odoo user;
2. it belongs to
   `t7s_inventory_history_projection.group_inventory_history_projection_reader`;
3. it has exactly one authorized/default company for this proof of concept;
4. it has no Purchase or Inventory role and no internal-user role; and
5. it uses a separate, ignored local API key.

The custom group grants no `ir.model.access` row and implies no other group. The
method checks the group explicitly. It then requires the requested `company_id` to
equal the active `env.company.id` and to belong to the caller's `company_ids`.
Changing the JSON-2 context cannot authorize a company absent from the user.

Generic `read`, `search_read`, `create`, `write`, and `unlink` are not granted on the
projection. Generic reads and every mutation remain denied on `stock.picking`,
`stock.move`, and `stock.move.line` for the dedicated caller.

## Request contract

The method accepts named JSON-2 parameters only:

| Parameter | Constraint |
| --- | --- |
| `company_id` | Positive integer; must be the active authorized company |
| `date_from` | Strict UTC-naive Odoo format `YYYY-MM-DD HH:MM:SS` |
| `date_to` | Same format; exclusive, later than `date_from`, and not in the future |
| `purchase_order_line_ids` | Non-empty list of unique positive IDs; maximum 50 |
| `limit` | Positive integer; maximum 200 stock-move facts |

The half-open historical window must not exceed 366 days. The exact line IDs are an
intentional T7-S restriction: the existing T6 identity can locate the four explicit
fixture orders and lines, while the projection caller cannot arbitrarily enumerate
purchase or inventory history. Missing bounds, duplicate IDs, unknown parameters,
future end dates, excessive ranges, and excessive limits are rejected.

## Fixed response contract

The method returns envelope version `t7s.inventory_history.v1`, the accepted company
and time bounds, `result_count`, and `records`. Each record contains exactly:

| Field | Validated source and meaning |
| --- | --- |
| `company_id` | Common company across PO line, PO, move, and picking |
| `commercial_partner_id` | `purchase.order.partner_id.commercial_partner_id`; T6-compatible supplier identity |
| `purchase_order_id` | Stable Odoo PO identity |
| `purchase_order_line_id` | Stable measurement-candidate line identity |
| `product_id` | Product variant shared by line and move |
| `product_uom_id` | UoM shared by line and move; conversions are unsupported |
| `expected_arrival_at` | `purchase.order.line.date_planned`, Odoo **Expected Arrival**; an operational schedule, not a supplier promise |
| `stock_move_id` | Stable done stock-move identity |
| `stock_picking_id` | Stable done transfer identity |
| `move_processed_at` | `stock.move.date` for a done move; Odoo defines it as actual move processing at that state |
| `ordered_quantity` | `purchase.order.line.product_qty`, serialized as a decimal string |
| `completed_quantity` | positive done `stock.move.quantity`, serialized as a decimal string |
| `state` | Must be exactly `done` |
| `source_location_usage` | Only `supplier` for receipt or `internal` for supplier return |
| `destination_location_usage` | Only `internal` for receipt or `supplier` for supplier return |
| `backorder_of_picking_id` | `stock.picking.backorder_id`, only when the referenced picking remains in the bounded result |
| `return_of_move_id` | `stock.move.origin_returned_move_id`, only for an explicit supplier return whose origin remains in the result |
| `return_of_picking_id` | `stock.picking.return_id`, required to agree with the returned move's original picking |

No names, display values, chatter, users, credentials, unrestricted record payloads,
or rejected KPI fields are returned. `stock.picking.date_done` is read only as
corroboration: the method requires a done picking and equality with the done move's
processing timestamp, but does not expose it as a second business event.

## Elevated ORM access

Elevated access is technically unavoidable because the dedicated caller must remain
unable to read all underlying generic inventory models. The addon therefore uses
`sudo()` only inside five private bounded readers. It never returns a sudoed
recordset and never uses raw SQL.

Before the first elevated read, the public method validates the caller group,
company, exact line-ID list, date range, and result limit. Each subsequent
`search_fetch` has fixed field names and a prebuilt domain:

- PO lines: exact requested IDs plus company, at most 51;
- POs: exact IDs derived from those lines plus company;
- partners: exact IDs derived from those POs;
- stock moves: exact requested line IDs, company, half-open date window, at most
  `limit + 1`; and
- pickings: exact IDs derived from those moves, company, and the same time window.

The extra row detects truncation and rejects the entire call. Relationship targets
for returns and backorders must already be present inside the same bounded result;
the method does not chase them outside the requested range. Only immutable primitive
dictionaries leave the elevated recordsets.

## Fail-closed semantics

The whole call fails if it observes a non-done move or picking, a picking type that
does not match its validated direction (`incoming` for supplier-to-internal receipts
or `outgoing` for explicit internal-to-supplier returns), non-positive quantity,
missing date, cross-company relationship, mismatched product or UoM, missing
PO/supplier/picking relationship, unsupported or mixed movement direction, timestamp
disagreement, backorder leaving the bounded result, or a return whose move and
picking relationships disagree. The method does not silently omit an unsupported row
and does not calculate eligibility, a percentage, or sample size.

## Verification layers

- `tests/test_t7s_projection_policy.py` tests strict request validation, exact output
  fields, cross-company rejection, unsupported states and directions, bounded
  backorders/returns, absence of raw SQL, absence of generic ACLs, and absence of
  implied broad roles.
- `tests/integration/test_live_odoo_contract.py` contains an opt-in T7-S JSON-2
  contract. It proves a same-company bounded call, direct-model denial, projection
  CRUD denial, cross-company rejection, and rejection of unbounded requests.
- The original T7 controlled fixture test now consumes this projection rather than
  reading generic stock models.

Live contracts remain disabled until the administrator completes
`docs/T7S_MANUAL_SETUP.md`.
