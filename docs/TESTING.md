# Testing

Markers (`pyproject.toml`): unmarked tests are **fast** and need only Python;
`integration` needs a running service (PostgreSQL test database or Odoo); `e2e`
drives a real browser against Reflex + FastAPI + PostgreSQL. Unknown markers fail.

| Command | What it proves |
| --- | --- |
| `python -m tools.dev check` | Format, lint, compile, all fast tests, dependency consistency |
| `pytest -m "integration and not e2e"` | Real PostgreSQL migrations, immutability triggers, idempotency races, live Odoo contracts (opt-in) |
| `pytest -m e2e --browser chromium` | Browser flows on the Odoo-history path: real FastAPI, PostgreSQL (disposable Compose project) and Reflex; Odoo and the supplier model come from the P1 fixtures (`tests/e2e/odoo_fixture_api.py`), so no live Odoo is needed. Needs Podman and `pip install -e ".[e2e]"` plus `playwright install chromium` |

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
| UI language and formatting: Hungarian default, HU/EN texts, locale money/date/number, relabel on switch without HTTP, supplier cards and KPI chart data | `test_p3_frontend.py` |
| Browser: open RFQ → case → tabs → approval → Hungarian PDF → English switch; 375 px case list, scenario chart, empty and error states | `tests/e2e/test_odoo_flow_browser.py`, `tests/e2e/test_cases_scenarios_mobile_browser.py` |
| Full HTTP acceptance flow on Odoo history (HU and EN PDF) | `test_t17_demo.py` |
| P4 validation tools: evaluation-group seeding guards, exhaustive reference optimum and invariants (K, ties, infeasible variants), nearest-rank p95, latency workload, one-command demo with isolated replay | `test_p4_validation.py` |
| Architecture boundaries | `test_architecture.py`, `test_t13_architecture.py`, `test_t14_architecture.py` |

Test file names still carry historical increment numbers; they are renamed by
capability when they are next changed. Frontend state tests patch HTTP clients with
`tests/frontend_patching.patch_client`, which targets the feature module that resolves
each name (`state_base`, `state_case`, `state_decision`, `state_creation`, …).

## Validation runs with live services (P4)

Not part of any pytest marker; they need the stack of [RUNBOOK.md](RUNBOOK.md) §5.4 and
write machine-readable evidence to `docs/evidence/`:

| Command | Evidence |
| --- | --- |
| `python -m tools.dev demo` | `P4_DEMO_REPORT.json`: full flow on live Odoo, replay without Odoo and model |
| `python -m tools.milp_evaluation` | `P4_MILP_EVALUATION.json`: latency (median, nearest-rank p95, max) for 4/5/10 suppliers × 1/3 ε and solver correctness vs. an exhaustive reference |
| `python -m tools.train_history_model report` | `P4_ML_REPORT_CHECK.json`: saved model re-evaluated, compared with the P1 report |

## ML evaluation conventions kept

Temporal train/test split with a gap so label windows never cross the boundary,
disjoint suppliers between train and test, preprocessing fitted on train only,
fixed seed, metrics reported per class with support, majority-class and single-rule
baselines. See [MODEL_ML.md](MODEL_ML.md).
