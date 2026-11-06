# R1 — Remove pre-P2 legacy code paths

Date: 2026-11-05. Worktree branch `claude/eloquent-benz-007a1d` on `main` `26536bc`.
Not committed; the owner commits. Drive was not changed. Official task: no clause changes
(technical debt only); FR-V2/AC-V2 definitions unchanged. Touches the evidence routes of
FR-V2-02/03 (ML), FR-V2-10/11/12 (storage, approval, PDF) and NFR-V2-03 (generated vs.
observed provenance).

## Problem

The code kept several layers whose only purpose was to read records stored before P2:
the synthetic T14 Decision Tree pipeline (plus a test helper that rebuilt synthetic demo
cases with it), branches for `t14_synthetic` / `controlled_synthetic` /
`odoo_quotations_synthetic_history` snapshots, one-directional scenario kind names,
v1/v2 approved-PDF references, captures without a declared data origin, and a
"demo vs. Odoo" library filter. The T7/T8 historical-KPI path and the unused
`GET /api/v1/procurement/rfqs` route had no current caller either. A reader learning the
code had to tell current from dead paths in every module.

## Decision

Owner decision 2026-11-05: records stored before P2 need not stay readable; the owner
resets the development database. So every compatibility layer for them is deleted, with
no replacement abstraction. Behaviour for records the current code writes stays the
same: persisted identifiers they carry (`t15-controlled-planning-v1`,
`t17-final-decision-v1`, `t17-approved-planning-v1`, `t17-approved-pdf-v3`, the
`t14-assessments:` / `t14-quantity-independent-controlled-proxy:` risk-context prefixes,
the advisory-lock prefixes, the audit text "Controlled demonstration; synthetic ML
evidence; …") are unchanged. Renaming them is out of scope.

## Implemented behaviour

Net diff: runtime packages +254 / −2512 lines, tests +331 / −2038, docs +45 / −74.

Deleted modules (lines):

| Module | Lines | Why it could go |
| --- | --- | --- |
| `supplier_evaluation/dataset.py`, `model.py`, `artifacts.py`, `cli.py`, `evaluation.py` | 279 + 266 + 46 + 58 + 162 | T14 synthetic pipeline; no runtime or `tools/` caller |
| `supplier_evaluation/history.py` | 106 | synthetic receipt → feature path and T8 conversion |
| `application/historical_performance.py`, `odoo_adapter/historical_performance_reader.py` | 505 + 269 | T7/T8 KPI path; only tests and the T14 dataset used it |
| `application/rfqs.py`, `odoo_adapter/rfq_reader.py`, `backend/app/routes/rfqs.py` | 51 + 137 + 68 | `/api/v1/procurement/rfqs`; not used by UI, tools, CI or compose |
| `tests/legacy_cases.py`, `tests/t14_helpers.py` | 225 + 46 | rebuilt pre-P2 cases |
| `tests/test_t14_dataset.py`, `test_t14_model.py`, `test_t14_runtime.py`, `test_historical_performance.py`, `test_odoo_historical_performance_adapter.py`, `test_rfqs.py`, `test_odoo_adapter.py` | 51 test functions | covered only deleted code |

Moved, not rewritten:

- `classification_metrics`, `runtime`, `tree_state` → `supplier_evaluation/history_model.py`
  (the ML package no longer imports `optimization_adapter`).
- `ProcurementDataUnavailable`, `ProcurementDataResponseError` → `application/errors.py`.
- `comparison_case_reader` now imports `_prefixed_id` from `product_history_reader`
  (there were two copies).

Removed shims and branches:

- `contracts.py`: T14 versions, `FEATURES`, `CLASSES`, `SEED`, `SYNTHETIC`,
  `LEGACY_HISTORY_DATA_ORIGIN`, `Assessment.class_name`; the contracts accept only the
  Odoo-history feature, label, mapping and dataset versions.
- `planning_input.assemble_planning_input`: only `OdooHistoryPlanningFacts` with captured
  history. `SupplierFacts.receipts` stays (always empty) because it is part of the stored
  snapshot JSON.
- `planning_cases`: `validate_snapshot` requires an Odoo-history snapshot;
  `create_planning_case(facts=…, base_kind=…)`, `LEGACY_SCENARIO_KINDS`, `DEMO_INPUT_KIND`
  and `case_origin` are gone.
- `planning_decisions._saved_evidence`, `planning_library.case_summary`,
  `supplier_overview` (`SOURCE_CLASSES`, synthetic features and leaf text),
  `document_adapter/approved_pdf.py` (synthetic notice and origin) and
  `planning_history.capture_origin` (now requires `data_origin`): no synthetic branch.
- `planning_documents`: only `t17-approved-pdf-v3` references are served. A stored v1/v2 row
  is kept but fails closed (503 `approved_pdf_unavailable`). The current code never wrote
  v2 after the plan/audit split, and the database is reset.
- Library and API: the `origin` filter (`demo`/`odoo`), the `origin` field of library
  items and of `PlanningCaseResponse`, and the persistence filter are removed. With demo
  cases gone it could only ever say "odoo". Library items keep `source_kind` and
  `data_origin` (generated/observed).
- Frontend: origin filter select and state, `VIEW_ALIASES` ("whatif" bookmarks), the
  `synthetic-` supplier label, the synthetic class/summary/badge/note texts, translation
  keys `kind_capacity_reduction`, `kind_demand_increase`, `kind_price_increase`,
  `badge_synthetic`, `synthetic_note`, `class_schedule_*`, `class_meaning_synthetic`,
  `history_summary_synthetic`, `demo_supplier`, `filter_origin`, `filter_all_sources`,
  `filter_odoo`, and the v1/v2 PDF references in `planning_pdf_client`.
- `backend/app/config.py`: `run_t6_live_contracts`, `run_t7s_live_contracts`,
  `run_t7_live_contracts`. The live test reads `RUN_T6_LIVE_CONTRACTS` /
  `RUN_T7S_LIVE_CONTRACTS` from the environment, like `TEST_DATABASE_URL`. The T7 fixture
  test (T8 vertical slice) and the open-RFQ live test were deleted. `RUN_T7_LIVE_CONTRACTS`
  left `.env.example`.

Kept on purpose:

- `PlanningPolicy.diversification_epsilon` and `AlternativeRun.kind` stay `omit_default`.
  Current records omit them (no balanced allowance; every risk run), and stored JSON must
  re-encode exactly. Only the comments changed.
- The Odoo addon `t7s_inventory_history_projection` keeps its `read_bounded_history`
  method and its policy test (`test_t7s_projection_policy.py`) plus the live T7s security
  test. This is deployed Odoo code. Removing it needs an addon upgrade (follow-up below).
- `/api/v1/health` (CI `integration.yml`, `tools/demo.py`, e2e and runtime tests use it).
- `tools/` needed none of the deleted code (`demo`, `milp_evaluation`, `seed_odoo_history`,
  `train_history_model`, `t17_demo` only use the Odoo-history path).
- Database: no migration. The check constraints admit only current values
  (`snapshot_version`, `language`, `kind`). Old migrations are unchanged.

Remaining hits of `rg -n "legacy|LEGACY|t14|T14|SYNTHETIC|synthetic_history"` over the
runtime packages: `supplier_evaluation/planning_bridge.py:66-67`, the persisted
`t14-assessments:` and `t14-quantity-independent-controlled-proxy:` prefixes written into
every current risk context (kept; renaming is the later constants increment).

Tests: the shared stored-case fixture (`test_t16_stored_planning.stored_cases`, used by
about 15 modules) and `test_t15_planning_api` now create real Odoo-history cases through
`POST /from-odoo-history` over the existing fake read-only Odoo
(`tests/t15_helpers.odoo_case_api`, `controlled_terms`, `create_case`). The model is trained
once per session (new `tests/conftest.py`, fixture `odoo_history`). The controlled
workload is demand 10, at most two suppliers, 80 % concentration and ε = 0.1. Odoo prices
are 9 / 12 / 10 USD and capacities 6 / 8 / 10, so the cheapest supplier is also the
riskiest. The expected values changed from the synthetic case (€102 / €109) to $94 / $98,
with outage delta $10. `test_t14_planning_bridge` now uses history-model assessments.
Tests that asserted legacy readability now assert that the legacy value is rejected (unknown
scenario kind, capture without origin, v1/v2 PDF rows → 503, `origin` query → 422).

## Evidence (commands run on this worktree, 2026-11-05)

- `python -m tools.dev check` → ruff format/check pass, compileall pass,
  **458 passed, 51 deselected**, `uv pip check` OK (run after the last code edit). The fast-suite count before R1 was 504 (REVIEW_FIXES); 51 test functions
  were deleted with the code they covered.
- `pytest -m "integration and not e2e"` against a freshly created disposable test DB
  (`infra/persistence/compose.test.yaml`), with Odoo running and the owner's `.env`:
  **42 passed, 4 skipped, 2 failed**. The 2 failures were `test_runtime_services` because
  no API ran on :8000. With the API started, `tests/integration/test_runtime_services.py`
  → **3 passed**. Skips: `RUN_T6_LIVE_CONTRACTS`, `RUN_T7S_LIVE_CONTRACTS`,
  `RUN_ODOO_HISTORY_LIVE` (×2) not set.
- Running API: `GET /api/v1/procurement/rfqs` → 404, `GET /api/v1/health` → 200.
- Browser (built-in, Reflex dev server): `/cases` filter bar shows search, decision status
  and refresh only, at desktop width and 375 px; the library shows its error state because
  the development planning DB was not running.
- `ponytail-review` over the diff: the duplicated `_prefixed_id` was fixed, the Reflex
  lock files rewritten by the UI run were reverted, and the always-empty receipts sort in
  `normalize_planning_facts` was left (stored JSON shape).

**Unrun: `python -m tools.dev demo` / `tools.demo`.** It was started against a fresh
test DB with the owner's model, and Odoo answered **HTTP 401** to the history reader key
(`ODOO_T7S_API_KEY`) on `read_product_history`. The quotation-group read with
`ODOO_API_KEY` worked. The key has to be renewed (RUNBOOK §5) before the live demo can
run. `docs/evidence/P4_DEMO_REPORT.json` was not touched. The e2e browser suite was not run.
Hosted CI not run.

### Follow-up fix 2026-11-06: date-independent stored-case fixture

The PR's Quality CI failed in 7 tests (`test_t16_scenarios` exposure `44.7 / 100` instead of
`31.2 / 100`, `test_t16_cockpit` `25.9` instead of `12.0` points). They had passed on
2026-11-05. Cause: `build_history` generated the history from the real clock, and the
training boundary snaps to the 1st or 16th of the month, so the trained tree and every
saved exposure value depended on the calendar day.

Fix (tests only, no runtime change): the session fixture `odoo_history` builds the history
at a fixed `REFERENCE_NOW` (2026-11-05 18:00 UTC, `tests/conftest.py`;
`build_history(directory, now=None)`). `t15_helpers.odoo_case_api` pins `datetime.now`
to the end of that history in the four modules that read the clock during case
creation: `application.odoo_planning_input`, `backend.app.dependencies` and the two Odoo
readers. Case creation time and decision time still use the real clock; they
do not affect plans or scores. The module fixture `history` of
`test_odoo_purchase_history.py` still uses the real clock; its tests assert no exact
values.

Evidence: the 88 affected tests pass. They pass again (170 tests including decisions,
PDFs, library and frontend) when a throwaway pytest plugin moves the remaining real-clock
reads (`planning_cases`, `planning_decisions`) by +40 and +400 days.
`python -m tools.dev check` passed after the fix: ruff format/check, compileall,
458 passed / 51 deselected, `uv pip check` OK. Hosted CI: see PR #58.

## Limitations

- Any pre-P2 case, decision or document left in a database is now unreadable. Its GET
  returns 503 `invalid_persisted_case`, and a library page containing one returns 503
  `invalid_library_data`. Reset the database (below).
- The library no longer offers a data-source filter. Screenshots in `docs/evidence/p3/`
  still show it until `tools/ui_screenshots.py` is rerun.
- Test file names still carry increment numbers (R2).

## Database reset for the owner

Development planning database (RUNBOOK §4; deletes all stored cases):

```powershell
podman compose -f infra/app/compose.yaml down -v
python -m tools.dev db-up
```

The disposable test database needs nothing: it has no volume and integration tests
recreate its schema.

## Drive follow-ups (not done; owner request needed)

- 03_ARCHITECTURE_DECISIONS: ADR-033/036 say v1/v2 PDFs stay valid. Record that R1 serves
  only v3. Check ADR-028/031 (not read in this session) and any note saying pre-P2 /
  synthetic cases stay readable; record the R1 owner decision of 2026-11-05.
- 07_DEVELOPMENT_STATUS / 00_THESIS_STATUS: R1 entry (legacy removal, RFQ route and T7/T8
  path removed, origin filter removed, live demo blocked by the expired history key).
- 06_REQUIREMENTS_BASELINE: no definition change; the AC evidence links that cite
  `test_t14_*`, `test_historical_performance.py` or `test_rfqs.py` should point to the
  current tests.
- Follow-up increment: remove `read_bounded_history` from the Odoo addon (needs an addon
  upgrade in `pdss_history_gen`) together with `test_t7s_projection_policy.py` and the
  live T7s test.

## Thesis chapter relevance

Chapter 6 (implementation): the ML package is now only the Odoo-history pipeline, and the
case contract has one creation path. Chapter 7 (testing): the shared fixtures exercise the
real creation route instead of a synthetic rebuild. Chapter 8/9: the expired history key
and the addon clean-up belong to the operating notes, not to new scope.
