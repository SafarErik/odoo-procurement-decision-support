# T4 Odoo decision-input mapping spike

## 1. Outcome

**SPIKE COMPLETE — CRITICAL MAPPING NOT AVAILABLE — ADAPTER DEFERRED**

Assessment date: 2026-09-17.

The current local environment cannot provide evidence-backed canonical
`PurchaseRequirement` and `SupplierOffer` input because the configured dedicated
integration credential receives HTTP 401 from every JSON-2 call. The failure also
affects the previously validated `res.users/context_get` and
`purchase.order/search_read` calls. T4 therefore did not implement an adapter,
mapping fixtures, an automatic evaluation flow, or any Odoo write.

This is an authentication-boundary result, not proof that the candidate models or
fields are absent. The credential may be expired, revoked, or mismatched; T4 did not
have evidence to select one cause.

## 2. Environment and evidence boundary

- Repository branch: `codex/t4-odoo-decision-input-spike`, created at the T3 merge
  commit `f123446dac7994d9ea4727225c5fe4a9d0a39cd5`.
- Local runtime: Podman client/server 6.0.2, WSL-based
  `podman-machine-default`, Odoo image `odoo:19.0-20260908`, and PostgreSQL
  `16.15-bookworm`.
- Database: local Community proof-of-concept database `procurement_poc`.
- Previously verified on 2026-09-16: Purchase and Inventory installed, seven demo
  RFQs, and the narrow T1 `purchase.order` contract described below.
- Verified during T4 on 2026-09-17: the Odoo web service returned HTTP 200 through
  a localhost-only SSH tunnel; `/doc?db=procurement_poc` was present but redirected
  to the interactive login; adding the JSON-2 bearer header still redirected because
  an API key does not establish a web session.
- Verified during T4 on 2026-09-17: the configured key was non-empty and remained
  outside the repository, but `res.users/context_get`,
  `purchase.order/search_read`, every attempted `fields_get`, every attempted
  `check_access_rights`, and the two existing live Odoo contract tests received
  HTTP 401.

The T1 evidence is retained as dated evidence. It is not presented as a successful
T4 revalidation, and no current access or business-data claim is inferred from it.

## 3. Identity and permission boundary

The intended identity is the existing internal `Procurement Integration` user.
T1 verified user ID 7, company ID 1 only, no Settings-administrator membership,
direct groups `Procurement RFQ API Reader` and `Role / User`, and this effective
`purchase.order` access:

| Model | Read | Create | Write | Unlink | Evidence date | T4 result |
| --- | --- | --- | --- | --- | --- | --- |
| `purchase.order` | allowed | denied | denied | denied | 2026-09-16 | Not revalidated; authentication returned HTTP 401. |
| `purchase.order.line` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `product.product` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `product.template` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `product.supplierinfo` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `res.partner` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `res.currency` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |
| `uom.uom` | unknown | unknown | unknown | unknown | none | Introspection returned HTTP 401. |

No write probe was performed. No ACL, record rule, group, company assignment, user,
API key, module, or business record was created or modified. The smallest possible
remediation is to issue a new key for the same dedicated user, without changing its
groups, and rerun the read-only probes. Any additional model permission must be
proposed from the resulting denial evidence and approved separately.

## 4. Models and exact candidate fields

T4 attempted narrowly scoped `fields_get` calls for the following models and exact
candidate fields. Each call returned HTTP 401 before field metadata was available.
The names in this list remain hypotheses, not a validated Odoo contract.

| Candidate model | Exact candidate fields requested | T4 result |
| --- | --- | --- |
| `purchase.order` | `id`, `name`, `partner_id`, `partner_ref`, `date_order`, `date_planned`, `state`, `currency_id`, `company_id`, `order_line`, `alternative_po_ids`, `source_po_id`, `origin` | HTTP 401; no new field validated. |
| `purchase.order.line` | `id`, `order_id`, `partner_id`, `product_id`, `product_uom`, `product_uom_id`, `product_qty`, `price_unit`, `discount`, `taxes_id`, `currency_id`, `company_id`, `date_planned`, `price_subtotal`, `price_total` | HTTP 401; no field validated. |
| `product.product` | `id`, `name`, `default_code`, `product_tmpl_id`, `uom_id`, `seller_ids` | HTTP 401; no field validated. |
| `product.template` | `id`, `name`, `uom_id`, `seller_ids` | HTTP 401; no field validated. |
| `product.supplierinfo` | `id`, `partner_id`, `product_id`, `product_tmpl_id`, `min_qty`, `price`, `currency_id`, `delay`, `date_start`, `date_end`, `company_id`, `product_uom_id` | HTTP 401; no field validated. |
| `res.partner` | `id`, `name`, `commercial_partner_id`, `parent_id`, `is_company`, `company_id`, `company_type`, `supplier_rank`, `active` | HTTP 401; no field validated. |
| `res.currency` | `id`, `name`, `symbol`, `decimal_places`, `active` | HTTP 401; no field validated. |
| `uom.uom` | `id`, `name`, `category_id`, `rounding`, `factor`, `factor_inv` | HTTP 401; no field validated. |

The only runtime-verified field contract remains the T1 `purchase.order` summary:
`id`, `name`, `partner_id`, `date_order`, `state`, `amount_total`, and
`currency_id`. Its observed JSON-2 response shapes were integer ID, non-empty text,
many2one `[id, display_name]`, Odoo datetime text, selection text, numeric amount,
and many2one `[id, display_name]`, respectively. Those fields support the RFQ
ledger only; they do not establish decision-input semantics.

## 5. Mapping evidence matrix

`ACCEPTED` below means only that the isolated transformation has dated runtime
evidence. It does not imply that a complete decision case can be constructed.

| Canonical field | Candidate Odoo model | Exact field | Observed type/shape | Business meaning | Dedicated-user read access | Transformation | Status | Caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Procurement-case identifier | `purchase.order` | hypothesized alternative relationship | Not observed | Stable identity shared by competing quotations | Not testable: HTTP 401 | None | UNRESOLVED | Similar names, origins, dates, products, or suppliers are not authoritative grouping keys. |
| Requirement identifier | Unknown | unknown | Not observed | Identity of one shared procurement need | Not testable: HTTP 401 | None | UNRESOLVED | An RFQ identifier identifies one document, not necessarily the shared requirement. |
| Requested quantity | `purchase.order.line` | hypothesized quantity field | Not observed | Quantity required once for all alternatives | Not testable: HTTP 401 | None | UNRESOLVED | Selecting one supplier line's quantity would be arbitrary if alternatives differ. |
| Offer identifier | `purchase.order` | `id` | T1 integer | Stable identity of one source RFQ record | T1 read allowed; T4 HTTP 401 | Decimal-free string form of the integer | ACCEPTED | Valid only as source-record identity after that RFQ is proven to be a comparable alternative. |
| Supplier identifier | `purchase.order` / `res.partner` | `partner_id` / hypothesized commercial-parent field | T1 many2one `[id, display_name]` for `partner_id`; parent shape not observed | Commercial supplier responsible for the RFQ | T1 order read only; partner access untested | None | UNRESOLVED | Display name is not canonical identity; parent/child and company semantics are unknown. |
| Product identifier | `purchase.order.line` | hypothesized product relationship | Not observed | Same product or variant across alternatives | Not testable: HTTP 401 | None | UNRESOLVED | Product-template and variant identity must not be conflated. |
| Unit of measure | `purchase.order.line` / `uom.uom` | hypothesized UoM relationship | Not observed | Unit in which quantity and unit price are expressed | Not testable: HTTP 401 | None | UNRESOLVED | Unit conversion is outside T4; exact equality would be required. |
| Unit price | `purchase.order.line` | hypothesized unit-price field | Not observed | Quoted price per verified line UoM, with discount/tax semantics defined | Not testable: HTTP 401 | None | UNRESOLVED | `purchase.order.amount_total` is explicitly rejected as unit price. |
| Currency | `purchase.order` / line | `currency_id` or hypothesized line relationship | T1 many2one `[id, display_name]` on order | Currency governing the quoted unit price | T1 order read only; T4 HTTP 401 | Compare stable IDs; retain code as metadata only after validation | UNRESOLVED | The Decision Core has no currency field; all offers must first be proven same-currency. |
| Lead time | `purchase.order.line` / `product.supplierinfo` | hypothesized planned date or vendor delay | Not observed | Quoted, configured, or calculated duration under one explicit definition | Not testable: HTTP 401 | None | UNRESOLVED | Reference date, target date, timezone, rounding, missing, and negative cases are undefined. |
| Minimum order quantity | `product.supplierinfo` | hypothesized minimum-quantity field | Not observed | Applicable supplier/product/company/date/currency/UoM minimum | Not testable: HTTP 401 | None | UNRESOLVED | RFQ line quantity is explicitly rejected as MOQ; no default is allowed. |
| RFQ state | `purchase.order` | `state` | T1 selection text; observed `draft`, `sent`, `to approve`, `purchase`, `cancel` | Lifecycle state of one purchase document | T1 read allowed; T4 HTTP 401 | Existing ledger maps open states only | UNRESOLVED | Comparable-offer eligibility by state was not established; cancelled records remain excluded. |
| Alternative-RFQ grouping | `purchase.order` | hypothesized explicit relation | Not observed | Reproducible relationship among competing RFQs | Not testable: HTTP 401 | None | UNRESOLVED | This is a critical blocker. |

## 6. Critical-invariant results

### Alternative grouping

No explicit, stable alternative-RFQ relationship was observed in T4 because schema
and value queries were rejected at authentication. No heuristic grouping was used.
This alone blocks the adapter gate.

### Product, UoM, and multi-line handling

Line access, product/variant identity, UoM identity, and line cardinality were not
available. T4 therefore cannot show that any two documents quote the same item and
quantity context. A later first adapter should reject multi-line documents unless
an explicitly selected comparable line is validated; it must not aggregate lines.

### Requirement and quantity

No authoritative shared requirement record or quantity was identified. An order
line quantity cannot be copied into `PurchaseRequirement.requested_quantity` until
its relationship to all alternatives is proven.

### Supplier identity

T1 observed the `partner_id` relationship shape but did not validate commercial
parent/child behavior or partner read access. The displayed name remains metadata,
not identity.

### Price and currency

T1 validated order total and order currency for the ledger. Order total is rejected
as unit price. T4 could not inspect line price, discount, tax, line UoM, or currency
semantics. Mixed-currency comparison and currency conversion remain unsupported.

### Lead time

No lead-time mapping was accepted. A future mapping must identify whether its value
is supplier-promised, vendor-configured, or Odoo-calculated and must define the
reference date, target or duration, timezone, rounding, missing-value behavior, and
negative-duration rejection. Purchase-order date, expected arrival, vendor delay,
and actual receipt date are not interchangeable.

### Minimum order quantity

No MOQ mapping was accepted. T4 could not read supplier-information schema or
values, establish product/variant and supplier applicability, or define selection
among multiple applicable rows. RFQ line quantity is rejected as MOQ, and missing
MOQ must not default to zero or one.

### State handling

Cancelled documents remain invalid. T1's open-state ledger filter does not prove
that draft, sent, awaiting-approval, or confirmed documents are semantically
comparable offers for decision evaluation.

## 7. Demo-data sufficiency

T4 could not inspect current business records, so the local data set is **not proven
sufficient**. The seven RFQs observed by T1 are unrelated ledger entries until an
explicit alternative relationship and the remaining invariants are demonstrated.
They are not a decision case merely because they are RFQs.

A later approved human setup, only after schema revalidation, should create through
the normal Odoo UI one explicit comparison case with:

1. one stable shared requirement identity and requested quantity;
2. at least three explicitly linked alternative RFQs;
3. one comparable line per RFQ for the same product variant, UoM, and quantity
   context;
4. three distinct stable commercial-supplier identities;
5. positive quoted line prices under verified discount and tax semantics;
6. one common currency;
7. one explicitly classified lead-time source per offer; and
8. applicable supplier-information MOQ values whose company, date, currency,
   product/variant, supplier, and UoM scope is unambiguous.

The setup must avoid cancelled documents and must record which state is intended for
comparison. No fixture was created during T4. Synthetic unit-test fixtures must wait
until the corresponding live schema and semantics are validated.

## 8. Accepted, rejected, and unresolved mappings

Accepted:

- `purchase.order.id` to a source RFQ identifier string, based on T1 evidence only
  and conditional on later proof that the document is an alternative offer.
- The existing seven-field RFQ summary contract remains accepted for the separate
  ledger use case; it is not a `SupplierOffer` mapping.

Rejected:

- unrelated RFQs as one decision case;
- names, free-text origin, close dates, or product coincidence as grouping keys;
- vendor display name as canonical supplier identity;
- `amount_total` as unit price;
- RFQ line quantity as MOQ;
- silent currency or UoM conversion;
- silent MOQ defaults;
- treating order date, planned arrival, configured vendor delay, promised delivery,
  and actual receipt as interchangeable;
- artificial multi-line aggregation.

Unresolved or not available:

- all grouping, requirement, quantity, line, product/variant, UoM, commercial
  supplier, unit-price, currency-consistency, lead-time, MOQ-selection, state, and
  multi-line semantics listed in the evidence matrix;
- read access and record-rule/company behavior for every newly required model;
- current dedicated-user identity and access, because authentication failed.

## 9. Security findings

- The key was loaded only through the existing ignored `.env`; its value was never
  printed, logged, committed, or copied into evidence.
- The HTTP 401 result was preserved without switching to an administrator identity.
- No PostgreSQL query, Odoo source inspection, module install, ACL change, record-rule
  change, business-data write, or write-capability probe occurred.
- The localhost exposure remained bound to `127.0.0.1`; the known Podman forwarding
  failure was handled with a temporary localhost-only SSH tunnel.
- The current key must be replaced or reissued before any live T4 mapping evidence
  can be gathered. The reason for rejection is not proven and should not be guessed.

## 10. Implementation gate decision

The gate failed. Critical schema, access, grouping, comparability, requirement,
supplier, price, currency, lead-time, and MOQ invariants are unresolved. Implementing
an Odoo-to-canonical adapter would therefore encode speculation and is prohibited.

The smallest next validation step is:

1. replace `ODOO_API_KEY` locally with a newly issued key for the unchanged
   `Procurement Integration` user;
2. prove `res.users/context_get` and the existing bounded T1 RFQ query again;
3. open the database-specific `/doc` page in an authenticated session;
4. rerun the exact bounded `fields_get`, `check_access_rights`, and `search_read`
   probes listed above; and
5. stop again unless an explicit grouping relationship plus all remaining critical
   invariants are proven.

T5 must not begin automatically.
