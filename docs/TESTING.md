# Testing

Markers (`pyproject.toml`): unmarked tests are **fast** and need only Python;
`integration` needs a running service (PostgreSQL test database or Odoo); `e2e`
drives a real browser against Reflex + FastAPI + PostgreSQL. Unknown markers fail.

| Command | What it proves |
| --- | --- |
| `python -m tools.dev check` | Format, lint, compile, all fast tests, dependency consistency |
| `pytest -m "integration and not e2e"` | Real PostgreSQL migrations, immutability triggers, idempotency races, live Odoo contracts (opt-in) |
| `pytest -m e2e --browser chromium` | Browser flows on the Odoo-history path: real FastAPI, PostgreSQL (disposable Compose project) and Reflex; Odoo and the supplier model come from the fast-test fakes (`tests/e2e/odoo_fixture_api.py` over `tests/helpers/odoo_fakes.py`), so no live Odoo is needed. Needs Podman and `pip install -e ".[e2e]"` plus `playwright install chromium` |

CI: `.github/workflows/quality.yml` (required) runs `python -m tools.dev check` on Python 3.11
plus whitespace and Compose-configuration checks;
`integration.yml` (path-filtered, optional) starts an empty Odoo and the test PostgreSQL with
Docker Compose on Ubuntu, starts FastAPI, runs `pytest -m "integration and not e2e"` (tests
that need seeded history skip), compiles the frontend and checks named-volume persistence.
No CI job runs the live Odoo-history path, the browser flow or the P4 tools below; those are
local evidence, recorded per run with branch, commit and dirty flag.

## Where tests live

| Path | Contents |
| --- | --- |
| `tests/test_*.py` | Fast tests (unmarked), one module per capability; each module's docstring names it |
| `tests/integration/` | `integration` marker: disposable PostgreSQL (`TEST_DATABASE_URL`) and opt-in live Odoo checks |
| `tests/e2e/` | `integration` + `e2e` markers: browser harness (`conftest.py`) and the fixture API it starts (`odoo_fixture_api.py`) |
| `tests/conftest.py` | Shared fixtures: `odoo_history` (fixed `REFERENCE_NOW`, exact values), `history` (current hour, real clock), `fake_odoo`, `frontend_api` (token + transport for `frontend/api/`), `stored_cases`, `decision_api`, `scenario_state`, `prepared_state` |
| `tests/integration/conftest.py` | `postgres_runtime` (migrated test database), `postgres_history_api`, `postgres_decision_api` |
| `tests/helpers/` | Non-fixture code: `odoo_fakes` (fake read-only Odoo, generated history, trained tree), `planning_api` (token, headers, case creation, decision intents), `in_memory_uow` (transactional in-memory store), `milp_requests` (small requests, exhaustive reference optimum), `frontend_patching` (`patch_client`, `use_transport`, `consume`, `event`), `browser` |

Test modules import shared code only from `tests.helpers`, never from another test module.
Frontend state tests either replace one API function with
`tests.helpers.frontend_patching.patch_client` (it patches `frontend/api/<resource>.py`,
where the state mixins resolve it) or keep the real client and route its requests with
`use_transport` (an `httpx.ASGITransport` over the FastAPI app or an `httpx.MockTransport`).

## What the fast suite covers

| Area | Main test files |
| --- | --- |
| MILP model: bounds, optimum vs. brute-force reference, alternatives, tie-break, infeasible / time-limit / solver-error states | `test_milp_planning.py`, `test_solver_runtime.py`, `test_balanced_alternative.py` |
| ML on Odoo purchase history: export policy, adapter, as-of features, next-window label, supplier/time split, depth selection, baselines, artifact, inference, readable path, seeding guards, full case lifecycle, strict terms, supplier overview, PDF v2 names | `test_odoo_purchase_history.py`, `test_supplier_overview.py` |
| ML → MILP risk bridge and score validity | `test_risk_bridge.py` |
| Odoo addon's bounded inventory projection policy (still deployed, unused by the runtime) | `test_odoo_inventory_projection_policy.py` |
| Odoo readers (open quotation groups, comparison groups, purchase history) with mocked transport | `test_quotation_groups.py`, `test_odoo_comparison_case_adapter.py`, `test_odoo_purchase_history.py` |
| Planning API: Odoo-history creation, fail-closed terms, idempotent replay, stored-only GET | `test_odoo_purchase_history.py`, `test_scenario_api.py` |
| Stress scenarios against the original base, both directions | `test_scenario_api.py`, `test_frontend_scenarios.py`, `test_scenario_baseline.py` |
| Human decision, No-award, conflicts, approved plan and audit PDF v3 (HU/EN, per-language and per-kind storage; stored v1/v2 artifacts fail closed) | `test_decision_api.py`, `test_decision_confirmation.py`, `test_approved_documents.py` |
| Saved-case library | `test_planning_library.py` |
| Frontend state and HTTP clients (no browser) | `test_frontend_stored_case.py`, `test_frontend_scenarios.py`, `test_frontend_explanations.py`, `test_frontend_decision.py`, `test_saved_result_presentation.py`, `test_supplier_evidence.py`, `test_creation_review.py`, `test_plan_comparison.py`, `test_workspace_navigation.py` |
| UI language and formatting: Hungarian default, HU/EN texts, locale money/date/number, relabel on switch without HTTP, supplier cards and KPI chart data | `test_frontend_presentation.py` |
| Guided preparation: draft preservation, field validation, group-change guard, bounded home requests, explicit chart selection | `test_guided_workspace.py`, `test_creation_review.py` |
| Browser: quotation → demand → terms → review → saved case → approval → HU/EN PDF; step/language preservation; 375 px scenario and error states; home and case views at 1440/1280/768/390 px, confirmation cancellation and No-award reopening without PDF | `tests/e2e/test_odoo_flow_browser.py`, `test_cases_scenarios_mobile_browser.py`, `test_guided_workspace_browser.py` |
| Full HTTP acceptance flow on Odoo history (HU and EN PDF) | `test_full_http_flow.py` |
| P4 validation tools: evaluation-group seeding guards, exhaustive reference optimum and invariants (K, ties, infeasible variants), nearest-rank p95, latency workload, one-command demo with isolated replay | `test_validation_tools.py` |
| Architecture boundaries, including the solver and ML runtimes being required in the fast gate | `test_architecture.py` |

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
