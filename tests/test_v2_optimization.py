"""Manual references and small exhaustive oracles for the optional V2 spike."""

import itertools
import random
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

pytest.importorskip("pulp", reason="Optional V2 spike: install .[optimization-spike]")

from tools.v2_optimization.experiments import baseline  # noqa: E402
from tools.v2_optimization.models import (  # noqa: E402
    PriceTier,
    ProcurementOptimizationInput,
    Status,
    Supplier,
)
from tools.v2_optimization.solver import optimize  # noqa: E402


def supplier(identity: str, price: str, capacity: int, **kwargs) -> Supplier:
    return Supplier(identity, Decimal(price), capacity, **kwargs)


def assert_plan(data, expected, cost, **kwargs):
    result = optimize(data, **kwargs)
    assert result.status is Status.OPTIMAL, result
    assert result.plan is not None
    assert dict(result.plan.allocations) == expected
    assert result.plan.total_cost == Decimal(cost)
    assert result.plan.total_quantity == data.required_quantity
    assert result.plan.selected_supplier_count == sum(x > 0 for x in expected.values())
    return result.plan


def test_a_basic_split_allocation():
    data = ProcurementOptimizationInput(10, (supplier("A", "2", 6), supplier("B", "3", 8)), 2)
    assert_plan(data, {"A": 6, "B": 4}, "24")


def test_b_cheapest_capacity_insufficient():
    data = ProcurementOptimizationInput(10, (supplier("A", "1", 3), supplier("B", "2", 10)), 2)
    plan = assert_plan(data, {"A": 3, "B": 7}, "17")
    assert ("A", "capacity_binding") in {(e.supplier_id, e.code) for e in plan.explanations}


def test_c_deadline_excludes_cheapest():
    data = ProcurementOptimizationInput(
        10, (supplier("A", "1", 10, deadline_eligible=False), supplier("B", "2", 10)), 2
    )
    plan = assert_plan(data, {"A": 0, "B": 10}, "20")
    assert "deadline_ineligible" in {e.code for e in plan.explanations}


def test_d_concentration_forces_multisourcing():
    data = ProcurementOptimizationInput(
        10, (supplier("A", "1", 10), supplier("B", "2", 10)), 2, Decimal("0.6")
    )
    plan = assert_plan(data, {"A": 6, "B": 4}, "14")
    assert "concentration_binding" in {e.code for e in plan.explanations}
    assert plan.concentration == Decimal("0.6")


def test_e_moq_changes_solution():
    data = ProcurementOptimizationInput(10, (supplier("A", "1", 8), supplier("B", "2", 10)), 2)
    assert_plan(data, {"A": 8, "B": 2}, "12")
    constrained = replace(
        data, suppliers=(data.suppliers[0], replace(data.suppliers[1], minimum_quantity=5))
    )
    plan = assert_plan(constrained, {"A": 5, "B": 5}, "15")
    assert "moq_binding" in {e.code for e in plan.explanations}


def test_f_supplier_outage():
    data = baseline()
    assert_plan(data, {"A": 60, "B": 40, "C": 0}, "1020")
    assert_plan(
        replace(data, suppliers=(replace(data.suppliers[0], available=False), *data.suppliers[1:])),
        {"A": 0, "B": 80, "C": 20},
        "1060",
    )


def test_g_demand_increase_and_capacity_reduction():
    data = baseline()
    assert_plan(replace(data, required_quantity=120), {"A": 60, "B": 60, "C": 0}, "1230")
    assert_plan(
        replace(data, suppliers=(replace(data.suppliers[0], capacity=30), *data.suppliers[1:])),
        {"A": 30, "B": 70, "C": 0},
        "1035",
    )


@pytest.mark.parametrize(
    "epsilon,allocation,cost,risk",
    [
        ("0.00", {"A": 60, "B": 40, "C": 0}, "1020", "0.26"),
        ("0.02", {"A": 20, "B": 80, "C": 0}, "1040", "0.12"),
        ("0.05", {"A": 0, "B": 58, "C": 42}, "1071", "0.0332"),
        ("0.10", {"A": 0, "B": 20, "C": 80}, "1090", "0.018"),
    ],
)
def test_h_risk_epsilon_reference(epsilon, allocation, cost, risk):
    plan = assert_plan(baseline(), allocation, cost, epsilon=Decimal(epsilon))
    assert plan.risk_proxy == Decimal(risk)
    assert plan.total_cost <= Decimal("1020") * (1 + Decimal(epsilon))


def test_i_explicit_infeasible_cases():
    result = optimize(replace(baseline(), required_quantity=300))
    assert result.status is Status.INFEASIBLE
    assert result.plan is None
    assert "insufficient_effective_capacity" in {reason.code for reason in result.reasons}
    data = ProcurementOptimizationInput(10, (supplier("A", "1", 6), supplier("B", "2", 6)), 1)
    assert "supplier_count_capacity_shortfall" in {e.code for e in optimize(data).reasons}
    # Aggregate capacity passes, but each selected supplier must buy six units.
    data = replace(
        data,
        max_suppliers=2,
        suppliers=tuple(replace(s, minimum_quantity=6) for s in data.suppliers),
    )
    result = optimize(data)
    assert result.status is Status.INFEASIBLE and result.plan is None
    assert "no minimal conflict set" in result.reasons[-1].detail


@pytest.mark.parametrize(
    "demand,allocation,cost",
    [
        (499, {"A": 0, "B": 499}, "474050"),
        (500, {"A": 500, "B": 0}, "460000"),
        (600, {"A": 600, "B": 0}, "552000"),
    ],
)
def test_j_all_units_price_tier(demand, allocation, cost):
    a = supplier(
        "A",
        "1000",
        1000,
        price_tiers=(PriceTier(1, Decimal("1000")), PriceTier(500, Decimal("920"))),
    )
    assert_plan(
        ProcurementOptimizationInput(demand, (a, supplier("B", "950", 1000)), 1), allocation, cost
    )


def test_price_increase_changes_allocation():
    data = baseline()
    assert_plan(
        replace(
            data,
            suppliers=(replace(data.suppliers[0], unit_cost=Decimal("11.5")), *data.suppliers[1:]),
        ),
        {"A": 0, "B": 80, "C": 20},
        "1060",
    )


def test_equal_cost_ties_are_canonical_under_input_reordering():
    data = ProcurementOptimizationInput(5, (supplier("B", "1", 5), supplier("A", "1", 5)), 2)
    first = assert_plan(data, {"A": 5, "B": 0}, "5")
    for _ in range(3):
        assert optimize(replace(data, suppliers=tuple(reversed(data.suppliers)))).plan == first


def test_equal_risk_secondary_cost_removes_dominated_plans():
    data = ProcurementOptimizationInput(
        5,
        tuple(
            supplier(i, c, 5, historical_adherence=Decimal("0.8"), sample_size=3)
            for i, c in (("A", "10"), ("B", "11"))
        ),
        2,
    )
    assert_plan(data, {"A": 5, "B": 0}, "50", epsilon=Decimal("0.1"))


def test_zero_risk_and_unreachable_tiers():
    a = supplier(
        "A",
        "10",
        10,
        historical_adherence=Decimal("1"),
        sample_size=3,
        price_tiers=(PriceTier(1, Decimal("10")), PriceTier(20, Decimal("9"))),
    )
    b = supplier("B", "11", 10, historical_adherence=Decimal("1"), sample_size=3)
    plan = assert_plan(
        ProcurementOptimizationInput(5, (a, b), 2), {"A": 5, "B": 0}, "50", epsilon=Decimal("0.1")
    )
    assert plan.risk_proxy == Decimal("0")


def test_missing_or_withheld_history_is_not_fabricated():
    data = baseline()
    for changes in ({"historical_adherence": None}, {"sample_size": 2}):
        incomplete = replace(
            data, suppliers=(replace(data.suppliers[0], **changes), *data.suppliers[1:])
        )
        assert optimize(incomplete).plan.risk_proxy is None
        result = optimize(incomplete, epsilon=Decimal("0.1"))
        assert result.status is Status.HISTORY_UNAVAILABLE and result.plan is None
        excluded = replace(
            incomplete,
            suppliers=(
                replace(incomplete.suppliers[0], deadline_eligible=False),
                *data.suppliers[1:],
            ),
        )
        assert optimize(excluded, epsilon=Decimal("0.1")).status is Status.OPTIMAL


def test_fractional_concentration_and_cost_cap_are_floored_exactly():
    data = ProcurementOptimizationInput(
        7, (supplier("A", "1", 7), supplier("B", "2", 7)), 2, Decimal("0.5")
    )
    assert optimize(data).status is Status.INFEASIBLE  # each floor is 3, total 6
    data = replace(data, required_quantity=5, concentration_limit=Decimal("0.6"))
    assert_plan(data, {"A": 3, "B": 2}, "7")
    data = ProcurementOptimizationInput(
        3,
        (
            supplier("A", "0.01", 3, historical_adherence=Decimal("0"), sample_size=3),
            supplier("B", "0.02", 3, historical_adherence=Decimal("1"), sample_size=3),
        ),
        2,
    )
    assert_plan(data, {"A": 3, "B": 0}, "0.03", epsilon=Decimal("0.1"))


@pytest.mark.parametrize(
    "change",
    [
        {"required_quantity": 0},
        {"required_quantity": True},
        {"max_suppliers": 0},
        {"concentration_limit": Decimal("NaN")},
        {"concentration_limit": Decimal("1.1")},
        {"concentration_limit": Decimal("0")},
    ],
)
def test_invalid_requirements_fail_before_solving(change):
    with pytest.raises(ValueError):
        replace(baseline(), **change)


@pytest.mark.parametrize(
    "change",
    [
        {"unit_cost": Decimal("0")},
        {"unit_cost": Decimal("1.001")},
        {"unit_cost": Decimal("Infinity")},
        {"capacity": -1},
        {"capacity": True},
        {"historical_adherence": Decimal("1.1")},
        {"sample_size": -1},
        {"available": "false"},
        {"supplier_id": ""},
        {"price_tiers": (PriceTier(2, Decimal("10")),)},
    ],
)
def test_invalid_supplier_values_fail_before_solving(change):
    with pytest.raises(ValueError):
        replace(baseline().suppliers[0], **change)


def test_duplicate_supplier_and_invalid_epsilon():
    with pytest.raises(ValueError):
        replace(baseline(), suppliers=(baseline().suppliers[0],) * 2)
    with pytest.raises(ValueError):
        optimize(baseline(), epsilon=Decimal("-0.01"))


def test_precision_validation_and_money_do_not_depend_on_decimal_context():
    with pytest.raises(ValueError):
        replace(baseline().suppliers[0], unit_cost=Decimal("1.00000000000000000000000000000001"))
    data = baseline()
    expected = optimize(data, epsilon=Decimal("0.05"))
    with localcontext() as context:
        context.prec = 2
        assert optimize(data, epsilon=Decimal("0.05")) == expected


def test_solver_incumbent_or_error_is_not_claimed_optimal(monkeypatch):
    import pulp

    from tools.v2_optimization import solver

    def incumbent(problem, _solver):
        problem.status = pulp.LpStatusOptimal
        problem.sol_status = pulp.LpSolutionIntegerFeasible

    monkeypatch.setattr(pulp.LpProblem, "solve", incumbent)
    result = solver.optimize(baseline())
    assert result.status is Status.NO_SOLUTION and result.plan is None

    def failed(problem, _solver):
        raise pulp.PulpSolverError("synthetic unavailable solver")

    monkeypatch.setattr(pulp.LpProblem, "solve", failed)
    result = solver.optimize(baseline())
    assert result.status is Status.SOLVER_ERROR and result.plan is None


def test_small_cases_match_exhaustive_independent_oracle():
    rng = random.Random(19)
    for _ in range(12):
        suppliers = tuple(
            supplier(
                identity,
                str(rng.randint(1, 5)),
                rng.randint(2, 6),
                minimum_quantity=rng.randint(0, 3),
                historical_adherence=Decimal(rng.randint(0, 10)) / 10,
                sample_size=5,
            )
            for identity in ("A", "B", "C")
        )
        data = ProcurementOptimizationInput(
            rng.randint(3, 8), suppliers, rng.randint(1, 3), Decimal("0.75")
        )
        feasible = []
        for xs in itertools.product(*(range(s.capacity + 1) for s in suppliers)):
            if sum(xs) != data.required_quantity or sum(x > 0 for x in xs) > data.max_suppliers:
                continue
            if any(x and x < s.minimum_quantity for s, x in zip(suppliers, xs, strict=True)):
                continue
            if any(Decimal(x) > data.concentration_limit * data.required_quantity for x in xs):
                continue
            cost = sum(s.unit_cost * x for s, x in zip(suppliers, xs, strict=True))
            risk = sum((1 - s.historical_adherence) * x for s, x in zip(suppliers, xs, strict=True))
            feasible.append((xs, cost, risk))
        result = optimize(data)
        if not feasible:
            assert result.status is Status.INFEASIBLE and result.plan is None
            continue
        expected = min(feasible, key=lambda p: (p[1], tuple(-x for x in p[0])))
        assert tuple(x for _, x in result.plan.allocations) == expected[0]
        capped = [p for p in feasible if p[1] <= expected[1] * Decimal("1.1")]
        expected_risk = min(capped, key=lambda p: (p[2], p[1], tuple(-x for x in p[0])))
        result = optimize(data, epsilon=Decimal("0.1"))
        assert tuple(x for _, x in result.plan.allocations) == expected_risk[0]
