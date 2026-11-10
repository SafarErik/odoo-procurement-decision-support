# optimization_adapter

The replaceable MILP solver: PuLP + CBC implementation of the `AllocationSolver` port
defined in [decision_core/planning/planner.py](../decision_core/planning/planner.py).

## Entry points

- [pulp_cbc.py](pulp_cbc.py) — `PulpCbcSolver` and `CbcConfiguration`. The module
  docstring states the formulation (variables, constraints, objectives per phase),
  the integer encoding with exact rational scaling and the deterministic tie-break.
  The prose version is [docs/MODEL_MILP.md](../docs/MODEL_MILP.md).

## Imports

- May import: `decision_core`, PuLP.
- Must not import: `application`, `backend`, `odoo_adapter`, `persistence`,
  scikit-learn, `tools`, Reflex, httpx. It is never an ERP or application client.
  Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

CBC really runs in the fast gate: `tests/test_milp_planning.py` (optimum vs. an
exhaustive reference), `tests/test_solver_runtime.py`, `tests/test_balanced_alternative.py`,
`tests/test_validation_tools.py`; see [docs/TESTING.md](../docs/TESTING.md).
