# Controlled V2 Odoo history fixture: owner approval plan

2026-10-14. **PLANNED; OWNER APPROVAL REQUIRED; NO DATABASE OR FIXTURE CREATED.**
This is a manual preparation plan, not an importer or application feature.
It preserves the official assignment, five CORE functions and read-only runtime.

## Decision and current evidence

Prepare **nine new one-line purchase orders in a neutralized test copy**, with
three eligible receipt obligations per existing V2 supplier. Use the existing
T7S projection, T8 KPI and T14 feature conversion; add no generic discovery or
reporting framework. First validate one pilot receipt, then complete the other
eight. Do not confirm or edit the original comparison RFQs or reuse T7 records.

Reviewed AGENTS.md, README, terminal runbook, agent baseline, completed
[feasibility assessment](ODOO_HISTORY_FEASIBILITY_ASSESSMENT.md), manual T6/T7/T7S
guides, current KPI/conversion source and canonical Drive 00/02/03/06/07. Latest
Drive addenda still require distinct synthetic origin, exact context, cutoff,
feature/label/model audit and offline training; no requirements or ADRs changed.
Their dated open-PR publication text is superseded by current GitHub state.

- Local and live published `main`: `86c389c0d07dd1893d5ace32bb035fbd05adf2b2`.
  Current branch: `feature/odoo-data-integration`, HEAD
  `bd44b3b483fa2002544a68f8f2b7c33733b50739`; its difference from main is three
  documentation files. Pre-existing uncommitted renewed-key updates in the
  assessment and implementation log were retained. No checkout/fetch/commit/push.
- The access prerequisite is resolved: the preceding renewed-key run returned
  projection HTTP 200/six events and **2 targeted live tests passed in 2.11 s**.
  Those passing tests were not repeated; credential renewal is not a current task.
- Read-only database inventory at `2026-10-14T21:33:08Z` returned HTTP 200 and only
  `procurement_poc`. **No separate Odoo test database is available on the checked
  server.** This does not inventory other hosts. No master-password/admin endpoint
  was invoked, and backup/restore permissions or backup quality are not verified.
- Fresh exact reads confirm group 2, draft RFQs 16/17/18 and lines 28/29/30.
  Existing T7 supplier 55/product 57 stays separate from V2 supplier IDs 51/52/53
  and product 54. Matching confirmed history was absent in the completed assessment.
- Product 54 is `T6 Comparison Product`, Goods (`type=consu`), purchasable,
  Units ID 1, **Track Inventory=false**. All three quotation lines use
  `qty_received_method=stock_moves`. The guarded policy requires stock-move-backed
  lines, not the tracking flag. Odoo 19 Goods receipt generation supports that
  path; retain the existing product configuration and make the pilot an explicit
  compatibility gate. Do not silently enable tracking or substitute product 57.
- The nine exact planned Source Document markers below returned no records in
  the bounded duplicate check. Recheck in the chosen copy before creation.

Read-only evidence is under `.artifacts/v2-history-fixture-plan/` (ignored).
`read-only-preflight.jsonl` SHA-256:
`0c1c467596c44c2fb90ee9af670b9a5acc97d7d2dd86bc24a49b5576ada1da19`.
`quotation-identities.jsonl` and `planned-marker-check.jsonl` retain exact reads.
No Odoo data, model, application code, schema, environment file, Drive or tracker
was changed; existing services were left as found.

## Explicit fixture manifest

| Manifest property | Planned value |
| --- | --- |
| Fixture reference | `v2-odoo-history-fixture-v1` |
| Evidence origin | `controlled_synthetic`; administrator-created test history |
| Actual transport attribution | Existing adapter's `odoo_projection`, retained unchanged |
| Source database | `procurement_poc` — preserved |
| Proposed target database | `procurement_v2_history_test_v1` — currently absent |
| Company | `odoo:res.company:1`, `My Company (San Francisco)` |
| Product | `odoo:product.product:54`, `T6 Comparison Product` |
| Unit / currency | `odoo:uom.uom:1`, Units / `odoo:res.currency:1`, USD |
| Quotation context | `odoo:purchase.order.group:2`; RFQs 16/17/18, lines 28/29/30 |
| A / B / C | `odoo:res.partner:51/52/53`, `T6 Supplier A/B/C`; commercial IDs equal direct IDs |
| Preparation date D | Actual local date of execution, Europe/Budapest; owner records it before entry |
| On-schedule Expected Arrival F | D + 1 day, 23:00 in the verified UI timezone |
| Late Expected Arrival P | D - 1 day, 00:00 in the verified UI timezone |
| History quantity / price | Every new order: 100 Units; A USD 10, B USD 12, C USD 9 |
| New PO/line/move/picking IDs | **Not assigned.** Capture actual IDs after manual preparation; never predict IDs |

Odoo IDs are database-local. A restored copy should preserve the business IDs, but
this must be read back before use. Database name plus fixture reference and exact
IDs are part of the manifest/provenance; matching numeric IDs alone is insufficient.
Fail closed on a mismatch rather than substituting names or another record.

| Source Document (exact) | Vendor ID | Expected Arrival | Receipt steps on D | Expected eligible / adherent contribution |
| --- | --- | --- | --- | --- |
| `V2-SYNTH-HIST-v1-A01` | 51 | F | Receive 100 once — **pilot** | 1 / 1 |
| `V2-SYNTH-HIST-v1-A02` | 51 | F | Receive 100 once | 1 / 1 |
| `V2-SYNTH-HIST-v1-A03` | 51 | F | Receive 100 once | 1 / 1 |
| `V2-SYNTH-HIST-v1-B01` | 52 | F | Receive 100 once | 1 / 1 |
| `V2-SYNTH-HIST-v1-B02` | 52 | F | Receive 100 once | 1 / 1 |
| `V2-SYNTH-HIST-v1-B03` | 52 | P | Receive 40; create backorder; receive remaining 60 | 1 / 0 |
| `V2-SYNTH-HIST-v1-C01` | 53 | F | Receive 100 once | 1 / 1 |
| `V2-SYNTH-HIST-v1-C02` | 53 | P | Receive 100 once | 1 / 0 |
| `V2-SYNTH-HIST-v1-C03` | 53 | P | Receive 100 once | 1 / 0 |

Expected final output, with all receipt events inside the bounded history window:

| Supplier | Eligible PO lines / inbound events | Adherent lines | Exact T8 KPI | Ordered T14 feature values |
| --- | --- | --- | --- | --- |
| A (51) | 3 / 3 | 3 | 100.00% | (100.0, 3.0) |
| B (52) | 3 / 4 | 2 | 66.67% | (66.67, 3.0) |
| C (53) | 3 / 3 | 1 | 33.33% | (33.33, 3.0) |

Nine obligations create **ten inbound receipt events** because B03 has two.
Completed support counts lines, not events or quantities. All final records are
usable with no expected exclusions/warnings. While B03 is only 40/100 received,
it contributes no completed obligation: B has n=2, a withheld KPI and incomplete/
insufficient-history warnings. The remaining 60 restores n=3 and 66.67%.

This is the smallest supported three-supplier input: fewer than three eligible
lines for any supplier withholds that supplier's feature. No extra return,
cancelled, overreceipt or missing-date orders are needed; existing T7 and neutral
calculator regression tests retain those edge cases. Adding them would exceed
this preparation scope. Three samples give low-support technical evidence, not
statistical confidence. KPI contrasts do not promise distinct tree classes/scores.

The history quantities/prices are explicit test terms, not future offers or demand.
The existing approved Q=200, capacity/MOQ/policy assumptions remain separate.
Do not label the origins as observed commercial performance, supplier-promise
compliance, real risk probability or real savings. The synthetic-origin marker
is visible directly in Source Document; the local manifest records origin as well.

## Stop gate and administrator-controlled preparation

**STOP HERE. The owner must explicitly approve this named test-copy plan before
any step below. The agent must not operate the Odoo UI or invoke administrator
mutation endpoints even after approval. These are human administrator actions.**

### 1. Backup, test-copy creation and permissions

Prerequisites: owner has the local Odoo database-manager master password and a
human administrator login; existing pinned Odoo/addons and company data are
available; backup location is private, outside Git, with space for ZIP/database/
filestore copies. Keep Odoo loopback-only. Stop interactive use during capture;
record capture time and backup hash. Passwords/ZIP contents never enter chat/Git.

1. Human opens `http://127.0.0.1:8069/web/database/manager`.
   For **procurement_poc**, choose **Backup**, enter the local master password,
   choose **zip** in **Backup Format**, retain **Include filestore**, then **Backup**.
   Save the downloaded archive privately. This is backup export, not fixture entry.
2. Record the actual ZIP path/time/hash; verify the ZIP opens and contains
   `dump.sql` and the expected attachment filestore content (if present in the
   source). A readable ZIP alone is not proof of successful restoration.
3. Choose **Restore Database**, upload that ZIP, set **Database Name** to
   `procurement_v2_history_test_v1`, choose the copy option, enable **Neutralize**,
   enter the master password and select **Continue**. Do not overwrite, delete,
   rename or duplicate `procurement_poc`. Restoring the backup as the copy also
   tests its restoration; no separate duplicate operation or new Podman stack.
4. Sign in manually at
   `http://127.0.0.1:8069/web/login?db=procurement_v2_history_test_v1`.
   Confirm the selected database, company 1, product/supplier IDs, draft group-2
   RFQs, installed T7S addon and absence of the nine markers. Verify neutralized
   email/automated integrations in the copy before business entry. Neutralization
   does not prove physical/network isolation from external systems.
5. Preserve the copied RFQ reader's rights and dedicated portal history user's
   company-1/method-only projection group. In **Settings > Users section > Manage
   Users**, verify the dedicated user remains **Portal** and company 1 only;
   in **Settings > Technical > Users & Companies > Groups**, verify
   `T7-S Inventory-History Projection Reader`. Do not add Purchase/Inventory
   roles to runtime users. The human admin's existing rights perform preparation.
6. Read-only clone probes use the explicit target database header/configuration;
   keep the source `.env`, running source backend and saved helper cases unchanged.
   Use existing restricted credentials first, then verify authentication and
   security in the copy. Cloned credential compatibility is unverified until this
   read. Renew a target key only if a new 401 proves it necessary; never substitute
   an administrator key. A wrong-database/header check must block the run.
7. Take a second ZIP+filestore backup of the verified **test copy** before the
   pilot. Retain its path/hash, selected DB and baseline identities. It is the
   rollback baseline. Owner confirms these prerequisites and a read-only clone
   postcondition before proceeding to receipt preparation.

A test copy was not created, neutralization/permissions were not changed, and
no backup/restore operation was run in this task. If database-manager access or
the copied addon/data is unavailable, stop; do not bypass through PostgreSQL.

### 2. Freeze D and create the single pilot

1. Confirm the human administrator's displayed timezone is Europe/Budapest and
   record D, F and P as literal dates/times before entry. Complete all receipts
   on D. If a midnight boundary or another timezone intervenes, stop and revise
   the unexecuted schedule rather than backdating completion or silently changing
   confirmed Expected Arrival. Save UTC readback in the execution manifest.
2. **Purchase > Orders > Purchase Orders**: remove default filters and search
   **Source Document** for each exact marker. None must exist initially. If some
   or duplicates exist, stop; do not repair/reuse them silently.
3. **Purchase > Orders > Requests for Quotation > New**: select **Vendor T6
   Supplier A**, **Company My Company (San Francisco)**, currency USD and **Source
   Document V2-SYNTH-HIST-v1-A01**. Add one **T6 Comparison Product** line,
   **Quantity 100**, **Unit Units**, **Unit Price 10**, **Discount 0**, no taxes,
   and line **Expected Arrival F**. Save, reopen and verify all values.
4. Do not use **Create Alternative**, confirm the original RFQs, or add the history
   order to group 2. Retain product 54's Goods/untracked setting. Use an ordinary
   supplier-to-internal receipt, not dropship/intercompany/multi-step replacement.
5. Select **Confirm Order > Receive**, verify exact PO/product/company/100-unit
   demand, set processed **Quantity 100**, then **Validate**. If Purchase confirmation
   prompts cancellation of alternatives, or **Receive** is absent, stop.
6. Owner reports completion and actual new PO/line/picking identifiers. Read-only
   pilot verification must prove the exact company/supplier/product/UoM chain,
   one done inbound move and completion at or before Expected Arrival. With
   only one line, the KPI is intentionally withheld (n=1); this is not a failure
   of the access gate. No invented PO IDs or administrator data-read fallback.
7. Only after the pilot passes may the human create the remaining eight orders.
   If untracked Goods does not yield the supported projection evidence, stop and
   preserve the failure. A product-setting change needs a separately approved
   amendment; it is not part of this nine-order plan.

### 3. Complete the remaining receipt scenarios

Repeat **New** for the eight remaining table rows with their exact marker, vendor,
price and F/P timestamp; keep the same company, product, 100 Units, zero discount,
no taxes and independent order. Save/reopen/verify before **Confirm Order**.

For every single receipt: **Receive > Quantity 100 > Validate**, verify **Done**.
For B03: **Receive > Quantity 40 > Validate > Create Backorder**; open its generated
backorder, verify **Back Order of** references the first receipt, then
**Quantity 60 > Validate**. Do not cancel the remaining quantity. Record both
actual move/picking IDs and their full-completion time. It must remain late.

Do not create vendor bills, returns/replacements, additional suppliers/products,
lot/serial tracking or model labels. Preserve RFQs 16/17/18 and old T7 lines 31–34.

### 4. Read-only postcondition checklist

After human completion, the agent may run these authorized restricted reads only:

1. Require the target DB explicitly. RFQ identity: `purchase.order/search_read`
   with exact nine `origin` values, `company_id=1`, limit **10**. Require exactly
   nine unique matching orders, one line each, direct/commercial supplier join
   51/52/53 and supported confirmed state. Use `read` on the returned exact line
   IDs; check product 54/unit 1, quantity 100, expected prices, zero discount/tax,
   stock-move receipt method and exact F/P UTC values. Freeze returned IDs.
2. Capture one common UTC window end E strictly after all completed receipts and
   no later than request time. Start S=E−365 days. Run **three** production
   `OdooHistoricalPerformanceReader.read_inventory_history` calls, one supplier
   at a time, each with only its three exact line IDs, company 1, [S,E), result
   limit **10**. Header `X-Odoo-Database` must be the approved test-copy name.
   The projection endpoint remains
   `/json/2/procurement.inventory.history.projection/read_bounded_history`.
3. Validate raw membership before aggregation: exact database manifest, company,
   commercial supplier, product, UoM, line/move/picking IDs and complete
   backorder links. Expected inbound event counts A/B/C=3/4/3, all done,
   supplier→internal, total completed 100 per line, and no return relationship.
   No truncation, unrequested records, unit conversion or unrelated T7 history.
4. Reuse `calculate_delivery_schedule_adherence` and assert the final table's
   exact Decimal percentages, n=3 and no warnings. Reuse
   `from_sourced_history` only after raw-context proof, with one common cutoff C
   after all acquisition `observed_at` timestamps. Require
   S=E−365 days and E≤observed_at≤C, C−E≤7 days. Retain source `odoo_projection`;
   save origin, database, fixture reference, exact evidence, exclusions and hashes
   in the offline capture manifest. No prior-as-of availability claim.
5. Check original group-2 RFQs remain draft and unchanged; original T7 fixture
   still belongs to 55/57. Verify source database has none of the nine markers.
   Existing targeted security/KPI contracts retain their accepted source result;
   recheck them only after relevant permission/adapter/environment changes.
   Clone-specific permissions require their own verification before pilot.

There is no current nine-order acceptance test/CLI; this is its precise future
check contract. Existing T7 tests select T7 markers and cannot be claimed as V2
fixture acceptance. No POST to the helper planning API, solver, training or model
load is needed to prove these receipt/KPI postconditions.

### 5. Restoration and cleanup

Do not delete done transfers or run `down -v`. On failed/abandoned preparation,
retain the failed test copy as evidence and have the human restore the **pre-pilot
test-copy ZIP** to a fresh unused name, e.g. `procurement_v2_history_test_v1_reset1`,
using copy+neutralization. Verify its original identity manifest, absence of new
markers and restricted reads before designating it the replacement target. Any
deletion of the failed test copy requires separate explicit owner authorization.
Never restore over/drop `procurement_poc` or a helper database. Retain backups,
evidence and the existing machine/volumes. A new target name invalidates the old
execution manifest; freeze an updated one rather than hiding the database change.

## Later model compatibility and smallest implementation increment

These nine lines produce **three current-time feature snapshots**, not nine ML
examples, future target labels or a training/test split. They are controlled
synthetic evidence delivered through Odoo. The current synthetic artifact must
continue rejecting `odoo_projection`; do not rename its source or patch a manifest.

Later inference needs an offline artifact explicitly evaluated for this data
origin, database/domain, exact feature order/semantics, label/mapping versions,
time/quantity validity and support. The original generator used 8–30 history
lines; fixture n=3 meets the technical minimum but adds a support-distribution
gap to evaluate. A compatible artifact may produce equal classes or coefficients:
100/66.67/33.33% is not a promised risk ranking or plan allocation.

Training/evaluation remains separate: the current target uses five contextual
future completions over the next 30 days; at least 20 training examples per class,
temporal label-window separation, supplier-disjoint holdout and non-reused evidence
must hold. These planning suppliers alone cannot establish that evaluation.
Newly read or backdated test records cannot prove knowledge at an older cutoff.
Document an adequate controlled dataset or capture genuine as-of snapshots and
later outcomes. Do not manufacture availability timestamps or downgrade those
gates to fit nine lines. The leaf fraction stays an uncalibrated exposure proxy.

**Next implementation, after manual fixture acceptance:** one task-specific
offline validation/capture command for this fixed manifest. Compose the existing
adapter, raw-context checks, T8 calculator and feature conversion, producing the
three exact snapshots plus origin/time/hash evidence. No generic query endpoint,
framework, schema migration, model fitting, API/UI redesign or MILP changes.
Keep current V2 routes and synthetic practice/saved cases unchanged.

| Regression area | Required checks in that increment |
| --- | --- |
| Exact source/context | Wrong DB despite same numeric IDs, company/supplier/product/UoM, duplicate markers/IDs, unrelated T7 lines and unrequested events rejected before aggregation |
| KPI/support | A/B/C exact percentages; B03 partial n=2 withheld then full n=3; events not counted as lines; preserve neutral cancellation/return/missing-date/overreceipt regressions |
| Time | UTC, half-open exact 365-day window, E≤observed_at≤C and ≤7-day freshness; future completion/late availability rejected; no fabricated retrospective schedule evidence |
| Provenance | Retain `odoo_projection` transport and explicit controlled-synthetic origin, DB, fixture reference, real IDs and acquisition times; stable capture hash; neither test receipt nor KPI promoted to observed truth |
| Model trust | Existing synthetic artifact rejects the new source; context/schema/support/artifact/runtime mismatch fails; no model training/loading through browser/input or zero-risk fallback |
| Existing V2 | Focused synthetic/base/from-odoo/scenario/replay/saved-decision/PDF contracts retain their behavior and old snapshots; capture command does not call planner or persist a planning case |

Full model-to-planning connection is a later explicitly authorized increment.
Its scope includes the source validators and saved retrieval/approval/library/UI/
PDF consumers identified in the assessment, without changing the solver/core.
Acceptance then includes atomic stored-only retry/GET/scenario and original-base
approval/PDF E2E with Odoo/model disabled after creation. Those E2E results cannot
be claimed from this plan or the thin capture command.

## Effort, handoff and approval requested

Planning estimates, not measured commitments; an engineering day means focused
work and excludes waiting for owner actions/data:

- Human backup/neutralized restore/permission verification: **45–90 minutes** if
  credentials, space and existing configuration work; large archives may add time.
- Nine manual orders including pilot and backorder: **60–120 minutes**, plus
  **30–60 minutes** for read-only postconditions/recording. Stop gates can span sessions.
- Thin capture command and focused regression checks: **1–2 engineering days**.
- Subsequent coherent runtime connection with an already accepted compatible
  artifact: provisionally **3–5 engineering days** including downstream regression/
  real service/browser evidence; refine after the artifact contract is accepted.
- Offline model/data promotion is **not included**. Genuine newly captured target
  labels require the full 30-day window plus collection/evaluation; adequate
  training/holdout data may dominate the schedule. No defensible total date yet.

Current outcome: plan and exact preflight evidence prepared; no admin operations,
fixture creation, training, code/schema/requirements changes or Git writes.
No implementation tests were run in this planning task; passing live access tests
remain the prior scoped evidence. Backup quality/restore, clone credentials and
untracked-product receipt compatibility remain owner/pilot gates.

**Approval requested:** owner approves backup and neutralized restoration of
`procurement_poc` to `procurement_v2_history_test_v1`, followed by human-only entry
of these nine orders after clone/pilot gates pass. Source records/product settings
and existing T7 fixtures stay untouched. This approval does not authorize agent
Odoo writes, automatic fixture creation, application/model/schema changes or Git
publication. AGENTS.md's manual-Odoo rule requires human execution and confirmation
before dependent validation; the current user request additionally requires this stop.

Thesis traceability: FR-V2-01/02/03/07, AC-V2-01/02/03, NFR-V2-02/03/04/05/08;
preserve FR/AC-V2-08/10/11/12 and AC-V2-13. Chapters 3–7 gain an exact controlled
ERP-history/KPI integration account; observed predictive validity remains a
separate limitation/future direction. No new CORE requirement or architecture.

## Sources

- Canonical Drive [00 status](https://docs.google.com/document/d/1X2WGVVYn0j1ymX0cv5kQQGIaJiEc7pcLSZYDIrXA3VU/edit),
  [02 roadmap](https://docs.google.com/document/d/1jlTCsRsO8C-MZ2xT-szbFJvExM2OVuphE5524NpIOr4/edit),
  [03 ADRs](https://docs.google.com/document/d/1HzhcD03TAiIpJT4n9_tYLurYT3u68ziRND_E9RHRTW4/edit),
  [06 requirements](https://docs.google.com/document/d/1g0zie-3mEWdrkiBMUET--ST8eCdmOPOVfyjyWXr_Iig/edit),
  [07 development](https://docs.google.com/document/d/1Xgphr_FEurdFlK651s2DTJWlubwt9vii1c5st9iO6E8/edit):
  refreshed 2026-10-14; current 2026-10-14 addenda retain the accepted boundaries.
- [Manual T6](T6_FIXTURE_SETUP.md), [manual T7](T7_FIXTURE_SETUP.md),
  [T7S setup](T7S_MANUAL_SETUP.md), [completed assessment](ODOO_HISTORY_FEASIBILITY_ASSESSMENT.md).
- Existing source: `application/historical_performance.py:66–106,305–399`,
  `supplier_evaluation/history.py:19–48`, `supplier_evaluation/contracts.py:45–123`,
  `supplier_evaluation/dataset.py:65–109,119–166`, guarded addon projection policy.
- Official Odoo 19 [database controller](https://github.com/odoo/odoo/blob/19.0/addons/web/controllers/database.py),
  [manager UI](https://github.com/odoo/odoo/blob/19.0/addons/web/static/src/public/database_manager.qweb.html)
  and [backup/restore service](https://github.com/odoo/odoo/blob/19.0/odoo/service/db.py)
  support the listed public inventory read and proposed manual copy/restore steps.
- Official [Goods purchase receipt source](https://github.com/odoo/odoo/blob/19.0/addons/purchase_stock/models/purchase_order_line.py)
  selects `type=consu` for stock-move receipt calculation/generation without making
  `is_storable` the entry gate. This source review and live metadata support the
  proposed pilot; they do not replace actual acceptance on the pinned local image.
