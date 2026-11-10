# decision_core

The ERP-neutral planning core: what a one-product procurement request and its plans
are, which business rules a plan must satisfy, and the order of the planning stages.
It knows nothing about Odoo, HTTP, databases, ML or where a value came from.

## Entry points

- [planning/models.py](planning/models.py) — immutable request, supplier terms, policy, plan
  and result types; one product, unit and currency per request.
- [planning/planner.py](planning/planner.py) — `plan_procurement`: minimum cost, then the
  cost–risk and balanced alternatives, through the `AllocationSolver` port.
- [planning/rules.py](planning/rules.py) — exact feasibility bounds and plan verification,
  without solver imports.

The model itself is explained in [docs/MODEL_MILP.md](../docs/MODEL_MILP.md); the solver
that implements the port is [optimization_adapter/](../optimization_adapter/README.md).

## Imports

- May import: the standard library only.
- Must not import: `application`, adapters, `backend`, `frontend`, `tools`, PuLP,
  scikit-learn, httpx, Reflex, SQLAlchemy; no provenance fields (`source_type`,
  `source_reference`). Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/test_milp_planning.py`, `tests/test_balanced_alternative.py`,
`tests/test_solver_runtime.py`; full map in [docs/TESTING.md](../docs/TESTING.md).
