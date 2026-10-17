# P1 — Odoo-sourced purchase history and ML retraining

Date: 2026-10-17. Branch: `feature/Odoo-history-revamp-new-training` (from `main` at
`cd52f23`, after the P0 merge #45). Status: implemented in the working tree, not
committed (owner commits). Plan: [REVAMP_PLAN.md](../REVAMP_PLAN.md) §P1.
Model documentation: [MODEL_ML.md](../MODEL_ML.md).

## Problem

The supplier model was trained on a synthetic generator whose label was a
near-deterministic function of an 80% adherence threshold (2 features, effectively
one), so it could not be defended as supplier evaluation from historical performance.
The only Odoo-history path was a fixed profile of 9 hand-made lines feeding that
same synthetic tree through a "qualification" wrapper. Odoo was not running on the
recreated Podman machine.

## Decisions (owner, 2026-10-17)

1. Train from purchase history **read from Odoo**, so the pipeline works unchanged
   on real data; the history itself is generated and labelled as such.
2. A scripted administrator **seeding tool** may write generated history into the
   dedicated test database `pdss_history_gen` only; the runtime stays read-only.
3. (A) The seeder back-dates business timestamps of its own generated records
   (simulated clock, documented). (B) The fixed `local-v1` history path is removed.
   (C) Demo cases keep the synthetic V1 tree for now. (D) One model per company,
   product-independent features.
4. Own decisions during the work, each recorded in MODEL_ML.md:
   - Label changed after run 1 from "late share ≥ 1/3" to "mean delay > 3 days or fill
     < 85%" because the first one flipped on single lines (structural reason, see §4).
   - Seed extended from 16 to 40 suppliers after run 2 because supplier-disjoint,
     time-purged CV folds had only 25–125 rows. The first 16 suppliers are unchanged.
   - Quotation-reader rights moved into a reproducible addon group (`pdss_quotation_reader`)
     instead of hand-made ACLs; the projection addon keeps no generic ACL.
   - No class weighting: checked on train-only folds, not better.

## Implemented behaviour

- **Odoo**: `infra/odoo/addons/t7s_inventory_history_projection` 19.0.2.0.0 adds
  `procurement.product.history.export.read_product_history`: one company and product,
  Expected Arrival window ≤366 days, ≤500 lines, confirmed lines with their completed
  receipts (backorder link) and returned quantity; same reader group, no CRUD surface.
  New addon `pdss_quotation_reader`: read-only ACLs for quotations, lines, products,
  partners, currencies, units.
- **Seeder** `tools/seed_odoo_history.py`: deterministic plan (seed 20261017, clock
  2026-10-17), 3 products, 40 suppliers with seven behaviours and drift, 2,546
  confirmed orders, 2,823 receipts (402 partial/short-closed orders), one open
  quotation group of four tax-free RFQs. Refuses any database other than
  `pdss_history_gen`, requires `pdss.seed_target` in that database and an admin key,
  is resumable, tags everything `PDSS-GEN-P1` / `[GEN]`. Runtime code never imports it
  (architecture test).
- **Neutral contract** `application/purchase_history.py` and adapter
  `odoo_adapter/product_history_reader.py` (fail-closed mapping, truncation guard).
- **ML** `supplier_evaluation/purchase_history.py`, `history_model.py`: seven as-of
  features, next-60-day label, held-out suppliers + time boundary, depth by
  time-series CV on train only, majority / expert-rule / learned-stump baselines,
  confusion matrix, per-class F1 and support, score ROC AUC, trusted artifact with
  checksum and semantic id, readable path text. Contracts are versioned
  (`odoo-purchase-history-features-v2` etc.) next to the V1 demo contracts.
- **Training CLI** `tools/train_history_model.py extract|train|all`: read-only
  extraction with the restricted history user, offline training, dataset card and
  report under `.artifacts/ml/`.
- **Case creation**: `GET /odoo-history/preview?purchase_group_id=N` and
  `POST /from-odoo-history {purchase_group_id, terms}` read the quotation group, then
  180 days of the product's history, freeze the raw lines in the snapshot, derive
  features at read time and score with `SUPPLIER_HISTORY_MODEL_DIRECTORY` (must match
  database and company). Stored cases re-derive and check features from stored lines;
  replay, scenarios, decisions and PDF never read Odoo, re-score or re-solve. A
  supplier with fewer than 3 settled lines blocks creation (`odoo_history_insufficient`,
  422); a missing/incompatible model blocks it with 503; nothing is saved in either case.
- **UI/PDF**: history rows and assessment texts show the new features and label; the
  readable path covers the new features; explanatory copy distinguishes Odoo history
  from the synthetic demo; PDF records the model's data origin.
- **Removed**: `supplier_evaluation/qualified_odoo.py`, `odoo_compatibility.py`,
  `odoo_adapter/planning_history_reader.py`, `config/odoo_history_local_v1.json`, their
  tests and the old Odoo-history browser e2e test; settings `ODOO_HISTORY_DATABASE`,
  `ODOO_HISTORY_API_KEY`, `ODOO_HISTORY_QUOTATION_API_KEY`, `ODOO_HISTORY_MODEL_DIRECTORY`.
- Fixes found on the way: `tools.dev ui` now runs the venv's `reflex` without
  activation; `t17_demo --odoo-history <group>` uses scenario changes relative to the
  read quotation.

## Evidence (commands actually run, 2026-10-17, Windows, Python 3.11.15 uv venv)

| Check | Result |
| --- | --- |
| `python -m tools.dev odoo-up` (Podman 6.1.4) | Odoo 19 HTTP 200, empty database list |
| Owner manual blocks 1–2 + read-only probes | DB `pdss_history_gen`; stock, purchase, purchase_stock, purchase_requisition, both addons installed; `pdss.seed_target` set; seed key = system admin; quotation user internal, non-admin, purchase models read-only, `stock.move`/`stock.picking` denied; history user portal, `stock.*` denied; export 200, 367-day window 422, quotation key on export 403 |
| `python -m tools.seed_odoo_history apply` (8-order smoke, then full, then batch 2) | 2,546 orders + 4 RFQs (`search_count` 2,550), exit 0; backdated receipts and backorder chain verified through the restricted export |
| `python -m tools.train_history_model all` | 2,546 lines extracted; 1,804 rows; depth 4; primary test macro F1 tree 0.589 / majority 0.409 / stump 0.594 / expert rule 0.658 ([report](../evidence/P1_ML_REPORT.json)) |
| `python -m tools.t17_demo run --odoo-history 1 …` against live API + Odoo + planning DB | base case, 6 scenarios (last infeasible), approval of alternative, No-award, PDF; stored cases, exact retries and PDF identical; No-award PDF denied (5.5 s) |
| Built-in browser, `/planning` → Odoo → Use history from Odoo → review → save → Suppliers | preview of 4 suppliers, saved case with minimum-cost plan and alternative, readable path ("Lateness spread (5.0 days) is above 4.5 days …"), checked at 375 px width; API error states 422 (unknown group) and 401 (no token) |
| `RUN_ODOO_HISTORY_LIVE=true pytest tests/integration/test_live_purchase_history.py -m integration` | 2 passed |
| `pytest -m "integration and not e2e"` on disposable PostgreSQL 16 + live Odoo | 42 passed, 5 skipped (T6/T7S fixture contracts, opt-in live history) |
| `python -m tools.dev check` | PASS — format, lint, compileall, 510 fast tests passed (56 deselected), `uv pip check` compatible |

## Not verified / remaining

- Hosted CI on the pushed branch: not run (nothing pushed).
- e2e browser suites (`pytest -m e2e`): not run; the old Odoo-history e2e test was
  removed, a new one belongs to P3's UI.
- Live T6/T7/T7S fixture contracts: skipped — those fixtures were not recreated in
  the new database (the T7S security contract is covered by the new live test).
- The addon record still reports `installed_version` 19.0.1.0.0 although the 2.0.0
  code is active; **Apps > T7-S Inventory-History Projection > Upgrade** aligns it.
- The internal quotation user receives full `stock.move.line` rights from Odoo's
  default `Role / User` group (not granted by us; the runtime never calls it).
- The demo path still uses the synthetic V1 tree (decision C).
- Several UI strings still say "Synthetic exposure"; buyer wording is P3.
- `.claude/launch.json` (local dev-server config) is untracked; commit or ignore.

## Limitations

- Generated data: the metrics validate the method, not real suppliers. On unseen
  suppliers the tree beats the majority baseline but not the hand-written on-time
  rule (MODEL_ML.md §6 explains the generator alignment and the train/test drift).
- Back-dated business timestamps; Odoo's technical create/write dates show the seeding day.
- Expected Arrival is read as currently stored; returns are not yet used in features.
- 10 held-out suppliers; overlapping semi-monthly windows make rows correlated.
- Leaf frequencies are uncalibrated scores.

## Owner action

1. Review and commit (deletions are already staged by `git rm`; new files untracked).
2. Optional: Odoo **Apps > T7-S Inventory-History Projection > Upgrade**.
3. Revoke the 1-week seeding admin key when no further seeding is needed.

## Thesis relevance

- Ch. 3–4: Odoo as the data source; read-only runtime vs. scripted test-data seeding;
  addon export as the bounded integration surface; reproducible security groups.
- Ch. 5: feature and label design, leakage-safe windows, why the first label failed.
- Ch. 6: pipeline (seed → export → dataset → train → artifact → case), capture and
  stored-only replay.
- Ch. 7: evaluation protocol and the honest result table (tree vs. baselines, AUC,
  run log), plus the generated-data caveat.
- Ch. 9: observed data, calibration, class imbalance and drift handling, returns as a
  feature, Expected Arrival versioning.
