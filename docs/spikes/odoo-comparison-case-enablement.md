# T5 Odoo comparison-case enablement — Phase A evidence

## 1. Status and boundary

Assessment date: 2026-09-17.

**PHASE A COMPLETE — READ-ONLY — EXPLICIT APPROVAL REQUIRED BEFORE PHASE B**

This document records discovery and an exact proposed mutation set. Phase A did not
install or enable a module, change an ACL or record rule, assign a role, create or
modify Odoo business data, change the application adapter, or access PostgreSQL.

T5 is not complete and no final `GO` decision is claimed. The current adapter gate
remains `NO-GO`: the standard grouping capability is not installed, order-line rows
remain unreadable, supplier-offer lead time is unresolved, and the only discovered
`min_qty` field does not have hard-MOQ business meaning.

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

## 3. Standard capability expected after installation

The matching Odoo 19 standard module source defines the following expected contract.
These are source-backed expectations, not runtime-accepted mappings; Phase B must
revalidate them through the database `/doc` page and JSON-2 after installation.

| Model | Field | Expected type and purpose |
| --- | --- | --- |
| `purchase.order.group` | `order_ids` | One2many to `purchase.order`; the technical persisted call-for-tender group. |
| `purchase.order` | `purchase_group_id` | Stored many2one to `purchase.order.group`; the candidate stable comparison-case identity. |
| `purchase.order` | `alternative_po_ids` | Related one2many over the group's open RFQs. |
| `purchase.order` | `requisition_id` | Optional many2one to `purchase.requisition`; an agreement link, not the alternative group itself. |
| `purchase.requisition` | `purchase_ids` | RFQs/orders generated from one blanket order or purchase template. |

Creating alternatives through the standard wizard creates or extends one
`purchase.order.group`. The stable candidate group key is therefore
`purchase.order.purchase_group_id[0]`, not names, timestamps, `origin`, product
coincidence, vendor coincidence, currency, quantity, or nearby record IDs.

The module also creates `purchase_requisition.group_purchase_alternatives`, labelled
**Manage Purchase Alternatives**. That group controls the Alternatives tab and its
Create Alternative and Compare Product Lines actions. It must be assigned only to
the human fixture operator, never to the integration identity.

## 4. Least-privilege access proposal

The only proposed integration-identity permission change is one read-only model ACL
for `purchase.order.line` on the existing `Procurement RFQ API Reader` group:

| Model | Read | Create | Write | Unlink |
| --- | --- | --- | --- | --- |
| `purchase.order.line` | allowed | denied | denied | denied |

Odoo's installed `purchase` module already has a global
`purchase_order_line_comp_rule` with domain
`[('company_id', 'in', company_ids)]`. Because the identity has only company ID 1,
this existing global rule is the narrow company boundary. Phase A proposes no
duplicate record rule and no Purchase/User, Purchase/Administrator, Inventory/User,
Settings, or administrator role.

The proposed adapter-facing grouping read uses `purchase_group_id` on already
permitted `purchase.order` records. No `purchase.order.group` ACL is proposed. If
that field cannot be read through JSON-2 without direct group-model access, Phase B
must stop and request a separately reviewed permission expansion rather than grant
it silently.

The custom group was created in the database and its external identifier is not
readable by the integration identity. The ACL should therefore be added through the
supported Technical / Security / Access Rights UI to that exact existing group.

## 5. Controlled fixture proposal

After approval, an authorized human Purchase operator would create only these clearly
labelled company-1 PoC records through supported Odoo UI operations:

- suppliers `T5 Supplier A`, `T5 Supplier B`, and `T5 Supplier C`, each a distinct
  commercial company;
- one purchasable product template and one exact variant with internal reference
  `T5-COMP-001`, using `Units`;
- one exact-variant supplier-information row per supplier, in USD and company 1,
  with a positive quantity threshold and configured lead time;
- one draft RFQ with exactly one product line, quantity `100`, `Units`, USD, zero
  discount, no taxes, and an entered quotation unit price;
- two alternatives created from the first RFQ with **Copy Products** enabled, then
  adjusted only for their distinct suppliers, actual quoted unit prices, and any
  explicitly evidenced expected-arrival values.

All three RFQs must remain in an open state and share the same non-empty
`purchase_group_id`. The fixture must not be created with the integration identity,
must not send real email, and must not reuse unrelated demo RFQs.

The supplier-information values are test inputs, not automatically accepted
canonical MOQ or supplier-offer lead time. Phase B must test their exact selection
and meaning independently.

## 6. Phase A mapping matrix

| Canonical concept | Candidate source | Runtime shape / meaning | Dedicated-user access | Transformation | Status | Caveat |
| --- | --- | --- | --- | --- | --- | --- |
| Procurement case ID | `purchase.order.purchase_group_id` | Expected many2one to persisted `purchase.order.group` | Field not installed | `odoo:purchase.order.group:<id>` candidate | `UNRESOLVED` | Exact field and access require installation and live validation. |
| Requirement ID | Same alternative group, or an explicit agreement if used | No installed shared business-requirement record | Not available | None | `UNRESOLVED` | A technical comparison group may identify a case but does not by itself prove one authoritative business requirement. |
| Requested quantity | `purchase.order.line.product_qty` | Stored float | Read denied | Exact decimal text only after invariant checks | `UNRESOLVED` | All alternatives must independently match; no line is authoritative by default. |
| Offer ID | `purchase.order.id` | Stable integer source record | Read allowed | `str(id)` | `ACCEPTED` | Conditional on membership in a valid group. |
| Supplier ID | `partner_id -> commercial_partner_id` | Stable commercial partner ID | Read allowed | `str(commercial_partner_id[0])` | `ACCEPTED` | Revalidate child-contact behavior in the fixture. |
| Product ID | `purchase.order.line.product_id` | Exact product variant | Read denied | `str(id)` | `UNRESOLVED` | Product templates must not substitute for variants. |
| Unit of measure | `purchase.order.line.product_uom_id` | Quotation-line UoM | Read denied | Stable ID equality; no conversion | `UNRESOLVED` | Every alternative must use the exact same UoM. |
| Unit price | `purchase.order.line.price_unit` | Stored actual quotation-line unit price | Read denied | Decimal text without using `amount_total` | `UNRESOLVED` | Discount and taxes require an explicit guard. |
| Currency | `purchase.order.currency_id` and line-related currency | Stable currency ID | Order read allowed | Stable ID equality | `ACCEPTED` | No conversion is authorized. |
| Discount / tax | line `discount`, `tax_ids`, `price_unit_discounted` | Runtime-verified fields; `price_unit_discounted` is computed | Line read denied | Proposed fixture guard: discount must be zero and `tax_ids` empty | `UNRESOLVED` | A later adapter must reject, not silently normalize, unsupported values. |
| Lead time | line `date_planned`; supplier info `delay` | Expected arrival; configured planning delay | Metadata only / supplier info readable | None accepted | `UNRESOLVED` | No validated supplier-offer promise date or semantically valid duration start exists. |
| MOQ | `product.supplierinfo.min_qty` | Quantity needed to benefit from a vendor-price tier | Read allowed | None | `REJECTED` | Runtime help does not define a hard minimum accepted order; it cannot drive the Decision Core's hard MOQ constraint. |
| RFQ state | `purchase.order.state` | Explicit lifecycle selection | Read allowed | Existing open-state mapping | `ACCEPTED` | Fixture must exclude `purchase` and `cancel`. |
| Company | order and line `company_id` | Stable company ID and global rule boundary | Order read allowed | Stable ID equality | `ACCEPTED` | Line enforcement remains to be tested after the ACL change. |
| Source traceability | model, record ID, observation time | Source identity plus client observation timestamp | Partially available | Preserve without business defaulting | `UNRESOLVED` | A complete grouped line read is still unavailable. |

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
date. Phase A therefore has no deterministic, semantically valid transformation to
the current canonical `lead_time_days`. A manually edited expected-arrival value in
a controlled fixture would still need an explicit business rule and provenance that
the schema does not encode.

### MOQ

Runtime `fields_get` states that `product.supplierinfo.min_qty` is the quantity needed
to benefit from the supplier row's unit price. Odoo filters seller rows by partner,
date range, product variant/template applicability, quantity converted to the
supplier UoM, and company; the selected row is then ordered by discounted price,
sequence, and record ID. The quotation line exposes computed
`selected_seller_id`, which can identify the price row chosen by Odoo once line access
exists.

That selection is deterministic pricing-tier behavior, but it does not establish a
hard supplier order minimum. The Decision Core interprets MOQ as an eligibility
constraint and requires it to be positive. Reusing the pricing threshold would
change business meaning, while zero-tier values cannot be repaired to a positive
value. The current MOQ candidate is therefore `REJECTED`, not defaulted.

This is an independently sufficient `NO-GO` condition for the current adapter scope
unless a different authoritative hard-MOQ source is produced and validated.

## 8. Proposed Phase B operations

The following mutations require one explicit approval and would be performed in this
order:

1. Back up the local PoC database using the supported Odoo/database administration
   procedure; do not remove Compose volumes.
2. As an administrator, enable Purchase Agreements, which installs the locally
   available standard `purchase_requisition` module.
3. Enable Purchase Alternatives for an authorized human Purchase operator; do not
   assign that group to `Procurement Integration`.
4. Add exactly one read-only `purchase.order.line` ACL to the existing
   `Procurement RFQ API Reader` group. Do not add a new rule unless a measured gap is
   reviewed separately.
5. Revalidate module state, `/doc`, exact fields, effective model rights, company
   isolation, and unrelated-model access before creating data.
6. Create the controlled records in section 5 through the Odoo UI.
7. Run bounded JSON-2 contract tests with the integration identity. Perform no
   application Odoo write and implement no adapter.

Phase B must stop if the standard module is unavailable at install time, the fields
differ, the grouping field cannot be read without broader access, line access leaks
another company, any mutation right becomes allowed, or a critical semantic mapping
remains unresolved.

## 9. Security, data impact, and rollback

Security impact is limited to exposing company-permitted purchase-order-line values
to the existing integration identity. Create, write, unlink, Settings, Purchase,
Inventory, and administrator privileges remain denied. Module installation adds
standard Purchase Agreements models and UI for authorized human users but must not
change the integration identity's direct groups.

Data impact consists of the installed module's schema/data records, one ACL, one
human feature-group assignment, and the explicitly prefixed PoC fixture.

Rollback, in reverse order:

1. cancel and remove only the three `T5` draft RFQs through supported Odoo UI;
2. remove the three dedicated supplier-information rows, product, and suppliers once
   no references remain;
3. delete the read-only line ACL and remove the human Purchase Alternatives group;
4. only after a database backup and removal of dependent fixture data, uninstall
   Purchase Agreements through Apps if full schema rollback is required;
5. rerun T4 contracts and verify line read is denied and grouping fields are absent.

Module uninstall is a destructive database operation and is not an ordinary restart
or first-line rollback. Never delete the named volumes for this validation.

## 10. Phase A verification

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
