# Final review fixes (2026-10-31)

Branch `feature/final-review` from `d3acab7` (`feature/image-regen`), uncommitted. Development
is closed, so this increment adds no capability: it fixes defects found by a whole-repository
review (code, browser, thesis text and the official task sheet) and corrects stale
documentation.

## Problem

A review of every package, the running UI and the thesis draft found a small number of
defects that contradict stated behaviour, plus stale documentation:

- A case can store five plans (minimum cost, three ε alternatives, the balanced plan), but
  the decision request schema accepted `plan_index ≤ 3`, so the fifth plan could not be
  approved. A random search over small instances produced such a case (4 suppliers,
  K = 2, five distinct plans).
- `GET /api/v1/procurement/rfqs` was the only data route without the bearer token.
- The live demonstration claims reproducibility until 2027-02-28, but with the production
  feature code the four-supplier demo group keeps three settled lines per supplier only
  until about 2027-01-10; later runs failed with a bare HTTP 422.
- UI: a definite 4xx on case creation (FastAPI's list-shaped 422, 400, 429) was reported as
  an uncertain save, trapping the buyer in the recovery panel; a recovered decision left the
  buyer on the Overview tab; the scenario price rejected a Hungarian decimal comma; a stale
  error banner reappeared on the New procurement page; nine text keys were defined twice
  (the earlier definition was never shown); the recovery text named a button that does not
  exist.
- Odoo history: a lagging Odoo container clock made every history read fail (Odoo rejects an
  export end in its future); an invalid export snapshot surfaced as a 422 input error instead
  of an Odoo response error; `extract --data-origin` was never checked against the database.
- The "Odoo is read-only" architecture test could never fail.

## Decision

Fix each defect with the smallest change and a regression test; delete unused frontend code
that would bypass the review step if wired; leave thesis prose to the owner (findings are
listed for chapter updates below).

## Implemented behaviour

| Area | Change |
| --- | --- |
| `backend/app/planning_case_schemas.py` | `plan_index` accepts 0–4 |
| `backend/app/routes/rfqs.py` | router requires `require_trusted_caller` |
| `backend/app/dependencies.py` | history read ends 60 s before now |
| `odoo_adapter/product_history_reader.py` | invalid snapshot → `ProcurementDataResponseError` |
| `tools/demo.py`, `tools/seed_odoo_history.py` | `check_live_history` turns `odoo_history_insufficient` into the stored-evidence message; the constant is documented as an upper bound |
| `tools/train_history_model.py` | `extract` refuses `generated` outside `pdss_history_gen` and `observed` inside it |
| `frontend/planning_client.py` | list-shaped `detail` handled; any other 4xx is a definite rejection |
| `frontend/planning/state_base.py` | recovered decision opens the Decision tab |
| `frontend/planning/state_scenarios.py` | price accepts `12,50` |
| `frontend/planning/state_creation.py` | `rfqs_on_load` clears a stale banner; unused `create_odoo` and `mark_creation_dirty` removed |
| `frontend/i18n*.py` | nine shadowed keys removed; recovery text names the real button; Hungarian price examples use a decimal comma |
| `frontend/app.py`, `workspace.py`, `theme.py` | page title "New procurement", stale docstrings, unused colour removed |
| `tests/test_architecture.py` | every JSON-2 method the adapter can call must be a read method |
| Docs | `ARCHITECTURE.md` (balanced plan, routes, three migrations, document key, token rule, tools), `RUNBOOK.md` (wizard steps), `MODEL_ML.md` (reproduce from the stored export; origin guard; path rendering) |

New tests: `test_every_storable_plan_index_passes_the_request_schema`,
`test_rfq_route_requires_the_service_token`, `test_each_text_key_is_defined_in_exactly_one_module`,
`test_live_demo_points_to_stored_evidence_when_a_supplier_ran_out_of_history`,
`test_history_extraction_refuses_a_data_origin_that_contradicts_the_database`,
`test_a_definite_client_error_on_creation_is_not_reported_as_uncertain`,
`test_returning_to_new_procurement_drops_a_stale_error_banner`,
`test_recovered_decision_opens_the_decision_tab`, a `12,00` scenario case, a duplicate-line
reader case and `test_odoo_adapter_calls_only_read_methods`. The recovery, reader and
architecture tests were confirmed to fail without their fix.

## Evidence (commands actually run, Windows, Python 3.11.15)

| Command | Result |
| --- | --- |
| `python -m tools.dev check` on clean `d3acab7` | 535 passed |
| `python -m tools.dev check` on this tree | format, lint, compile, dependency check pass; 551 passed, 54 deselected |
| `pytest -m "integration and not e2e"` (disposable test DB) on this tree | 46 passed, 5 skipped (the opt-in live-Odoo contracts) |
| `pytest --collect-only` | 605 tests: 551 fast, 51 integration, 3 e2e (was 589 / 535 / 51 / 3) |
| Built-in browser, `tools.dev api` + `ui`, live Odoo `pdss_history_gen` | Home, Cases, case tabs (HU and EN), New procurement list, 375 px without page overflow; after the fixes: `/rfqs` titled "New procurement", Scenarios tab renders, no console errors |
| Live-window computation with `supplier_evaluation.purchase_history.feature_values` on `.artifacts/ml/history_export.json` | all four demo suppliers score until 2027-01-10 12:00 UTC, not on 2027-01-11 |

Not run: `pytest -m e2e` (Playwright not set up in this session), `tools.dev demo`,
`tools.milp_evaluation`, `train_history_model report`, hosted CI. The evidence JSON files are
unchanged.

## Limitations kept

- The risk-validity range is the hard-coded 1–1000 proxy (`QuantityValidity(1, 1000)`); an
  effective upper bound above 1000 is rejected with 422.
- Saved-scenario rows show only kind and demand; two price changes look alike.
- `supplier_evaluation.history_model` still imports the legacy `evaluation`/`model` modules,
  which import the solver adapter.
- Not changed: UI terminology drift (ügy/összehasonlítás, szállító/beszállító), English
  browser titles, the 180-day request versus the 366-day/500-line export ceiling.

## Thesis relevance

- Ch. 7.2 and 8: test counts become 605 (551 fast); integration unchanged at 51.
- Ch. 7.5: live reproduction until about 2027-01-10, not 2027-02-28.
- Ch. 3.2/6.6: the UI asks a reason for every decision; the backend requires it only for a
  non-minimum plan and No-award.
- Ch. 6.6: plan PDF order is allocation → supplier assessment → decision; the audit PDF has
  solver settings and outcome but no per-stage run log.
- Ch. 6.5: one `PlanningState` composed of six mixins, not separate state classes.
- Ch. 7.3: 31% problematic is the ten held-out suppliers after the boundary (all 40: 25.8%).
- Ch. 5.2: t0 is the history read time, about half a second before the case is stored.
