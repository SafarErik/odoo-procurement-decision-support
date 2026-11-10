# backend

The FastAPI HTTP API and the composition root that wires adapters into the use cases.
Routes stay thin: they validate the request, check the service token and call
`application/`. Every data route needs the Bearer service token; only
`GET /api/v1/health` is open.

## Entry points

- [app/main.py](app/main.py) — the FastAPI app and the health route.
- [app/dependencies.py](app/dependencies.py) — composition root: Odoo readers, PostgreSQL
  repositories, the CBC solver and the trusted supplier model.
- [app/routes/planning_cases.py](app/routes/planning_cases.py) — planning cases,
  scenarios, supplier overview, final decision, approved PDFs.
- [app/routes/quotation_groups.py](app/routes/quotation_groups.py) — open Odoo quotation groups.
- [app/planning_case_schemas.py](app/planning_case_schemas.py), [app/schemas.py](app/schemas.py),
  [app/api_common.py](app/api_common.py) — strict request and response schemas, the
  trusted-caller gate.
- [app/config.py](app/config.py) — settings from the ignored `.env`.

Route table: [docs/ARCHITECTURE.md §4](../docs/ARCHITECTURE.md#4-http-api). Running it:
[docs/RUNBOOK.md §4](../docs/RUNBOOK.md#4-planning-database-api-and-ui).

## Imports

- May import: every runtime package except `frontend` and `tools`.
- Routes must not import `odoo_adapter` or the planner directly; only
  `dependencies.py`, `config.py` and `planning_case_schemas.py` touch `supplier_evaluation`.
  Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/test_health.py`, `tests/test_scenario_api.py`, `tests/test_decision_api.py`,
`tests/test_full_http_flow.py`; with PostgreSQL in `tests/integration/`. See
[docs/TESTING.md](../docs/TESTING.md).
