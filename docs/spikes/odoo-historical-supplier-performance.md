# T7 historical supplier-performance capability spike

## 1. Outcome and boundary

Assessment date: 2026-09-19.

**PENDING CONTROLLED LIVE ACCEPTANCE**

Standard Odoo 19 Community exposes a technically coherent candidate chain from a
purchase-order line to stock moves and receipt pickings, and its source documents
the actual-processing meaning of a completed stock move's `date`. The currently
configured integration identity cannot read either `stock.move` or `stock.picking`,
however, and no existing confirmed purchase line has a completed receipt. The
mandatory relationship, completion, partial/backorder, return, and timestamp
behaviour therefore has not been observed end to end.

There is an additional security blocker: the standard Odoo 19 ACL for every internal
user grants read, create, write, and unlink on `stock.move.line`. The live identity
inherits those rights through `Role / User`. T7 performed no mutation, but this means
the identity cannot currently be described as read-only for inventory-operation
lines. A `GO` is prohibited until this is remediated without granting a broad
Inventory role and the controlled fixture passes.

T7 adds no production KPI calculator, Odoo adapter, public endpoint, Decision Core
criterion, `SupplierOffer` field, `StrategicProfile` field, persistence schema, or
frontend behaviour. AC-07 remains unsatisfied.

## 2. Reproducible environment and method

The branch starts exactly at T6 merge commit
`01b9ff16d77934c2164d75ae6f4d938d98eedee3`. Discovery used only the configured
`Procurement Integration` API key through Odoo JSON-2. No administrator credential,
Odoo write, direct PostgreSQL access, or browser automation was used.

The runtime reported these installed Community modules:

| Module | Version | State | License |
| --- | --- | --- | --- |
| `base` | `19.0.1.3` | installed | LGPL-3 |
| `purchase` | `19.0.1.2` | installed | LGPL-3 |
| `purchase_stock` | `19.0.1.2` | installed | LGPL-3 |
| `purchase_requisition` | `19.0.0.1` | installed | LGPL-3 |
| `stock` | `19.0.1.1` | installed | LGPL-3 |

The authenticated identity is the existing dedicated internal, non-Settings-admin
user, limited to company ID 1, with timezone `Europe/Budapest`. Its direct groups
remain `Procurement RFQ API Reader` and `Role / User`; no Purchase or Inventory role
was added.

Discovery consisted of bounded `fields_get`, `check_access_rights`, `search_read`,
and `search_count` requests. Values below are redacted by type and shape; local
record IDs, names, and credentials are not evidence required by this spike.

## 3. Evidence matrix

The columns deliberately distinguish field existence, readability, relationship
validity, observed behaviour, semantic interpretation, and proposed use.

| Model | Field or relationship | Integration access and observed redacted shape | Business interpretation | Confidence and limitation | Disposition |
| --- | --- | --- | --- | --- | --- |
| `purchase.order` | `partner_id` | Readable many2one `[<partner-id>, <display>]` | Direct vendor contact selected on the PO | High for identity link; display name is never an identity | Accepted only as input to commercial-partner resolution |
| `res.partner` | `commercial_partner_id` | Readable many2one `[<commercial-id>, <display>]` | Stable commercial entity used by T6 | High; T6 already live-validated the mapping | Accepted supplier grouping identity |
| `purchase.order.line` | `order_id` | Readable many2one | Exact parent PO | High | Accepted relationship |
| `purchase.order.line` | `date_planned` | Readable stored datetime such as `<YYYY-MM-DD HH:MM:SS>`; label **Expected Arrival** | Operational expected arrival; defaults from vendor-pricelist lead time and remains editable | High for schema meaning; live lifecycle changes are not yet controlled | Candidate reference timestamp, never a supplier promise |
| `purchase.order.line` | `move_ids` | One2many relation to `stock.move`; attempting to read values returns HTTP 403 | Exact Odoo relationship to stock moves | Field existence high, integration readability denied, relationship behaviour not live-proven | Blocking pending narrow read access |
| `purchase.order.line` | `qty_received`, `qty_received_method` | Readable; confirmed stockable lines showed `0.0` and `stock_moves`, demo service lines used `manual` | Current received aggregate and its mechanism | Useful corroboration only; contains no completion timestamp or movement direction | Rejected as sole KPI source |
| `stock.move` | `purchase_line_id` | Metadata readable; record read denied and bounded `search_read` returns HTTP 403 | Exact purchase-line relationship defined by `purchase_stock` | High from schema/source, not live-readable | Required and blocking |
| `stock.move` | `state`, `quantity`, `product_uom`, `company_id` | Metadata readable; values denied | Completion state, actual moved quantity, UoM, and company | Mandatory for a defensible actual event | Required and blocking |
| `stock.move` | `date` | Metadata help: scheduled until done, then actual move-processing date; values denied | Candidate actual receipt timestamp only when `state = done` and direction is inbound | Source semantics high; live behaviour and timezone boundary pending | Primary actual-event candidate, blocking |
| `stock.move` | `location_usage`, `location_dest_usage` | Metadata readable; values denied | Source/destination direction, including supplier-to-internal receipt and internal-to-supplier return | Mandatory to distinguish receipts and returns | Required and blocking |
| `stock.move` | `origin_returned_move_id`, `returned_move_ids` | Metadata relations exist; values denied | Explicit move-level return chain | Mandatory for return exclusion | Required and blocking |
| `stock.picking` | `state`, `date_done` | Metadata readable; record read denied and bounded `search_read` returns HTTP 403 | Transfer completion corroboration; `date_done` also covers cancellation, so state is mandatory | High semantic confidence; live value unavailable | Required corroboration, blocking |
| `stock.picking` | `backorder_id`, `backorder_ids` | Metadata relations exist; values denied | Explicit split/backorder chain | Required for partial-receipt evidence | Required and blocking |
| `stock.picking` | `return_id`, `return_ids` | Metadata relations exist; values denied | Explicit picking-level return chain | Required for return evidence | Required and blocking |
| `stock.move.line` | `move_id`, `picking_id`, `state`, `quantity`, `date`, locations | Readable; representative rows include completed inventory adjustments and assigned internal moves | Detailed operations, not necessarily vendor receipts | Cannot reach `purchase_line_id`; `date` changes for several events and is not selected as the authoritative actual timestamp | Rejected as a standalone history source |
| `purchase.order` | `effective_date` | Readable stored datetime; all five confirmed orders returned `false` | Completion date of the first non-return receipt | Order-level first receipt is wrong for line completion and partial/multiple receipts | Rejected for the primary KPI |
| `purchase.order` / `res.partner` | `on_time_rate` | Field metadata readable; value read returns HTTP 403 because its compute traverses denied stock moves | Odoo's quantity-weighted rate over direct partner, normally 365 days | No separate sample size; direct-partner grouping differs from T6; source excludes semantic controls required here | Rejected as project KPI input |
| `product.supplierinfo` | `delay` | Previously readable configured integer | Planning lead time from PO confirmation to warehouse receipt | Master data, not history | Rejected |

Observed existing data does not substitute for a controlled fixture. Five confirmed
orders contained eight lines. All had `effective_date = false`; five orders had no
receipt and two had pending receipts. Every line had `qty_received = 0.0`. A bounded
`stock.move.line` read returned inventory-adjustment and internal-movement rows, not
an unambiguous purchase receipt. A relational domain through
`move_id.purchase_line_id` returned HTTP 403. No existing record was heuristically
joined by product, origin text, timestamps, or names.

## 4. Supplier identity

The recommended grouping key remains the T6 identity:

```text
purchase.order.partner_id
    -> res.partner.commercial_partner_id
    -> odoo:res.partner:<commercial-partner-id>
```

This groups child vendor contacts under the stable commercial entity without using
names. It is compatible with `OdooComparisonCaseReader` and the canonical
`SupplierOffer.supplier_id` already used by T6.

Odoo's computed `on_time_rate` is not reused. Odoo 19 source searches purchase lines
by their direct `partner_id`, sums quantities from done moves completed no later than
`date_planned`, and divides by ordered quantity. It does not expose the supporting
sample size through the field, and direct-partner grouping can fragment the same
commercial supplier. Reading the computed value is also denied for the integration
identity.

## 5. Purchase-to-receipt relationship

The only accepted candidate path is the explicit ORM relationship:

```text
purchase.order.id
    -> purchase.order.line.order_id
    -> purchase.order.line.move_ids
    <-> stock.move.purchase_line_id
    -> stock.move.picking_id
    -> stock.picking
```

`stock.move.product_id`, `product_uom`, and `company_id` must match the purchase line
and order. `stock.move.state = done`, `location_usage = supplier`, and
`location_dest_usage = internal` define the proposed ordinary warehouse-receipt
direction. Dropship receipts, internal transfers, inventory adjustments, scrap, and
returns are outside this initial candidate.

The relationship is proven by runtime metadata and matching Odoo 19 source but not
yet by readable live records. This is sufficient to justify a controlled test, not
a `GO` or production adapter.

## 6. Reference and actual timestamps

### Reference

`purchase.order.line.date_planned` is **Expected Arrival**. Runtime help says it
defaults from the vendor-pricelist lead time and then today's date. Official Odoo 19
documentation describes Expected Arrival as Order Deadline plus Vendor Lead Time,
and notes that changing a receipt's scheduled date does not change the PO-line
expected arrival. Odoo source also allows the line date to be updated and propagates
changes to unvalidated receipts.

The field is therefore an operational schedule reference. It is not evidence of a
supplier-confirmed promise and must never be mapped to T6's
`supplier_promised_lead_time_days`.

### Actual

`stock.move.date` is the strongest candidate. Runtime metadata states that it is the
scheduled date until the move is done and the actual move-processing date after
completion. A usable event additionally requires `state = done`, a positive actual
`quantity`, the exact `purchase_line_id`, supplier-to-internal direction, matching
product/UoM/company, no return relationship, and a done receipt picking.

`stock.picking.date_done` alone is insufficient because its help covers both
processed and cancelled transfers. It is proposed as corroboration: for the
controlled subset, a done move's actual timestamp must equal its done picking's
`date_done`. `stock.move.line.date` is rejected as the primary timestamp because its
metadata says it changes on quantity increases, picked-state changes, and completion.

Odoo JSON-2 returns datetimes without an offset in this environment. The existing
adapter interprets them as UTC. The controlled fixture must prove comparisons around
the configured `Europe/Budapest` timezone before a production policy is approved.

## 7. Primary KPI candidate

Exactly one candidate is recommended for controlled acceptance:

### `delivery_schedule_adherence`

| Property | Definition |
| --- | --- |
| Business meaning | Percentage of eligible completed purchase-order-line receipt obligations whose full current ordered quantity reached the internal warehouse no later than Odoo's line-level Expected Arrival. It measures adherence to the operational Odoo schedule, not a supplier promise. |
| Supplier grouping | Stable commercial-partner identity, compatible with T6. |
| Measurement grain | One eligible completed stock-move-backed purchase-order line. |
| Per-line actual event | Earliest done inbound move timestamp at which cumulative eligible received quantity reaches `product_qty`. |
| Numerator | Count of eligible lines whose completion timestamp is less than or equal to `date_planned`. |
| Denominator | Count of all eligible completed lines in the window. |
| Formula | `adherent_line_count / eligible_completed_line_count * 100`. |
| Reporting range | `0.00` through `100.00` percent. |
| Rounding | Decimal arithmetic, round half up to two decimal places only for presentation. |
| Historical window | Half-open 365-day window by completion timestamp: `[as_of - 365 days, as_of)`. The duration is an explicit project policy, not borrowed as proof from Odoo's computed field. |
| Sample size | `eligible_completed_line_count`, returned separately from the percentage. |
| Insufficient data | Withhold the KPI when sample size is below 3; return the sample size and `insufficient_history`. This PoC threshold limits fixture size and is not a statistical-confidence claim. |
| Data-quality output | Separate warning codes for every excluded or unusual record; never silently discard. |

The candidate is deliberately line-count weighted. Summing raw quantities across
different products and UoMs would let large numeric quantities dominate the supplier
result and is not comparable without a separately validated normalization policy.

## 8. Edge-case policy

| Case | Classification | Candidate rule or reason |
| --- | --- | --- |
| Partial receipt still open | Excluded with documented reason | Not a completed line; report `incomplete_receipt`. It may enter a later window after completion. |
| Multiple incoming receipts | Included with documented rule | Sort eligible done inbound moves by actual timestamp and use the first point where cumulative quantity reaches the final ordered quantity. |
| Backorder | Included with documented rule | Require the explicit picking `backorder_id` chain and the same purchase-line relationship; completion uses cumulative quantity across the chain. |
| Supplier return | Excluded with documented reason | Any related move/picking return makes the line ineligible in T7; report `supplier_return_observed`. Timeliness and quality/replacement policy must not be conflated. |
| Cancelled residual move | Unsupported and fail-closed | Exclude the line and report `cancelled_receipt_obligation`; current ordered quantity may no longer preserve the original obligation. |
| Ordered-quantity change | Unsupported and fail-closed | No approved immutable quantity snapshot exists. Exclude when a decrease/cancellation is observable; broader change-history detection remains unresolved. |
| Replacement receipt | Unsupported and fail-closed | Exclude any line with return/replacement activity until the exact replacement relationship and counting rule are separately proven. |
| Missing `date_planned` | Excluded with documented reason | No comparison reference; report `missing_expected_arrival`. |
| Missing completion timestamp | Unsupported and fail-closed | A done move/picking without the required actual timestamps is inconsistent evidence. |
| Timezone boundary | Unresolved and blocking `GO` | Interpret JSON-2 values as UTC, but require controlled evidence around a Budapest calendar boundary before production use. |
| Other company | Excluded by security boundary | Query only the integration user's allowed company and require equality across order, line, move, and picking. Outside-company reads must return no records. |
| Ambiguous relationship | Unsupported and fail-closed | Never join by product, reference text, partner name, or timing proximity. |
| Over-receipt | Included with warning | Use the timestamp when cumulative quantity first reaches ordered quantity; report `over_receipt` and do not improve the KPI for excess units. |
| Dropship receipt | Excluded with documented reason | The initial definition requires supplier-to-internal movement. A customer destination needs a separate business decision. |
| Service or manual receipt line | Excluded with documented reason | Require `qty_received_method = stock_moves`; manual values do not provide an independently verified physical event. |

Cancelled residuals, quantity changes, replacements, and timezone boundaries remain
blocking for an unrestricted production implementation. The narrow controlled
fixture intentionally exercises on-time, late, backorder, and return records; it
does not turn the proposed policies into a generic adapter.

## 9. Security and permission result

Live `check_access_rights` returned:

| Model | Read | Create | Write | Unlink | T7 interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| `purchase.order` | yes | no | no | no | Existing boundary preserved |
| `purchase.order.line` | yes | no | no | no | Existing T5 boundary preserved |
| `stock.picking` | **no** | no | no | no | Required receipt read blocked |
| `stock.move` | **no** | no | no | no | Required relationship and actual-event read blocked |
| `stock.move.line` | yes | **yes** | **yes** | **yes** | Not read-only; inherited standard internal-user ACL |
| `stock.picking.type` | yes | no | no | no | Metadata/reference read only |
| `stock.location` | yes | no | no | no | Location reference read only |

The standard Odoo 19 stock ACL file grants full `stock.move.line` CRUD to
`base.group_user`. Odoo ACL permissions are additive, so adding a read-only ACL does
not revoke that inherited mutation capability. Do not attempt to solve this by
granting `stock.group_stock_user`; that would add broad picking and move mutation
rights.

Before fixture creation, a separate approved security decision must establish an
effective read-only inventory-history identity or an equivalent narrowly scoped
read projection. It must provide only company-scoped reads of `stock.move` and
`stock.picking`, remove or isolate effective `stock.move.line` mutation capability,
and re-run create/write/unlink denial. T7 does not prescribe or install that security
change automatically.

## 10. Controlled acceptance gate

`docs/T7_FIXTURE_SETUP.md` defines the human-admin-only steps. The fixture uses exact
Source Document markers and one commercial supplier, product, UoM, and company. It
contains a full on-time receipt, a full late receipt, a two-step late backorder, and
a receipt followed by a supplier return. The first three are the proposed KPI sample;
the return case must be excluded with a warning. Expected controlled result:
`33.33%`, sample size `3`.

Live T7 tests require `RUN_T7_LIVE_CONTRACTS=true`. The first contract requires the
post-remediation read-only security boundary and validates the schema. The second is
intentionally dormant until that remediation and the exact fixture exist; it bounds
all reads by the four exact markers and proves the relationship/timestamp scenarios
without adding production calculation code.

## 11. Rejected interpretations

- `product.supplierinfo.delay` is configured planning data, not history.
- `purchase.order.line.date_planned` is Expected Arrival, not a supplier-confirmed
  promise or a canonical quotation lead time.
- `purchase.order.effective_date` is the first receipt completion and cannot measure
  full line completion across partial receipts.
- `purchase.order.receipt_status` is a coarse current state without sample evidence.
- `purchase.order.line.qty_received` has no actual-event timestamp or direction.
- `res.partner.on_time_rate` has no exposed sample size, uses direct partner identity,
  applies Odoo's quantity-weighted policy, and is unreadable to this identity.
- `stock.move.line.date` is not selected as the authoritative receipt timestamp.
- Product/name/origin/timestamp proximity is never a relationship join.

## 12. Sources

- [Odoo 19 Purchase & Vendor dashboard](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/purchase_dashboard.html)
- [Odoo 19 lead times](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/lead_times.html)
- [Odoo 19 purchase/stock order implementation](https://github.com/odoo/odoo/blob/19.0/addons/purchase_stock/models/purchase_order.py)
- [Odoo 19 supplier on-time-rate implementation](https://github.com/odoo/odoo/blob/19.0/addons/purchase_stock/models/res_partner.py)
- [Odoo 19 stock picking implementation](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_picking.py)
- [Odoo 19 stock move implementation](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_move.py)
- [Odoo 19 stock move-line implementation](https://github.com/odoo/odoo/blob/19.0/addons/stock/models/stock_move_line.py)
- [Odoo 19 stock ACLs](https://github.com/odoo/odoo/blob/19.0/addons/stock/security/ir.model.access.csv)

Official documentation corroborates that Odoo reports on-time quantities against
Expected Arrival. The repository's candidate definition is intentionally narrower,
line-count weighted, sample-size explicit, commercial-partner grouped, and
fail-closed on unsupported history.
