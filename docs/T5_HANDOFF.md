# T5 handoff — Odoo comparison-case enablement

## Status

**T5 COMPLETE — NO-GO — PRODUCTION ADAPTER REMAINS DEFERRED**

T5 removed the two T4 infrastructure blockers with approved, bounded changes: the
standard comparison-group fields are installed and the dedicated integration
identity can read company-permitted purchase-order lines. The result is still
`NO-GO` because Odoo's available supplier quantity is a price-tier threshold rather
than a hard MOQ, and the available planning dates do not establish authoritative
supplier-offer lead time.

No production adapter or T6 work was started.

## Branch and base

- Branch: `codex/t5-odoo-comparison-case-enablement`.
- Base: T4 merge `e8eccf71f786e7a987fdbc47b0c3c88e8f40b5ef`.
- Phase A checkpoint commit: `a3d07207151a837aec4c13c68dc52d2dfc8fc6a2`.
- Final T5 implementation commit: recorded in the external task handoff after the
  commit is created.

## Approval and backup

On 2026-09-18, the user explicitly approved the Phase B changes described in this
file and confirmed that the Odoo database backup had been completed. The user also
left the Odoo 19 Community UI open in Brave with an administrator session.

## Exact Odoo changes

The following supported UI changes were performed:

1. enabled **Purchase Agreements**, installing the local standard LGPL-3
   `purchase_requisition` module;
2. created one access-control entry named `Purchase Order Line Read only access`
   for model `purchase.order.line` and group `Procurement RFQ API Reader`, with
   Read enabled and Create, Write, and Delete disabled;
3. restricted `purchase_requisition.group_purchase_alternatives` to the human
   operator `Mitchell Admin`.

An intermediate validation caught that the global **Purchase Alternatives** setting
implicitly grants the feature group to every internal user. That setting was
immediately disabled and the group was assigned directly to `Mitchell Admin`.
Follow-up `has_group` validation proved that `Procurement Integration` does not have
the feature group. This correction is part of the final state, not an unresolved
exception.

No record rule, broad Purchase/Inventory/Settings role, direct PostgreSQL change,
application Odoo write, or Google Drive change was made.

## Standard grouping mechanism

Runtime `fields_get` now verifies:

| Model | Field | Runtime contract |
| --- | --- | --- |
| `purchase.order` | `purchase_group_id` | Stored many2one to `purchase.order.group` |
| `purchase.order` | `alternative_po_ids` | Related one2many to `purchase.order` |
| `purchase.order` | `requisition_id` | Stored many2one to `purchase.requisition` |
| `purchase.order.group` | `order_ids` | Stored one2many to `purchase.order` |

`source_po_id` is not present. The candidate stable comparison identity is
`purchase.order.purchase_group_id[0]`. The dedicated integration identity can read
that many2one value on permitted purchase orders without direct read access to the
`purchase.order.group` model.

## Dedicated integration identity

The final live contract verifies user ID 7 remains non-admin, limited to company ID
1, and has only the direct groups `Procurement RFQ API Reader` and `Role / User`.

| Model | Read | Create | Write | Unlink |
| --- | --- | --- | --- | --- |
| `purchase.order` | allowed | denied | denied | denied |
| `purchase.order.line` | allowed | denied | denied | denied |
| `purchase.order.group` | denied | denied | denied | denied |
| `purchase.requisition` | denied | denied | denied | denied |

A bounded `purchase.order.line/search_read` succeeds with actual line fields,
including exact product variant, UoM, quantity, quotation unit price, discount,
taxes, currency, company, expected arrival, and selected supplier-price row.
Traversing `purchase.order.order_line` also succeeds. All observed rows are in the
identity's only allowed company, and an explicit outside-company domain returns no
rows. Existing global rule `purchase.purchase_order_line_comp_rule` remains the
company boundary; no duplicate rule was added.

## Controlled comparison fixture

No T5 suppliers, product, supplier-information rows, or alternative RFQs were
created. Phase B stopped at the approved pre-fixture validation gate because a
critical semantic mapping remains invalid. Creating a synthetic three-offer case
would demonstrate UI mechanics but could not satisfy the canonical MOQ and lead-time
requirements, and the approved plan explicitly required stopping in that condition.

The existing unrelated demo RFQs were read only and were not treated as one
comparison case.

## Mapping decision

The installed standard module changes grouping and line access from the T4 result:

- explicit persisted grouping field: `ACCEPTED` as a technical source identity;
- order-line access and exact quotation-line price: `ACCEPTED` at the access/schema
  level;
- integration mutation rights: remain denied;
- hard MOQ from `product.supplierinfo.min_qty`: `REJECTED` because it is the
  quantity required to benefit from a price tier, not a supplier order-minimum
  constraint;
- supplier-offer lead time: `UNRESOLVED` because `product.supplierinfo.delay` is
  configured planning time and `purchase.order.line.date_planned` is Expected
  Arrival, not a recorded supplier promise with an authoritative duration start;
- shared requirement identity and complete controlled-case invariants: `UNRESOLVED`
  because the stop gate correctly prevented fixture creation.

MOQ alone is an independently sufficient blocker for the current Decision Core
contract. No value was defaulted, repaired, relabelled, or taken from supplier master
price as an observed quotation.

## Verification

Final Phase B verification on 2026-09-18:

- focused live Odoo contracts: 16 passed;
- full served integration selection: 19 passed, 80 deselected;
- fast test suite: 80 passed, 19 integration/E2E tests deselected;
- Ruff format and lint: passed;
- Python compilation for all five source packages: passed;
- dependency consistency: passed;
- Podman Compose configuration: passed with the project-local provider;
- Decision Core framework-import boundary scan: passed;
- `.env` ignore check and final diff check: passed;
- module state: `purchase_requisition` installed;
- line ACL: read allowed, create/write/unlink denied;
- integration alternatives group: denied;
- unrelated group/agreement models: read denied;
- company-scoped line query: passed;
- GitHub Actions: recorded in the external task handoff after the branch is pushed.

The known local `.pytest_cache` permission warning and dependency deprecation
warnings were emitted; they did not fail the suites.

## Security and rollback

Final data impact is limited to the installed standard module, one read-only ACL,
and one direct human feature-group assignment. There is no T5 business-data fixture
to remove.

Rollback, in reverse order:

1. remove `Mitchell Admin` from **Manage Purchase Alternatives**;
2. delete `Purchase Order Line Read only access` through Technical / Security /
   Access Rights;
3. only after a fresh database backup, uninstall Purchase Agreements through Apps
   if full schema rollback is required;
4. rerun the T4 contracts and verify line reads are denied and grouping fields are
   absent.

Module uninstall and ACL deletion are destructive actions and require explicit
action-time confirmation. Do not remove the Compose named volumes for rollback.

## Final decision

**NO-GO**

The local Odoo 19 Community PoC now has a supported explicit grouping mechanism and
least-privilege line reads, but it still cannot provide a deterministic positive hard
MOQ or an authoritative supplier-offer lead time compatible with the current
canonical model. The production Odoo-to-canonical adapter remains deferred.

See `docs/spikes/odoo-comparison-case-enablement.md` for the detailed evidence and
mapping matrix.
