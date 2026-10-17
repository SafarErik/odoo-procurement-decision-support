# P2 — Backend capabilities

Date: 2026-10-17. Branch: `feature/p2-backend-capabilities` (from `main` at `0d13964`,
after the P1 merge #46). Status: implemented in the working tree, not committed (owner
commits). Plan: [REVAMP_PLAN.md](../REVAMP_PLAN.md) §P2. Requirements touched:
FR-V2-01/02 (Odoo data with provenance), FR-V2-07/09 (explanations, UI), FR-V2-08 /
AC-V2-08 (stress scenarios), FR-V2-10/11/12 / AC-V2-10/11/12 (storage, approval, PDF).

## Problem

- A buyer could only analyse the one quotation group configured in
  `ODOO_HISTORY_PURCHASE_GROUP_ID`; there was no way to see or choose open groups.
- Stress scenarios only allowed stricter conditions (capacity down, demand and price
  up), while the task sheet asks for capacity, demand and price *change*.
- Supplier history, assessment and decision path existed only inside the raw case
  snapshot; there was no per-supplier read model for the UI.
- The approved PDF was English, read like an audit log and contained raw JSON; it
  was not a document a buyer could send as a purchase proposal.
- Two creation paths (`POST /`, `POST /from-odoo`) still scored with the synthetic
  two-feature V1 tree (P1 decision C left this open).

## Decisions (owner, 2026-10-17)

1. Branch `feature/p2-backend-capabilities` cut from `main` after the P1 merge.
2. **Demo cases**: switch to the Odoo-history model and remove the synthetic V1 tree
   from the runtime. Consequence: the demo creation routes are removed; the seeded
   test database `pdss_history_gen` is the demo.
3. **PDF storage**: one immutable artifact per `(case_id, language)` via a new migration.
4. **T18 evaluation tool**: deleted with the demo path (with `t15_demo`, `t15_odoo_demo`);
   rebuilt on the Odoo-history path in P4 (needs seeded 5- and 10-supplier groups).
5. Earlier owner decisions applied: PDF language follows the UI (Hungarian default),
   one "Megrendelési javaslat" page per supplier, audit at the end, no raw JSON;
   scenarios both ways; frontend changes minimal (UI revamp is P3); new code keyed by
   product and supplier.

Own decisions, each recorded below: store Odoo display names in new snapshots;
adaptive decimals in readable tree paths; legacy English PDFs served unchanged; e2e
suite paused until P3.

## Implemented behavior

### 1. Open quotation-group selection

- `GET /api/v2/procurement/quotation-groups?limit=1..20` (service token): the newest
  open groups of the company in `PLANNING_LIBRARY_COMPANY_ID` (`odoo:res.company:N`).
  Each item has product, quantity, unit, currency, supplier count, quotations with
  supplier names and prices, latest order date, and `selectable`/`issue`
  (`unsupported_offer_count`, `not_all_open`, `not_single_line`, `duplicate_supplier`,
  `mixed_context`, `discount_or_tax`), mirroring the case-assembly contract.
- Bounds: one scan of at most 200 newest open orders (`truncated` reported), at most
  20 groups, 20 orders and 40 lines per group, counted before reading. Only
  `search_read`/`search_count`; company filter on every order read. Errors: 503 when
  Odoo is unreachable or the company is not configured, 502 for invalid Odoo data.
- Case creation stays on P1's `GET /odoo-history/preview?purchase_group_id=N` and
  `POST /from-odoo-history`; the UI now takes the group from the listing
  (`ODOO_HISTORY_PURCHASE_GROUP_ID` removed from both settings classes and `.env.example`).
- New Odoo-history snapshots carry `facts.labels`: Odoo display names of suppliers,
  quotations, product and unit read together with the quotations. They are used for
  documents and the overview only, never in planning.

### 2. Stress scenarios in both directions

- Kinds `supplier_outage`, `capacity_change`, `demand_change`, `price_change`,
  `combined`. Capacity: any other integer ≥ 0; demand: any other integer ≥ 1; price:
  any other positive decimal; a value equal to the stored one is rejected (422).
- Same MILP, saved scores, base immutability and stored-only replay unchanged.
- Stored pre-P2 scenarios keep `capacity_reduction`/`demand_increase`/`price_increase`;
  the library maps them to the new names. Exactly what changed and why:
  [MODEL_MILP.md](../MODEL_MILP.md) §6.
- Frontend: renamed options, "higher or lower" hints, equality checks.

### 3. Supplier overview

`GET /planning-cases/{id}/suppliers?language=hu|en` (`application/supplier_overview.py`)
from the validated stored snapshot only: product/supplier keys, Odoo names (when
stored), offer, terms, history window and the seven KPI values with labels and
locale formatting, class label, score, leaf support, model ids, readable tree path
per split plus the leaf sentence, and planned quantities in the minimum-cost plan
and each alternative. Works for pre-P2 synthetic cases too (two-feature labels). No
Odoo read, model load or solve. A company/product-level live overview was not built:
the stored-case overview covers the buyer flow; P3 can add it if the UI needs it.

### 4. PDF v2

- `GET /{id}/approved-pdf/{hash}?language=hu|en` (Hungarian default), response
  header `Content-Language`, file names `megrendelesi-javaslat-…-hu.pdf` /
  `purchase-order-proposal-…-en.pdf`, reference `t17-approved-pdf-v2:{case}:{lang}:{hash}`.
- Layout (`document_adapter/approved_pdf.py`, `layout-v2`): summary page (data-origin
  notice: generated/observed Odoo history or synthetic demo; product; demand; required
  date; selected plan; total cost; supplier count; largest share; exposure with its
  meaning; cost premium; allocation table with shares and total; human decision);
  one "Megrendelési javaslat"/"Purchase order proposal" page per supplier with a
  non-zero quantity (supplier, quotation, product, quantity, unit, unit price, line
  total, currency, required and promised date, MOQ, capacity, availability, price and
  delivery ranges, "not an Odoo Purchase Order" note); audit appendix at the end
  (data source and capture hash, model ids and artifact hash, per-supplier class,
  score, KPIs and readable decision path, solver and policy, decision log, content
  identity, field-level provenance table). No raw JSON. Rendered only from the
  validated approved content.
- Storage: migration `20261019_01` adds `planning_documents.language` (`hu`|`en`),
  primary key `(case_id, language)`; existing rows become `en` without UPDATE (the
  immutability trigger is untouched). A pre-P2 English artifact keeps its v1 reference
  and bytes and is served as is; Hungarian is rendered and stored on first request.
  Downgrade deletes Hungarian rows only.
- UI: "PDF language" select (Magyar/English) next to "View approved PDF"; P3 binds it
  to the UI language toggle.

### 5. Demo cases

- Removed: `POST /planning-cases`, `POST /from-odoo`, `infer_planning_features`,
  `resolve_odoo_planning_input`, setting `SUPPLIER_MODEL_DIRECTORY`, the synthetic
  request schemas, the UI "Demo" tab and "Load prepared Odoo comparison",
  `tools/t15_demo.py`, `tools/t15_odoo_demo.py`, `tools/t18_evaluation.py` and their
  tests (`test_t15_demo`, `test_t15_odoo_planning`, `test_t16_odoo_planning`,
  `test_t18_evaluation`). Deleted with `rm`, not staged.
- Kept: stored synthetic cases stay readable, approvable and printable. The V1 tree code
  in `supplier_evaluation/` remains as offline library code; `tests/legacy_cases.py`
  rebuilds such cases through the application use case so tests keep proving that.
- `tools/t17_demo.py` now requires `--odoo-history GROUP`, runs nine scenarios in both
  directions and approves the alternative only when the scores produced one.

### Fixes found on the way

- **P1 bug**: the case library rejected every Odoo-history case (`invalid_library_data`,
  503) because `case_summary` accepted only synthetic sources. Fixed and covered by a
  memory and a Postgres test.
- The new quotation-group route first bound the Odoo reader at import time, so a test
  read the live `pdss_history_gen` (read-only). It now resolves the reader per call;
  the fast suite also passes with Odoo and database settings blanked.
- Readable tree paths showed e.g. "0,7 nap – legfeljebb 0,7 nap": decimals now grow until
  the value and the threshold differ.

## Evidence (commands actually run, 2026-10-17, Windows, Python 3.11.15 uv venv)

| Check | Result |
| --- | --- |
| `python -m tools.dev check` | PASS — format, lint, compileall, **466 passed**, 49 deselected, `uv pip check` compatible |
| Fast suite with `ODOO_BASE_URL`, `ODOO_API_KEY`, `ODOO_T7S_API_KEY`, `DECISION_DATABASE_URL` blank | 466 passed (no live dependency) |
| `pytest -m "integration and not e2e"` on the disposable PostgreSQL 16 (Podman), API running | **44 passed**, 5 skipped (T6, 2×T7S live fixtures, 2× opt-in live history); includes migration downgrade/upgrade keeping the English PDF byte-identical, one artifact per language, legacy synthetic case readable, library origin filter with an Odoo-history case |
| `RUN_ODOO_HISTORY_LIVE=true pytest tests/integration/test_live_purchase_history.py -m integration` | 2 passed |
| `python -m tools.dev db-up` (dev planning DB) | migration `20261018_01 -> 20261019_01` applied |
| Live API + Odoo: `GET /quotation-groups` | 200; group 1 `[GEN] Steel bracket M8`, 200 Units, HUF, 4 `[GEN]` suppliers, selectable; no token 401; `limit=0` 422; `POST /` and `/from-odoo` 405 |
| `python -m tools.t17_demo run --odoo-history 1 …` | complete in 3.0 s: base, 9 scenarios (outage; capacity −/+; demand +25 % infeasible because of the 2-supplier limit; demand −25 %; price +30 %/−20 %; combined; 5× demand infeasible), approval of alternative 1, No-award, HU PDF; stored cases, exact retries and PDF identical; No-award PDF denied |
| Live `GET /{id}/suppliers?language=hu|en`, PDF hu/en | 200; Odoo names, HU/EN paths; PDFs 10 pages each, v2 references; pages reviewed as images |
| Built-in browser at 397 px: Odoo tab → Load open quotation groups → Group 1 → Use history from Odoo → Review → Calculate and save → What-if price 1545.7→1400 HUF for Supplier 8 | case and scenario saved; cost −7,624 HUF, allocation moved to Supplier 8; no horizontal scroll |
| Browser error state: unchanged price 1545.7 | alert "enter a positive decimal price different from the original…", no request |
| Browser PDF: approved case, PDF language Magyar → English | viewer "Page 1 of 10"; download name `purchase-order-proposal-…-en.pdf` |

## Not verified / remaining

- Hosted CI: not run (nothing pushed).
- `pytest -m e2e`: **0 tests collected**; `tests/e2e/conftest.py` sets
  `collect_ignore_glob` because every browser flow starts from the removed demo. P3
  rebuilds them on the Odoo-history flow (some e2e files still import deleted tools;
  they are not imported while ignored).
- MILP/API latency evaluation (T18): removed; to be rebuilt in P4.
- Browser console shows two `_set_focus` "No element found for ref" errors after
  review/save; this focus code is unchanged since before P2.
- The dev planning database now contains the P2 live-check cases; their stored
  Hungarian/English PDFs were rendered before the tree-path precision fix (stored
  artifacts are immutable; new approvals use the fixed text).

## Limitations

- Supplier and product names exist only in snapshots created after P2 and only as
  Odoo display names; older cases and the creation preview show identities.
- Odoo 19 names quotation groups `purchase.order.group,N`; the UI shows "Group N".
- The listing scans the 200 newest open orders; older open groups need a larger bound
  or paging (`truncated` tells the buyer).
- The stored decision record's demonstration text still says "synthetic ML evidence"
  for Odoo-history cases (immutable `t17-final-decision-v1` contract); the PDF shows it
  only as recorded text in the appendix next to the correct data-origin notice.
- The PDF is a proposal from the approved plan, not an Odoo Purchase Order, and has no
  legal supplier data (address, tax number).
- Exposure and the overview's KPIs are generated-data values in the test database.

## Owner action

1. Review and commit. New files are untracked; deleted files are deleted from the working
   tree but not staged (`git add -A` stages both).
2. Optional `.env` cleanup: `SUPPLIER_MODEL_DIRECTORY`, `ODOO_HISTORY_PURCHASE_GROUP_ID`
   and the P1-removed `ODOO_HISTORY_*` keys are ignored now.
3. Other development databases: `python -m tools.dev db-up` applies `20261019_01`.

## Thesis relevance

- Ch. 4 (design): quotation-group selection as a bounded read-only integration surface;
  one creation path; per-language immutable document storage and its migration.
- Ch. 5 (models): stress scenarios as two-way input changes on the unchanged MILP, with
  the reasoning from the task sheet ([MODEL_MILP.md](../MODEL_MILP.md) §6).
- Ch. 6 (implementation): supplier overview read model, HU/EN explanation texts, PDF v2
  structure (summary, purchase order proposal per supplier, audit appendix).
- Ch. 7 (evaluation): the evidence table above; e2e and latency evaluation open until
  P3/P4.
- Ch. 9: legal supplier data on proposals, Odoo PO creation, paging of large group lists.
