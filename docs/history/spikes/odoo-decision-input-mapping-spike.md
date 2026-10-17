# T4 Odoo decision-input mapping spike

## 1. Outcome

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

Assessment date: 2026-09-17.

The renewed API key restored the dedicated integration identity, allowing T4 to
complete bounded, read-only schema, access, and value discovery. The local database
does not currently provide a validated explicit relationship that groups several
RFQs as alternatives for one requirement. In addition, the dedicated identity has
no read access to `purchase.order.line`. These independent blockers prevent a
semantically valid `PurchaseRequirement` plus `SupplierOffer` collection.

No production adapter, synthetic mapping fixture, permission change, module install,
or Odoo business-data write was implemented.

## 2. Environment and installed modules

- Branch base: T3 merge commit
  `f123446dac7994d9ea4727225c5fe4a9d0a39cd5`.
- Local runtime: Podman client/server 6.0.2, WSL-based
  `podman-machine-default`, Odoo image `odoo:19.0-20260908`, PostgreSQL
  `16.15-bookworm`, and database `procurement_poc`.
- The database-specific `/doc?db=procurement_poc` route was present and required an
  interactive authenticated web session. JSON-2 bearer authentication does not
  establish that browser session.
- JSON-2 `ir.module.module/search_read` verified `purchase` version `19.0.1.2` and
  `stock` version `19.0.1.1` as installed.
- `purchase_requisition` was included in the same narrow installed-module query and
  was not returned. T4 did not install it or infer what installing it would expose.

## 3. Identity and permission boundary

`res.users/context_get` authenticated as user ID 7. A bounded self-read verified the
internal `Procurement Integration` user, company ID 1 only, and timezone
`Europe/Budapest`. `has_group` confirmed that the user is not a Settings
administrator.

Effective access was measured through `check_access_rights` without attempting any
write operation:

| Model | Read | Create | Write | Unlink | Result |
| --- | --- | --- | --- | --- | --- |
| `purchase.order` | allowed | denied | denied | denied | Suitable for the existing RFQ summary only. |
| `purchase.order.line` | **denied** | denied | denied | denied | Critical blocker; `search_read` returned HTTP 403. |
| `product.product` | allowed | denied | denied | denied | Read-only. |
| `product.template` | allowed | denied | denied | denied | Read-only. |
| `product.supplierinfo` | allowed | denied | denied | denied | Read-only. |
| `res.partner` | allowed | denied | denied | denied | Read-only. |
| `res.currency` | allowed | denied | denied | denied | Read-only. |
| `uom.uom` | allowed | denied | denied | denied | Read-only. |
| `ir.module.module` | allowed | denied | denied | denied | Used only for the bounded module check. |

Reading `purchase.order.order_line` also returned HTTP 403 because Odoo attempted
to traverse the denied `purchase.order.line` relation. The server reported that
line reads are available only to broader standard groups such as Purchase/User,
Inventory/User, and other unrelated roles. T4 did not assign any of them. The
smallest permission change requiring separate approval is a read-only
`purchase.order.line` ACL for the existing `Procurement RFQ API Reader` group,
subject to an equally narrow company record rule.

## 4. Models and exact fields inspected

Every field below was requested explicitly through `fields_get`. Missing candidate
names were omitted by Odoo and are listed separately.

| Model | Runtime-verified fields and types |
| --- | --- |
| `purchase.order` | `id` integer; `name` char; `partner_id` many2one to `res.partner`; `partner_ref` char; `date_order` datetime labelled **Order Deadline**; `date_planned` datetime labelled **Expected Arrival**; `state` selection; `currency_id` many2one to `res.currency`; `company_id` many2one to `res.company`; `order_line` one2many to `purchase.order.line`; `origin` char. |
| `purchase.order.line` | `id` integer; `order_id` many2one to `purchase.order`; `partner_id` many2one to `res.partner`; `product_id` many2one to `product.product`; `product_uom_id` many2one to `uom.uom`; `product_qty` float; `price_unit` float; `discount` float; `currency_id` many2one to `res.currency`; `company_id` many2one to `res.company`; `date_planned` datetime; `price_subtotal` and `price_total` monetary. Schema metadata was visible, but records were not. |
| `product.product` | `id` integer; `name` char; `default_code` char; `product_tmpl_id` many2one to `product.template`; `uom_id` many2one to `uom.uom`; `seller_ids` one2many to `product.supplierinfo`. |
| `product.template` | `id` integer; `name` char; `uom_id` many2one to `uom.uom`; `seller_ids` one2many to `product.supplierinfo`. |
| `product.supplierinfo` | `id` integer; `partner_id` many2one to `res.partner`; optional `product_id` many2one to `product.product`; required `product_tmpl_id` many2one to `product.template`; required `product_uom_id` many2one to `uom.uom`; required `min_qty` float labelled **Quantity**; `price` float labelled **Unit Price**; required `currency_id`; required integer `delay` labelled **Lead Time**; optional `date_start`, `date_end`, and `company_id`. |
| `res.partner` | `id` integer; `name` char; `commercial_partner_id` many2one to `res.partner`; `parent_id` many2one to `res.partner`; `is_company` boolean; `company_id` many2one to `res.company`; `company_type` selection; `supplier_rank` integer; `active` boolean. |
| `res.currency` | `id` integer; `name` and `symbol` char; `decimal_places` integer; `active` boolean. |
| `uom.uom` | `id` integer; `name` char; `rounding` and `factor` float. |

The candidate `purchase.order` fields `alternative_po_ids`, `source_po_id`, and
`requisition_id` were not returned. Candidate line fields `product_uom` and
`taxes_id` were also not returned; `product_uom_id` is the verified UoM field, while
tax semantics remain unresolved rather than being inferred from another name.

## 5. Observed bounded values

- Eleven non-cancelled purchase documents were returned with deterministic
  `id asc` ordering and a limit of 20: seven open RFQs (`draft` or `sent`) and four
  confirmed `purchase` records.
- Every observed document belonged to company ID 1 and currency ID 1 (`USD`).
- Every observed `origin` and `partner_ref` value was false. Similar timestamps and
  common currency are not grouping evidence.
- Five referenced vendors were readable. Each observed RFQ vendor was a company,
  had no parent, and its `commercial_partner_id` equalled its own stable record ID.
- The bounded supplier-information query returned 26 rows for those vendors.
  Observed `delay` values ranged from 0 to 10 days, `min_qty` included 0, 1, 3, 5,
  and 12, currency was USD, UoM was `Units`, and company was ID 1.
- Some supplier-information rows applied at product-template level because
  `product_id` was false. Several templates have multiple variants, so template and
  variant identity cannot be treated as interchangeable.
- Multiple supplier-information rows can apply to the same vendor/template. For
  example, Ready Mat had two Large Cabinet rows with minimum quantities 1 and 3 and
  different prices. No T4 selection rule was inferred.
- All supplier-information rows were vendor master data, not observed quotation-line
  values.

## 6. Mapping evidence matrix

| Canonical field | Candidate Odoo model | Exact field | Observed type/shape | Business meaning | Dedicated-user read access | Transformation | Status | Caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Procurement-case identifier | `purchase.order` | `alternative_po_ids`, `source_po_id`, or `requisition_id` candidates | None returned | Stable identity shared by alternatives | Order read allowed | None | NOT AVAILABLE | The standard relationship candidates are absent and `purchase_requisition` is not installed. |
| Requirement identifier | Unknown | none validated | Not observed | Identity of one shared need | Not applicable | None | NOT AVAILABLE | An individual RFQ ID is not a shared requirement ID. |
| Requested quantity | `purchase.order.line` | `product_qty` | Float metadata only | Shared requested quantity context | **Read denied** | None | UNRESOLVED | No line value could be compared; one supplier's quantity cannot be chosen arbitrarily. |
| Offer identifier | `purchase.order` | `id` | Integer | Stable source RFQ identity | Read allowed | `str(id)` | ACCEPTED | Conditional on later proof that the document belongs to a valid comparison case. |
| Supplier identifier | `res.partner` | `commercial_partner_id` reached from order `partner_id` | many2one `[id, display_name]` | Stable commercial entity | Read allowed | `str(commercial_partner_id[0])` | ACCEPTED | Observed vendors were companies with self-commercial identity; revalidate child-contact cases. |
| Product identifier | `purchase.order.line` | `product_id` | many2one metadata only | Exact product variant quoted | **Read denied** | None | UNRESOLVED | Supplier information often targets templates; variants must not be collapsed. |
| Unit of measure | `purchase.order.line` | `product_uom_id` | many2one metadata only | Unit for quantity and unit price | **Read denied** | None | UNRESOLVED | Supplier master data used Units, but quotation-line equality was not observable. |
| Unit price | `purchase.order.line` | `price_unit` plus `discount` and tax semantics | Float metadata only | Actual quoted unit price | **Read denied** | None | UNRESOLVED | Supplier-information `price` is vendor master data and is rejected as a quotation price. |
| Currency | `purchase.order` | `currency_id` | many2one `[1, "USD"]` | Order currency | Read allowed | Compare stable currency IDs | ACCEPTED | All observed documents were USD, but no valid grouped case or line-price mapping exists. |
| Lead time | `product.supplierinfo` / `purchase.order` | `delay` / `date_planned` | Required integer / datetime | Configured vendor lead time / calculated expected arrival | Read allowed | None | UNRESOLVED | The quoted product line cannot be matched; configured delay and expected arrival are not supplier promise dates. |
| Minimum order quantity | `product.supplierinfo` | `min_qty` | Required float | Vendor-pricelist quantity threshold | Read allowed | None | UNRESOLVED | Matching and deterministic tier selection require product, quantity, date, company, currency, and UoM. Zero values conflict with the current positive-MOQ domain invariant. |
| RFQ state | `purchase.order` | `state` | Selection | Document lifecycle | Read allowed | Existing neutral open-state mapping | ACCEPTED | For a future comparison case, cancelled and confirmed/historical records must not be mixed with open offers. |
| Alternative-RFQ grouping | `purchase.order` | probed explicit relationship candidates | None returned | Reproducible alternative relationship | Order read allowed | None | NOT AVAILABLE | Names, origin, dates, product coincidence, and supplier inference are rejected. |

## 7. Critical-invariant decisions

### Procurement-case grouping

No supported grouping relationship was available among the explicitly probed
fields. The installed-module check also found no `purchase_requisition` module.
All observed `origin` values were empty. T4 therefore has no explicit, stable,
reproducible way to identify alternative RFQs for one requirement. This is a
standalone adapter blocker.

### Product, UoM, quantity, and multi-line handling

The line schema exposes the expected concepts, but the dedicated user cannot read
line records. T4 cannot establish line cardinality, exact product variant, UoM, or
quantity equality for any RFQ. No unit conversion or multi-line aggregation was
introduced.

### Supplier identity

For the observed companies, `commercial_partner_id[0]` is accepted as the stable
supplier identity and the display name is metadata only. Child-contact behavior was
not present in the observed RFQ set and remains a caveat.

### Price and currency

`price_unit` is the candidate quotation-line field, but values are inaccessible.
`discount` exists; the exact tax field and before/after-tax semantics were not
validated. Supplier-information `price` is rejected because it is master data, not
the quotation. All observed purchase documents and supplier-information rows used
USD, but same-currency data does not create a valid comparison case.

### Lead time

`product.supplierinfo.delay` is explicitly a configured integer **Lead Time**.
`purchase.order.date_planned` is explicitly **Expected Arrival**, while
`date_order` is **Order Deadline**. Their values demonstrate that these concepts
exist, not that either is a supplier-promised quotation lead time. Because the
quoted product line cannot be matched to one applicable supplier row and promise
semantics are absent, `lead_time_days` remains unresolved. No date subtraction,
timezone conversion, or rounding rule was implemented.

### Minimum order quantity

`product.supplierinfo.min_qty` is a required float and is the only viable MOQ
candidate found. It cannot yet support the hard constraint because the quotation
product and requested quantity are unreadable and multiple tier rows can match.
Observed zero values also cannot enter the existing `SupplierOffer`, which requires
a positive MOQ. T4 did not default or repair those values and did not change the
Decision Core.

### RFQ state

Odoo exposed `draft`, `sent`, `to approve`, `purchase`, and `cancel`. The existing
ledger includes only the first three. A future decision case should likewise be
restricted to one explicitly justified open-offer lifecycle and must exclude
cancelled, confirmed, and historical documents unless separate semantics are
approved.

## 8. Demo-data sufficiency

The current data set is **insufficient and not fully inspectable**:

- it has at least three open RFQs and all observed orders use one company and USD;
- it has supplier master data containing lead-time and minimum-quantity values;
- it has no validated alternative-RFQ grouping relationship;
- purchase-order lines cannot be read, so same product/variant, UoM, quantity,
  quoted price, and one-line cardinality cannot be established; and
- no authoritative shared requirement identifier or requested quantity is present.

The eleven purchase documents must not be grouped by their similar timestamps or
empty origins. No live or synthetic comparison case was fabricated.

A later approved human fixture requires one explicit grouping identity, at least
three open alternatives, exactly one comparable product-variant line per RFQ, the
same UoM and requested-quantity context, one currency, actual quotation-line prices,
distinct stable commercial suppliers, an explicitly classified lead-time source,
and unambiguous applicable supplier-information MOQ tiers.

## 9. Accepted, rejected, and unresolved mappings

Accepted in isolation:

- `purchase.order.id` as source offer identity;
- order `partner_id` followed by `commercial_partner_id[0]` as stable supplier
  identity for the observed company vendors;
- stable `currency_id` equality as the currency guard;
- the existing open-state selection mapping;
- exact schema meanings for `product.supplierinfo.delay` and `min_qty`, but not their
  canonical transformations.

Rejected:

- unrelated RFQs as one decision case;
- names, origin, close timestamps, or product coincidence as grouping keys;
- vendor display name as canonical supplier identity;
- `amount_total` or supplier-information `price` as quotation unit price;
- RFQ line quantity as MOQ;
- silent currency or UoM conversion;
- silent MOQ defaults;
- treating order deadline, expected arrival, configured vendor delay, promised
  delivery, and actual receipt as interchangeable; and
- artificial multi-line aggregation.

Unresolved or not available:

- all grouping, requirement, quantity, line, product/variant, quotation UoM,
  quotation-price, discount/tax, lead-time, MOQ-selection, and multi-line semantics;
- any complete live comparison case.

## 10. Security findings

- The API key remained in the ignored `.env` and was never printed or committed.
- The renewed key authenticates only as the existing non-admin integration user.
- All newly required models except `purchase.order.line` have read-only effective
  access; create, write, and unlink are denied everywhere tested.
- The line denial was recorded without assigning a broader standard role.
- No PostgreSQL query, module installation, ACL/record-rule change, Odoo source
  inspection, or business-data write occurred.
- The localhost-only SSH tunnel preserved the existing network boundary.

## 11. Implementation gate and next step

The adapter gate failed. Missing explicit grouping alone blocks a decision case;
line read denial independently blocks product, quantity, UoM, price, and line-count
validation. Implementing an adapter or mapping fixtures would be speculative.

The smallest next approved validation increment has two prerequisites:

1. add only read access for `purchase.order.line` to the existing
   `Procurement RFQ API Reader` group, with company-scoped record behavior, then
   rerun the bounded line probes; and
2. make a separate product/process decision about an Odoo-supported explicit
   requirement/alternative grouping mechanism, then validate its exact model and
   fields through `/doc` and JSON-2 before creating controlled data.

Do not assign Purchase/User or Inventory/User merely to obtain line access. Do not
install a module or create a custom grouping field without separate scope and
approval. Do not begin T5 automatically.

## 12. T6 mapping disposition

T5 subsequently validated the standard `purchase_group_id` mechanism and
company-scoped read access to `purchase.order.line`. T6 does not reverse the semantic
rejections in this spike. Instead, its narrow hybrid assembler uses the following
source split:

| Decision input | T6 source | Disposition |
| --- | --- | --- |
| Case identity | `purchase.order.purchase_group_id` | Validated Odoo fact |
| Offer, supplier, product, UoM, quantity, price, currency, company, state | Read-only order, line, and commercial-partner facts | Validated only inside the explicit supported subset |
| Hard MOQ | Explicit supplemental value with field/source/reference/time attribution | Accepted as source-attributed, not automatically verified |
| Supplier-promised lead time | Explicit supplemental value with field/source/reference/time attribution | Accepted as source-attributed, not automatically verified |
| `product.supplierinfo.min_qty` | Never mapped | Rejected price-tier threshold |
| `product.supplierinfo.delay` | Never mapped | Rejected planning lead time |
| `purchase.order.line.date_planned` | Never mapped | Rejected expected-arrival date |

See `docs/T6_DESIGN.md` for the complete invariant and provenance contract. This
addendum does not convert T6 into a production adapter or make supplemental claims
authoritative.
