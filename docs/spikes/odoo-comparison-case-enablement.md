# T5 Odoo comparison-case enablement — final evidence

## 1. Status and boundary

Assessment dates: 2026-09-17 through 2026-09-18.

**T5 COMPLETE — NO-GO — ADAPTER DEFERRED**

Phase A recorded read-only discovery and the exact mutation proposal. On 2026-09-18,
the user approved that proposal and confirmed a database backup. Phase B installed
the standard module, added the one read-only line ACL, restricted the alternatives
feature to the human administrator, and revalidated the dedicated identity through
JSON-2. No direct PostgreSQL access or application Odoo write occurred.

The final adapter decision is `NO-GO`. The standard grouping capability and
least-privilege order-line reads are now available, but supplier-offer lead time
remains unresolved and the only discovered `min_qty` field does not have hard-MOQ
business meaning. The approved pre-fixture gate therefore stopped Phase B before
creating synthetic business records.

## 2. Exact local runtime findings

Read-only JSON-2 calls against `procurement_poc` authenticated as the existing
non-administrator `Procurement Integration` user (ID 7). The identity remains limited
to company ID 1 and has only the direct `Procurement RFQ API Reader` and `Role / User`
groups.

`ir.module.module/search_read` returned exactly one local module named
`purchase_requisition`:

| Property | Observed value |
| --- | --- |
| Display name | `Purchase Agreements` |
| State | `uninstalled` |
| License | `LGPL-3` |
| Application flag | `false` |

`res.config.settings/fields_get` returned the boolean
`module_purchase_requisition`, labelled **Purchase Agreements**. This proves that the
exact Community build contains the standard module and can enable it through the
supported Purchase setting. It does not require an Enterprise edition change or a
third-party module. Enabling it is still a module installation and therefore requires
explicit approval.

The existing live T4 contract re-passed unchanged: `purchase.order.line` read is
denied, its bounded `search_read` remains unavailable, the module is not installed,
and `purchase_group_id`, `alternative_po_ids`, and `requisition_id` are not yet in
the runtime `purchase.order` schema.

Those statements describe the Phase A checkpoint. After approval, Phase B changed
the module state to `installed` and added one read-only line ACL. The final dedicated
identity still has only company ID 1 and direct groups `Procurement RFQ API Reader`
and `Role / User`.

The standard settings checkbox for Purchase Alternatives initially implied the
feature group to all internal users. A live `has_group` assertion caught that
`Procurement Integration` had inherited it. The checkbox was disabled, and
`purchase_requisition.group_purchase_alternatives` was instead assigned directly to
`Mitchell Admin`. Final `has_group` is false for the integration identity, while the
group UI shows exactly one user: `Mitchell Admin`.

## 3. Standard capability verified after installation

The matching Odoo 19 standard module source and final JSON-2 `fields_get` agree on
the following runtime contract.

| Model | Field | Expected type and purpose |
| --- | --- | --- |
| `purchase.order.group` | `order_ids` | One2many to `purchase.order`; the technical persisted call-for-tender group. |
| `purchase.order` | `purchase_group_id` | Stored many2one to `purchase.order.group`; the candidate stable comparison-case identity. |
| `purchase.order` | `alternative_po_ids` | Related one2many over the group's open RFQs. |
| `purchase.order` | `requisition_id` | Optional many2one to `purchase.requisition`; an agreement link, not the alternative group itself. |
| `purchase.requisition` | `purchase_ids` | RFQs/orders generated from one blanket order or purchase template. |

Standard source shows that creating alternatives through the wizard creates or
extends one
`purchase.order.group`. The stable candidate group key is therefore
`purchase.order.purchase_group_id[0]`, not names, timestamps, `origin`, product
coincidence, vendor coincidence, currency, quantity, or nearby record IDs.

The installed module also creates
`purchase_requisition.group_purchase_alternatives`, labelled
**Manage Purchase Alternatives**. That group controls the Alternatives tab and its
Create Alternative and Compare Product Lines actions. It must be assigned only to
the human fixture operator, never to the integration identity.

## 4. Least-privilege access result

The only integration-identity permission change is one read-only model ACL
for `purchase.order.line` on the existing `Procurement RFQ API Reader` group:

| Model | Read | Create | Write | Unlink |
| --- | --- | --- | --- | --- |
| `purchase.order.line` | allowed | denied | denied | denied |

Odoo's installed `purchase` module already has a global
`purchase_order_line_comp_rule` with domain
`[('company_id', 'in', company_ids)]`. Because the identity has only company ID 1,
this existing global rule is the narrow company boundary. No duplicate record rule
or Purchase/User, Purchase/Administrator, Inventory/User, Settings, or administrator
role was added.

The adapter-facing grouping read can use `purchase_group_id` on already permitted
`purchase.order` records. The integration identity can read that field while direct
`purchase.order.group` and `purchase.requisition` model rights remain denied, so no
additional ACL was needed.

The ACL was added through the supported Technical / Security / Access Rights UI to
the exact existing custom group. Bounded line `search_read` and order `order_line`
traversal now succeed; create, write, and unlink remain denied. Every observed line
belongs to company 1, and an explicit outside-company domain returns no rows.

## 5. Controlled fixture stop result

No T5 business fixture was created. The approved operation order required module,
schema, access, company-isolation, and semantic validation before creating data, and
required Phase B to stop while any critical semantic mapping remained unresolved.

The live fields retained the Phase A meanings: `product.supplierinfo.min_qty` is a
price-tier threshold, `product.supplierinfo.delay` is configured planning time, and
`purchase.order.line.date_planned` is Expected Arrival. Those values cannot satisfy
the canonical hard-MOQ and supplier-offer lead-time contracts. Creating the proposed
three suppliers, product, supplier rows, and alternative RFQs would therefore prove
UI mechanics but not a valid canonical case.

No records with the proposed `T5 Supplier A/B/C` or `T5-COMP-001` identifiers were
created. Existing demo RFQs were queried read-only and were not grouped heuristically.

## 6. Final mapping matrix

| Canonical concept | Candidate source | Runtime shape / meaning | Dedicated-user access | Transformation | Status | Caveat |
| --- | --- | --- | --- | --- | --- | --- |
| Procurement case ID | `purchase.order.purchase_group_id` | Stored many2one to persisted `purchase.order.group` | Field read allowed on permitted orders | `odoo:purchase.order.group:<id>` | `ACCEPTED` | Technical source identity is explicit; no controlled grouped record was created after the stop gate. |
| Requirement ID | Same alternative group, or an explicit agreement if used | No authoritative shared business-requirement record established | Group field readable | None | `UNRESOLVED` | A technical comparison group does not itself prove one business requirement. |
| Requested quantity | `purchase.order.line.product_qty` | Stored float | Read allowed | Exact decimal text only after invariant checks | `UNRESOLVED` | No controlled alternatives exist to prove equality and authority. |
| Offer ID | `purchase.order.id` | Stable integer source record | Read allowed | `str(id)` | `ACCEPTED` | Conditional on membership in a valid group. |
| Supplier ID | `partner_id -> commercial_partner_id` | Stable commercial partner ID | Read allowed | `str(commercial_partner_id[0])` | `ACCEPTED` | Revalidate child-contact behavior in the fixture. |
| Product ID | `purchase.order.line.product_id` | Exact product variant | Read allowed | `str(id)` | `UNRESOLVED` | Access is proven; cross-alternative equality is not. |
| Unit of measure | `purchase.order.line.product_uom_id` | Quotation-line UoM | Read allowed | Stable ID equality; no conversion | `UNRESOLVED` | Access is proven; cross-alternative equality is not. |
| Unit price | `purchase.order.line.price_unit` | Stored actual quotation-line unit price | Read allowed | Decimal text without using `amount_total` | `UNRESOLVED` | Line values are readable, but no controlled offer set exists. |
| Currency | `purchase.order.currency_id` and line-related currency | Stable currency ID | Order read allowed | Stable ID equality | `ACCEPTED` | No conversion is authorized. |
| Discount / tax | line `discount`, `tax_ids`, `price_unit_discounted` | Runtime-verified fields; `price_unit_discounted` is computed | Line read allowed | Proposed guard: discount must be zero and `tax_ids` empty | `UNRESOLVED` | No controlled case proves the guard; a later adapter must reject unsupported values. |
| Lead time | line `date_planned`; supplier info `delay` | Expected arrival; configured planning delay | Metadata only / supplier info readable | None accepted | `UNRESOLVED` | No validated supplier-offer promise date or semantically valid duration start exists. |
| MOQ | `product.supplierinfo.min_qty` | Quantity needed to benefit from a vendor-price tier | Read allowed | None | `REJECTED` | Runtime help does not define a hard minimum accepted order; it cannot drive the Decision Core's hard MOQ constraint. |
| RFQ state | `purchase.order.state` | Explicit lifecycle selection | Read allowed | Existing open-state mapping | `ACCEPTED` | Fixture must exclude `purchase` and `cancel`. |
| Company | order and line `company_id` | Stable company ID and global rule boundary | Order and line read allowed | Stable ID equality | `ACCEPTED` | Company 1 observed; outside-company domain returned no rows. |
| Source traceability | model, record ID, observation time | Source identity plus client observation timestamp | Available for permitted orders and lines | Preserve without business defaulting | `UNRESOLVED` | No complete controlled grouped case exists. |

## 7. Lead-time and MOQ gate

### Lead time

Runtime `fields_get` describes `purchase.order.line.date_planned` as **Expected
Arrival** and says it defaults from vendor-pricelist lead time, then today's date.
It describes `product.supplierinfo.delay` as the days between purchase-order
confirmation and warehouse receipt, used for automatic planning. The standard Odoo
implementation calculates expected arrival from the order deadline plus the selected
supplier-information delay.

This is configured operational planning data, not a recorded supplier quotation
promise. `date_order` is **Order Deadline**, not an offer-observation or dispatch
date. T5 therefore has no deterministic, semantically valid transformation to
the current canonical `lead_time_days`. A manually edited expected-arrival value in
a controlled fixture would still need an explicit business rule and provenance that
the schema does not encode.

### MOQ

Runtime `fields_get` states that `product.supplierinfo.min_qty` is the quantity needed
to benefit from the supplier row's unit price. Odoo filters seller rows by partner,
date range, product variant/template applicability, quantity converted to the
supplier UoM, and company; the selected row is then ordered by discounted price,
sequence, and record ID. The quotation line exposes computed
`selected_seller_id`, which is now readable and can identify the price row selected
by Odoo.

That selection is deterministic pricing-tier behavior, but it does not establish a
hard supplier order minimum. The Decision Core interprets MOQ as an eligibility
constraint and requires it to be positive. Reusing the pricing threshold would
change business meaning, while zero-tier values cannot be repaired to a positive
value. The current MOQ candidate is therefore `REJECTED`, not defaulted.

This is an independently sufficient `NO-GO` condition for the current adapter scope
unless a different authoritative hard-MOQ source is produced and validated.

## 8. Phase B operations and stop gate

The user confirmed the database backup and explicitly approved Phase B on
2026-09-18. The administrator then performed the supported UI changes described in
sections 1 through 4. Read-only JSON-2 validation confirmed module state, exact
fields, effective model rights, company scoping, line traversal, and unchanged
denial of unrelated models and mutation operations.

The global Purchase Alternatives checkbox briefly implied the feature group to the
integration identity. Validation detected that overgrant immediately. The setting
was disabled and the group was assigned directly to `Mitchell Admin`; the final
identity contract proves the integration user does not have it.

The approved stop condition then applied: hard MOQ is still rejected and supplier-
offer lead time is still unresolved. Phase B therefore did not create the section 5
business fixture and did not implement an adapter.

## 9. Security, data impact, and rollback

Security impact is limited to exposing company-permitted purchase-order-line values
to the existing integration identity. Create, write, unlink, Settings, Purchase,
Inventory, and administrator privileges remain denied. Module installation adds
standard Purchase Agreements models and UI for authorized human users but must not
change the integration identity's direct groups.

Data impact consists of the installed module's schema/data records, one ACL, and one
direct human feature-group assignment. No T5 supplier, product, supplier-information,
RFQ, or purchase-order-line record was created.

Rollback, in reverse order:

1. remove `Mitchell Admin` from **Manage Purchase Alternatives**;
2. delete the read-only line ACL through supported Odoo UI;
3. only after a fresh database backup, uninstall Purchase Agreements through Apps if
   full schema rollback is required;
4. rerun T4 contracts and verify line read is denied and grouping fields are absent.

Module uninstall is a destructive database operation and is not an ordinary restart
or first-line rollback. Never delete the named volumes for this validation.

## 10. Verification

### Phase A checkpoint

| Check | Result |
| --- | --- |
| Branch contains T4 merge `e8eccf7` | Passed. |
| Odoo HTTP boundary | HTTP 200. |
| Full live integration selection | 16 passed, including 13 Odoo contracts. |
| T5 Phase A module metadata | `purchase_requisition` available, LGPL-3, uninstalled. |
| T5 Phase A exact line/supplier field metadata | Verified read-only through `fields_get`. |
| Ruff format and lint | Passed. |
| Python compilation | Passed for all five source packages. |
| Fast tests | 80 passed, 16 integration/E2E tests deselected. |
| Dependency consistency | Passed. |
| Compose configuration | Passed with Podman 6.0.2 and project-local `podman-compose`. |
| Odoo mutation | None. |
| Application adapter change | None. |
| Google Drive change | None. |

### Phase B final verification

| Check | Result |
| --- | --- |
| User approval and backup | Explicitly confirmed on 2026-09-18. |
| `purchase_requisition` state | `installed`. |
| Standard grouping fields | Verified through JSON-2 `fields_get`. |
| Line ACL | Read allowed; create, write, and unlink denied. |
| Bounded line values | `search_read` passed with exact variant, UoM, quantity, price, discount, taxes, currency, company, expected arrival, and selected seller. |
| Order-line traversal | Passed on permitted open RFQs. |
| Company boundary | Company 1 only; outside-company domain returned no rows. |
| Integration alternatives group | Denied after remediation. |
| Direct integration groups | Unchanged: API reader plus Role / User. |
| Unrelated group/agreement models | Read denied. |
| Focused live Odoo tests | 16 passed. |
| Full served integration selection | 19 passed, 80 deselected. |
| Ruff format and lint | Passed. |
| Python compilation | Passed for all five source packages. |
| Fast tests | 80 passed, 19 integration/E2E tests deselected. |
| Dependency consistency | Passed. |
| Compose configuration | Passed with the project-local provider. |
| Boundary and ignore checks | Decision Core framework-import scan, `.env` ignore check, and diff check passed. |
| Controlled fixture | Not created; approved semantic stop gate reached. |
| Application adapter and T6 | Not started. |
| Google Drive | Unchanged. |

## 11. Primary sources

- Odoo 19 Call for tender documentation:
  <https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals/calls_for_tenders.html>
- Odoo 19 `purchase_requisition` manifest and models:
  <https://github.com/odoo/odoo/tree/19.0/addons/purchase_requisition>
- Odoo 19 purchase-line implementation:
  <https://github.com/odoo/odoo/blob/19.0/addons/purchase/models/purchase_order_line.py>
- Odoo 19 seller selection implementation:
  <https://github.com/odoo/odoo/blob/19.0/addons/product/models/product_product.py>
- Odoo 19 purchase ACLs and global multi-company rules:
  <https://github.com/odoo/odoo/tree/19.0/addons/purchase/security>
