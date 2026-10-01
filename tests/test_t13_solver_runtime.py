"""Required solver gate: dependencies/executable failures must fail CI, never skip."""

import sys
import time

import pulp
import pytest

from decision_core.planning.models import PlanningStatus
from optimization_adapter.pulp_cbc import PulpCbcSolver
from tests.test_t13_planning import request


def test_required_pulp_and_actual_cbc_runtime():
    assert sys.version_info >= (3, 11)
    info = PulpCbcSolver().runtime_info()
    assert info["pulp"] == "3.3.0" and info["cbc"] == "2.10.3"
    result = PulpCbcSolver().minimum_cost(request(), time.monotonic() + 10)
    assert result.status is PlanningStatus.OPTIMAL
    assert tuple(a.quantity for a in result.allocations) == (6, 4, 0)


def test_absent_executable_is_solver_failure(monkeypatch):
    adapter = PulpCbcSolver()
    solver = pulp.PULP_CBC_CMD(msg=False)
    monkeypatch.setattr(solver, "available", lambda: False)
    monkeypatch.setattr(adapter, "_solver", lambda remaining: solver)
    assert (
        adapter.minimum_cost(request(), time.monotonic() + 10).status is PlanningStatus.SOLVER_ERROR
    )


def test_expired_total_budget_does_not_return_incumbent():
    outcome = PulpCbcSolver().minimum_cost(request(), time.monotonic() - 1)
    assert outcome.status is PlanningStatus.NO_PROVEN_OPTIMUM and outcome.allocations == ()


def test_cbc_incumbent_status_is_not_a_proven_optimum(monkeypatch):
    adapter = PulpCbcSolver()
    model = adapter._model(request())

    def incumbent(solver):
        model.problem.status = pulp.LpStatusOptimal
        model.problem.sol_status = pulp.LpSolutionIntegerFeasible

    monkeypatch.setattr(model.problem, "solve", incumbent)
    assert (
        adapter._run(model, time.monotonic() + 10, initial=True) is PlanningStatus.NO_PROVEN_OPTIMUM
    )


def test_nonintegral_or_constraint_corrupted_primal_is_rejected():
    adapter = PulpCbcSolver()
    model = adapter._model(request())
    for var in model.problem.variables():
        var.varValue = 0
    model.quantities[0].varValue = 1.5
    with pytest.raises(ValueError, match="noninteger"):
        adapter._integer_values(model.problem)
    model.quantities[0].varValue = 1
    with pytest.raises(ValueError, match="constraint"):
        adapter._integer_values(model.problem)
