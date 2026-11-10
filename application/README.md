# application

Framework-independent use cases: everything the buyer can do, expressed over ports.
It assembles inputs with field-level provenance, calls the ML and planning core, and
stores immutable cases, scenarios, decisions and documents through repository ports.

## Entry points

| Module | Use case |
| --- | --- |
| [planning_history.py](planning_history.py) | Capture Odoo purchase history; preview suggested buyer terms |
| [odoo_planning_input.py](odoo_planning_input.py), [planning_input.py](planning_input.py), [provenance.py](provenance.py) | Assemble planning facts with Odoo vs. buyer sources |
| [procurement_planning.py](procurement_planning.py) | Planning entry point and the ML → MILP risk bridge (`risk_inputs`) |
| [planning_cases.py](planning_cases.py) | Create base cases and scenarios; stored-only replay |
| [planning_decisions.py](planning_decisions.py) | Approve one plan or record No-award, once |
| [planning_documents.py](planning_documents.py) | Store and serve approved PDFs per language and kind |
| [planning_library.py](planning_library.py) | Bounded saved-case listing |
| [supplier_overview.py](supplier_overview.py) | Per-supplier overview and its HU/EN labels and tree-path sentences |
| [errors.py](errors.py), [stored_contracts.py](stored_contracts.py), [planning_serialization.py](planning_serialization.py) | Error contracts, stored contract ids, exact JSON snapshots |
| [odoo_quotations.py](odoo_quotations.py), [purchase_history.py](purchase_history.py) | ERP-neutral facts the Odoo readers return |

Stored contract ids (for example `t15-controlled-planning-v1`) are persisted in the
database and are never renamed.

## Imports

- May import: `decision_core`, `supplier_evaluation`.
- Must not import: `odoo_adapter`, `persistence`, `backend`, `tools`, SQLAlchemy,
  psycopg, Alembic. Adapters implement its ports and are wired in `backend/app/dependencies.py`.
  Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/test_odoo_purchase_history.py`, `tests/test_scenario_api.py`,
`tests/test_decision_api.py`, `tests/test_approved_documents.py`,
`tests/test_planning_library.py`, `tests/test_supplier_overview.py`; see
[docs/TESTING.md](../docs/TESTING.md).
