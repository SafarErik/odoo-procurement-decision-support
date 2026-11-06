# R2 — Test suite structured by capability

Date: 2026-11-06. Worktree branch `claude/r2-test-structure-3ba511` on `main` `5f475da`.
Not committed; the owner commits. Drive was not changed. Official task: no clause changes
(technical debt only); FR-V2/NFR-V2/AC-V2 definitions unchanged. Production code is
untouched; only `tests/`, docs and one CI comment changed.

## Problem

Test files were named after the increment that created them (`test_t13_planning.py`,
`test_t17_decisions.py`, `test_p3_frontend.py`, …), so a reader could not tell from a name
what a file proves. About 60 import lines pulled fixtures and builders out of other test
modules (`from tests.test_t16_stored_planning import stored_cases as stored_cases`), which
made the fixture graph hard to follow and tied unrelated modules together. Several
fixtures and helpers were copied with small differences: `configured` ×6 with five
different shapes, `headers` ×3 with two tokens, `forbidden` ×3, `consume` ×3, `imports` ×2.

## Decision

- Shared fixtures live only in conftest files; shared non-fixture code only in the new
  `tests/helpers/` package. No test module imports from another test module.
- Each shared `configured` variant really had a different shape, so each became one
  conftest fixture named by what it provides (below). The one local variant
  (`test_scenario_api.py`) became `controlled_api`.
- One test token (`history-test-token`) and one `headers`, `forbidden`, `consume`.
  The stored-case tests set the backend token explicitly, so the value change from
  `t16-test-secret` changes no assertion.
- `history` (current hour, real clock) and `odoo_history` (fixed `REFERENCE_NOW`) stay
  separate on purpose: tests that use `fake_odoo` let case creation read the real clock,
  so they need history that ends now. `odoo_history`-based exact values stay date-independent.
- `_request` / `_evidence` in `test_odoo_purchase_history.py` and
  `test_odoo_inventory_projection_policy.py` stay local: they build inputs for two
  different addon policies.
- Not renamed (later increments): persisted identifiers in test data
  (`t15-controlled-planning-v1`, `t17-*`, lock prefixes, `PDSS-GEN-P1`), the live-contract
  helpers in `tests/integration/test_live_odoo_contract.py` (`_t6_*`, `_t7s_*`, tied to the
  T6 fixture records, the T7-S addon and `RUN_T7S_LIVE_CONTRACTS` / `ODOO_T7S_API_KEY`), the
  addon directory `t7s_inventory_history_projection`, and `tools/t17_demo.py`.

## Old → new file map

| Old | New |
| --- | --- |
| `tests/test_t13_planning.py` | `tests/test_milp_planning.py` |
| `tests/test_t13_solver_runtime.py` | `tests/test_solver_runtime.py` |
| `tests/test_t13_architecture.py`, `tests/test_t14_architecture.py` | merged into `tests/test_architecture.py` |
| `tests/test_t14_planning_bridge.py` | `tests/test_risk_bridge.py` |
| `tests/test_t15_planning_api.py` | `tests/test_scenario_api.py` |
| `tests/test_t16_scenarios.py` | `tests/test_frontend_scenarios.py` |
| `tests/test_t16_cockpit.py` | `tests/test_frontend_explanations.py` |
| `tests/test_t16_acceptance.py` | `tests/test_saved_result_presentation.py` |
| `tests/test_t16_stored_planning.py` | `tests/test_frontend_stored_case.py` |
| `tests/test_t17_decisions.py` | `tests/test_decision_api.py` |
| `tests/test_t17_frontend.py` | `tests/test_frontend_decision.py` |
| `tests/test_t17_demo.py` | `tests/test_full_http_flow.py` |
| `tests/test_t21_documents.py` | `tests/test_approved_documents.py` |
| `tests/test_t7s_projection_policy.py` | `tests/test_odoo_inventory_projection_policy.py` |
| `tests/test_p3_frontend.py` | `tests/test_frontend_presentation.py` |
| `tests/test_p4_validation.py` | `tests/test_validation_tools.py` |
| `tests/integration/test_t15_planning_postgres.py` | `tests/integration/test_planning_postgres.py` |
| `tests/integration/test_t17_decisions_postgres.py` | `tests/integration/test_decisions_postgres.py` |
| `tests/integration/test_t21_documents_postgres.py` | `tests/integration/test_documents_postgres.py` |
| `tests/t15_helpers.py` | `tests/helpers/in_memory_uow.py` + `tests/helpers/planning_api.py` |
| `tests/frontend_patching.py` | `tests/helpers/frontend_patching.py` |

Renamed test functions: `test_t13_is_required_in_python_311_quality_not_an_optional_skip`
→ `test_solver_is_required_in_python_311_quality_not_an_optional_skip`,
`test_t7s_addon_is_projection_only` → `test_inventory_projection_addon_is_projection_only`.
The architecture self-checks that listed `test_t13*` / `test_t14*` by glob now name the
renamed files explicitly. Module docstrings that only named an increment (P1–P4, T6, T7-S,
T16) now name the capability; every test module already had a docstring.

## Fixture and helper map

| Name | Where | Was |
| --- | --- | --- |
| `odoo_history` (session) | `tests/conftest.py` | unchanged (R1) |
| `history` (module) | `tests/conftest.py` | `test_odoo_purchase_history.history` |
| `fake_odoo` → `(calls, uow)` | `tests/conftest.py` | `test_odoo_purchase_history.configured` |
| `stored_cases` (module) | `tests/conftest.py` | `test_t16_stored_planning.stored_cases` |
| `decision_api` → `(client, uow, base, child, infeasible)` | `tests/conftest.py` | `test_t17_decisions.configured` |
| `scenario_state` → `(state, uow, base, posts, transport)` | `tests/conftest.py` | `test_t16_scenarios.configured` |
| `prepared_state` → `(state, form)` | `tests/conftest.py` | `test_creation_review.prepared_state` |
| `postgres_history_api` → `(engine, factory, payload, calls)` | `tests/integration/conftest.py` | `test_t15_planning_postgres.configured` |
| `postgres_decision_api` → `(engine, factory, client, base, child)` | `tests/integration/conftest.py` | `test_t17_decisions_postgres.configured` |
| `DATABASE`, `COMPANY`, `quotation_payloads`, `plan_lines`, `build_history`, `export_response`, `install_fake_odoo` | `tests/helpers/odoo_fakes.py` | `test_odoo_purchase_history`, `test_odoo_comparison_case_adapter._payloads` |
| `BASE`, `TOKEN`, `headers`, `forbidden`, `odoo_case_api`, `controlled_terms`, `create_case`, `intent`, `approve` | `tests/helpers/planning_api.py` | `t15_helpers`, `test_t17_decisions`, `test_t15_planning_api`, `test_t21_documents`, `test_t15_planning_postgres.create` |
| `MemoryPlanningUnitOfWork` (+ decisions, documents) | `tests/helpers/in_memory_uow.py` | `t15_helpers` |
| `DAY`, `supplier`, `request`, `scored`, `exhaustive` | `tests/helpers/milp_requests.py` | `test_t13_planning` |
| `patch_client`, `consume`, `event` | `tests/helpers/frontend_patching.py` | `frontend_patching`, three `consume` copies, `test_t16_scenarios.event` |
| `create_base_case`, `no_horizontal_scroll` | `tests/helpers/browser.py` | `test_cases_scenarios_mobile_browser._create_case` / `_no_horizontal_scroll` |

`create_case` now sends `headers(key)` (token + key) instead of only the key; the token is
the one the client already sent by default, so the request is the same. The integration
`create(client, payload)` became `create_case(client, payload["terms"])`, which posts the
same body. The dead `copy_payload` helper was deleted.

## Evidence (commands actually run, Python 3.11 venv in the worktree)

| Command | Before (main `5f475da`) | After |
| --- | --- | --- |
| `pytest --collect-only -q -m "not integration and not e2e"` | 458 | 458 |
| `pytest --collect-only -q -m "integration and not e2e"` | 48 | 48 |
| `pytest --collect-only -q -m e2e` | 3 | 3 |

The sorted test-function IDs (path stripped) are identical before and after, except for
the two renamed functions, random UUIDs inside parametrize IDs, and the token value inside
one parametrize ID (`../other-t16-test-secret` → `../other-history-test-token`).

- `pytest -q -m "not integration and not e2e"` → 458 passed.
- `python -m tools.dev check` → format, lint, compile, 458 passed, `uv pip check` OK.
- `rg "from tests\.test_|import tests\.test_" tests tools` → empty.
- `rg -n "test_t1[3-7]|test_t21|test_t7s|test_p[34]_|t15_helpers|t14_helpers" -g '!docs/history/**'`
  → only dated handoff text (`P0`, `P2`, `P3`, `P3_LIBRARY_SEARCH_RELOAD_FIX`, `P4_VALIDATION`,
  `P4_RERUN_AND_PDF_FIXES`, `PDF_PLAN_AND_AUDIT_SPLIT`, `R1`) and the file-hash pin in
  `docs/evidence/GUIDED_WORKSPACE.json`. These record commands and files as they were when
  run; none is a markdown link, so they were left as written (use the map above).
- `pytest -m "integration and not e2e"` against a fresh disposable test PostgreSQL
  (`TEST_DATABASE_URL` on 127.0.0.1:55432), run twice (before and after the review fix)
  → 27 passed, 19 skipped (live Odoo opt-ins), 2 failed. Both failures are
  `tests/integration/test_runtime_services.py` (health and token checks against a running
  FastAPI); no API process was running (`httpx.ConnectError`), and that file is unchanged
  by R2. 27 + 19 + 2 = 48, the collected count.
- e2e: only `--collect-only` (3 collected); the browser stack was not run.
- `ponytail-review` over the diff: one finding (duplicated `TRUNCATE` in the integration
  conftest), fixed.

## Limitations

- e2e browser tests were collected but not run; `tests/e2e/odoo_fixture_api.py` now imports
  `tests.helpers.odoo_fakes` and the root conftest imports the backend app and the Reflex
  state at session start, also in e2e sessions.
- Live Odoo checks (`RUN_ODOO_HISTORY_LIVE`, `RUN_T6_LIVE_CONTRACTS`,
  `RUN_T7S_LIVE_CONTRACTS`) were not run (R1 recorded HTTP 401 for the history key).
- `podman compose` on this machine resolves to Docker's compose provider with a missing
  pipe; the disposable test database was started with an equivalent `podman run` of
  `infra/persistence/compose.test.yaml`'s image, user, database and port.
- Hosted CI not run; local success only.

## Drive follow-ups (not done; Drive changes need an owner request)

- 06_REQUIREMENTS_BASELINE AC-V2 evidence links and 07_DEVELOPMENT_STATUS cite test files
  by their old names (for example `test_t13_planning.py`, `test_t15_planning_api.py`,
  `test_t16_scenarios.py`, `test_t17_decisions.py`, `test_t17_demo.py`,
  `test_t21_documents.py`, `test_p3_frontend.py`, `test_p4_validation.py`). Update them with
  the old → new map above. Not verified against the live Drive text in this session.

## Thesis chapter relevance

Chapter 7 (testing and validation): the suite is now described by capability — MILP model
and solver runtime, ML on Odoo history and the risk bridge, planning/scenario/decision API,
approved documents, frontend state, architecture boundaries — with one fixture layer
(`conftest.py`) and one helper layer (`tests/helpers/`). `docs/TESTING.md` "Where tests
live" is the map to cite.
