# Testing

Markers (`pyproject.toml`): unmarked tests are **fast** and need only Python;
`integration` needs a running service (PostgreSQL test database or Odoo); `e2e`
drives a real browser against Reflex + FastAPI + PostgreSQL. Unknown markers fail.

| Command | What it proves |
| --- | --- |
| `python -m tools.dev check` | Format, lint, compile, all fast tests, dependency consistency |
| `pytest -m "integration and not e2e"` | Real PostgreSQL migrations, immutability triggers, idempotency races, live Odoo contracts (opt-in) |
| `pytest -m e2e` | Browser flows (create, compare, scenario, approve, PDF, recovery) |

CI: `.github/workflows/quality.yml` (required) runs the fast gate on Python 3.11;
`integration.yml` (path-filtered, optional) runs the container/API tests with
Docker Compose on Ubuntu.

## What the fast suite covers

| Area | Main test files |
| --- | --- |
| MILP model: bounds, optimum vs. brute-force reference, alternatives, tie-break, infeasible / time-limit / solver-error states | `test_t13_planning.py`, `test_t13_solver_runtime.py` |
| ML: dataset generation, label window, leakage guards, time/supplier split, training, metrics, artifact reload, tree path | `test_t14_dataset.py`, `test_t14_model.py`, `test_t14_runtime.py` |
| ML → MILP risk bridge and score validity | `test_t14_planning_bridge.py` |
| Historical KPI (delivery schedule adherence) and the bounded Odoo projection | `test_historical_performance.py`, `test_t7s_projection_policy.py`, `test_odoo_historical_performance_adapter.py` |
| Odoo readers (RFQs, comparison groups, history) with mocked transport | `test_odoo_adapter.py`, `test_odoo_comparison_case_adapter.py`, `test_odoo_history_integration.py` |
| Planning API: creation, provenance, fail-closed inputs, idempotent replay, stored-only GET | `test_t15_planning_api.py`, `test_t15_odoo_planning.py` |
| Stress scenarios against the original base | `test_t16_scenarios.py`, `test_scenario_baseline.py` |
| Human decision, No-award, conflicts, approved PDF content | `test_t17_decisions.py`, `test_decision_confirmation.py`, `test_t21_documents.py` |
| Saved-case library | `test_planning_library.py` |
| Frontend state and HTTP clients (no browser) | `test_t16_*`, `test_creation_review.py`, `test_plan_comparison.py`, `test_workspace_navigation.py` |
| Full demo flows and the evaluation harness | `test_t15_demo.py`, `test_t17_demo.py`, `test_t18_evaluation.py` |
| Architecture boundaries | `test_architecture.py`, `test_t13_architecture.py`, `test_t14_architecture.py` |

Test file names still carry historical increment numbers; they are renamed by
capability when they are next changed.

## ML evaluation conventions kept

Temporal train/test split with a gap so label windows never cross the boundary,
disjoint suppliers between train and test, preprocessing fitted on train only,
fixed seed, metrics reported per class with support. See [MODEL_ML.md](MODEL_ML.md)
(written in P1).
