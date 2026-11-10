# tools

Developer and evaluation command-line tools. Runtime code never imports this package.
Each module documents itself in its docstring and `--help`; the command list is the
docstring of [dev.py](dev.py) (`python -m tools.dev --help`).

| Module | Purpose |
| --- | --- |
| [dev.py](dev.py) | One entry point: `check` (the fast gate CI runs), `db-up`/`db-down`, `api`, `ui`, `odoo-up`/`odoo-down`, `demo` |
| [seed_odoo_history.py](seed_odoo_history.py) | Writes generated purchase history into the dedicated Odoo test database only; refuses any other |
| [train_history_model.py](train_history_model.py) | Offline extraction, training and report of the supplier model |
| [http_flow.py](http_flow.py) | Full HTTP acceptance flow against a running API |
| [demo.py](demo.py) | One-command demonstration with replay without Odoo and model |
| [milp_evaluation.py](milp_evaluation.py) | MILP/API latency and correctness evaluation |
| [ui_screenshots.py](ui_screenshots.py) | UI evidence screenshots from a running dev stack |

When to run which and with what settings: [docs/RUNBOOK.md](../docs/RUNBOOK.md).
Evidence the tools write: [docs/evidence/](../docs/evidence/).

## Imports

May import any project package; must never be imported by `application`, `backend`,
`odoo_adapter`, `supplier_evaluation` or `frontend`
([tests/test_architecture.py](../tests/test_architecture.py)).

## Tests

`tests/test_validation_tools.py` (seeding guards, evaluation, demo replay),
`tests/test_full_http_flow.py`; see [docs/TESTING.md](../docs/TESTING.md).
