# Testing

Markers (`pyproject.toml`): unmarked tests are **fast** and need only Python;
`integration` needs a running service (PostgreSQL test database or Odoo); `e2e`
drives a real browser against Reflex + FastAPI + PostgreSQL. Unknown markers fail.

| Command | What it proves |
| --- | --- |
| `python -m tools.dev check` | Format, lint, compile, all fast tests, dependency consistency |
| `pytest -m "integration and not e2e"` | Real PostgreSQL migrations, immutability triggers, idempotency races, live Odoo contracts (opt-in) |
| `pytest -m e2e` | Browser flows; **not collected since P2** (they start from the removed synthetic demo); P3 rebuilds them on the Odoo-history flow |

CI: `.github/workflows/quality.yml` (required) runs the fast gate on Python 3.11;
`integration.yml` (path-filtered, optional) runs the container/API tests with
Docker Compose on Ubuntu.

## What the fast suite covers

| Area | Main test files |
| --- | --- |
| MILP model: bounds, optimum vs. brute-force reference, alternatives, tie-break, infeasible / time-limit / solver-error states | `test_t13_planning.py`, `test_t13_solver_runtime.py` |
| ML on Odoo purchase history: export policy, adapter, as-of features, next-window label, supplier/time split, depth selection, baselines, artifact, inference, readable path, seeding guards, full case lifecycle, strict terms, supplier overview, PDF v2 names | `test_odoo_purchase_history.py`, `test_supplier_overview.py` |
| Pre-P2 synthetic V1 tree (offline library; rebuilds stored demo cases via `tests/legacy_cases.py`) | `test_t14_dataset.py`, `test_t14_model.py`, `test_t14_runtime.py` |
| ML → MILP risk bridge and score validity | `test_t14_planning_bridge.py` |
| Historical KPI (delivery schedule adherence) and the bounded Odoo projection | `test_historical_performance.py`, `test_t7s_projection_policy.py`, `test_odoo_historical_performance_adapter.py` |
| Odoo readers (RFQs, open quotation groups, comparison groups, purchase history) with mocked transport | `test_odoo_adapter.py`, `test_quotation_groups.py`, `test_odoo_comparison_case_adapter.py`, `test_odoo_purchase_history.py` |
| Planning API: Odoo-history creation, fail-closed terms, idempotent replay, stored-only GET of new and pre-P2 cases | `test_odoo_purchase_history.py`, `test_t15_planning_api.py` |
| Stress scenarios against the original base, both directions | `test_t15_planning_api.py`, `test_t16_scenarios.py`, `test_scenario_baseline.py` |
| Human decision, No-award, conflicts, approved PDF v2 (HU/EN, per-language storage, pre-P2 English artifact) | `test_t17_decisions.py`, `test_decision_confirmation.py`, `test_t21_documents.py` |
| Saved-case library | `test_planning_library.py` |
| Frontend state and HTTP clients (no browser) | `test_t16_*`, `test_creation_review.py`, `test_plan_comparison.py`, `test_workspace_navigation.py` |
| Full HTTP acceptance flow on Odoo history | `test_t17_demo.py` |
| Architecture boundaries | `test_architecture.py`, `test_t13_architecture.py`, `test_t14_architecture.py` |

Test file names still carry historical increment numbers; they are renamed by
capability when they are next changed.

## ML evaluation conventions kept

Temporal train/test split with a gap so label windows never cross the boundary,
disjoint suppliers between train and test, preprocessing fitted on train only,
fixed seed, metrics reported per class with support, majority-class and single-rule
baselines. See [MODEL_ML.md](MODEL_ML.md).
