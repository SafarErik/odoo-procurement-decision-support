# T5 handoff — Phase A approval checkpoint

## Status

**PHASE A COMPLETE — NO ODOO MUTATION — PHASE B AWAITS EXPLICIT APPROVAL**

This is an approval checkpoint, not the final T5 handoff. The final increment must
still end in an evidence-backed `GO` or `NO-GO` after the user either approves the
bounded Phase B proposal or accepts the current blockers as the terminal result.

The current adapter decision remains `NO-GO`. No production adapter or T6 work has
started.

## Branch and base

- Branch: `codex/t5-odoo-comparison-case-enablement`.
- Base and current starting commit: T4 merge
  `e8eccf71f786e7a987fdbc47b0c3c88e8f40b5ef`.
- T2, T3, and T4 expected commits are ancestors of the branch.
- The worktree was clean before Phase A changes.

## Phase A findings

The exact local Odoo 19 Community database contains the standard
`purchase_requisition` module as an uninstalled LGPL-3 module named **Purchase
Agreements**. The corresponding `module_purchase_requisition` setting exists. This
requires standard module installation but no Enterprise edition change, new license,
third-party module, or custom grouping field.

Matching Odoo 19 source defines a persisted `purchase.order.group` and
`purchase.order.purchase_group_id` for calls for tender, plus related
`alternative_po_ids`. This is the supported primary grouping candidate. It is not
yet runtime-validated because the approval gate prohibits installation in Phase A.

The integration identity still cannot read `purchase.order.line`. Its current direct
groups and company boundary are unchanged. The smallest proposed change is one
read-only line ACL on its existing custom group. Odoo's already-installed global
line rule restricts records to `company_ids`, so no duplicate record rule or broad
Purchase/Inventory role is proposed.

## Critical semantic findings

`product.supplierinfo.min_qty` is a vendor-price-tier threshold: the runtime says it
is the quantity needed to benefit from that unit price. It is not an authoritative
hard minimum order accepted by the supplier. Mapping it to the Decision Core MOQ
constraint is therefore rejected.

`product.supplierinfo.delay` is configured planning time from PO confirmation to
warehouse receipt. `purchase.order.line.date_planned` is Expected Arrival and
defaults from that configured delay. Neither field currently proves a supplier-offer
promise or supplies an unambiguous duration start for canonical `lead_time_days`.

These lead-time and MOQ gates remain critical. Phase B can validate the standard
grouping and line contract, but it must not force a `GO` by relabelling pricing-tier
or planning data.

## Approval requested

The exact requested authorization is limited to:

1. install the local standard `purchase_requisition` module through Purchase
   Agreements;
2. enable Purchase Alternatives for the authorized human fixture operator only;
3. add read-only `purchase.order.line` access to the existing
   `Procurement RFQ API Reader` group, relying on the existing global company rule;
4. create the explicitly prefixed three-supplier, one-product, three-alternative-RFQ
   fixture described in
   `docs/spikes/odoo-comparison-case-enablement.md`;
5. run read-only schema/access/value validation with the integration identity.

The authorization would not include an application adapter, Odoo API write by the
application, Decision Core change, broad role, direct database modification, custom
grouping module/field, external manifest, real email, production data, or T6.

## Changes made in Phase A

- Added a focused T5 evidence document and mapping/proposal matrix.
- Added this approval-checkpoint handoff.
- Added live read-only contracts for module availability and exact line/supplier
  metadata.
- Updated the implementation log.

No Odoo state, Google Drive document, application source, adapter, Decision Core,
frontend, Compose configuration, or CI workflow was changed.

## Verification at checkpoint

- Ruff formatting: passed; 50 Python files formatted.
- Ruff lint: passed.
- Python compilation: passed for all five source packages.
- Fast tests: 80 passed, 16 integration/E2E tests deselected.
- Live integration tests: 16 passed, including 13 Odoo contracts and the served
  FastAPI health/decision plus Odoo HTTP checks.
- Dependency consistency: passed.
- Compose configuration: passed with project-local `podman-compose`; Podman client
  and server are 6.0.2.
- Whitespace and architecture/security scans: recorded after the final diff review.
- GitHub Actions: not run; the branch has not been pushed by this checkpoint work.

Pytest reported existing FastAPI/Starlette deprecation notices and the known local
`.pytest_cache` write warning; no test failed.

See `docs/spikes/odoo-comparison-case-enablement.md` for exact evidence, security
impact, controlled records, rollback, and primary sources.
