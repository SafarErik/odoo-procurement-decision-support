"""Balanced (min–max supplier share) alternative: exact optimum, invariants and records."""

import itertools
import random
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

from application.planning_serialization import json_value, read_request, read_result
from decision_core.planning.models import PlanningStatus
from decision_core.planning.planner import plan_procurement
from optimization_adapter.pulp_cbc import PulpCbcSolver
from tests.test_t13_planning import request, scored, supplier
from tools.milp_evaluation import check_result, reference_plans


def balanced(data, epsilon="0.2"):
    return replace(data, policy=replace(data.policy, diversification_epsilon=Decimal(epsilon)))


def l5_case(**policy):
    """The L5 shape: the cheapest plan leans 60/40 on one supplier."""
    data = request(
        quantity=200,
        suppliers=(supplier("A", "10", 120), supplier("B", "11", 120), supplier("C", "11.5", 120)),
        **policy,
    )
    return scored(data, values=("0.8", "0.2", "0.2"), epsilons=(Decimal("0.05"),))


def quantities(plan):
    return [a.quantity for a in plan.allocations]


def test_balanced_plan_halves_the_largest_dependence_without_raising_exposure():
    result = plan_procurement(balanced(l5_case()), PulpCbcSolver())
    assert result.status is PlanningStatus.OPTIMAL
    minimum = result.minimum_cost_plan
    assert quantities(minimum) == [120, 80, 0] and minimum.largest_share == Fraction(3, 5)
    run = result.runs[-1]
    assert (run.kind, run.epsilon, run.code) == (
        "diversified",
        Decimal("0.2"),
        "distinct_alternative",
    )
    plan = result.alternatives[run.plan_index - 1]
    # Min largest quantity (100), then lowest exposure among 100/100 splits, then cost.
    assert quantities(plan) == [0, 100, 100]
    assert plan.largest_share == Fraction(1, 2)
    assert plan.risk_exposure <= minimum.risk_exposure
    assert plan.total_cost <= minimum.total_cost * Decimal("1.2")


def test_risk_stages_keep_their_kind_and_the_balanced_stage_comes_last():
    result = plan_procurement(balanced(l5_case()), PulpCbcSolver())
    assert [(r.kind, r.epsilon) for r in result.runs] == [
        ("risk", Decimal("0.05")),
        ("diversified", Decimal("0.2")),
    ]


def test_tight_allowance_returns_the_cheapest_plan_as_its_own_balanced_proof():
    # With no extra cost allowed only the unique cheapest split fits; the stage proves plan 0.
    result = plan_procurement(balanced(l5_case(), "0"), PulpCbcSolver())
    assert result.runs[-1].kind == "diversified"
    assert result.runs[-1].plan_index == 0
    assert result.runs[-1].code == "duplicate_allocation"


def test_balanced_plan_matches_the_exhaustive_reference_on_random_instances():
    rng = random.Random(23)
    for _ in range(25):
        count = rng.randint(2, 4)
        suppliers = tuple(
            supplier(name, str(rng.randint(5, 15)), rng.randint(3, 12)) for name in "ABCD"[:count]
        )
        data = request(
            quantity=rng.randint(4, 14), suppliers=suppliers, max_suppliers=rng.randint(1, 3)
        )
        values = tuple(str(Decimal(rng.randint(0, 10)) / 10) for _ in suppliers)
        data = balanced(scored(data, values=values, epsilons=(Decimal("0.1"),)), "0.3")
        expected = reference_plans(data)
        result = plan_procurement(data, PulpCbcSolver())
        assert check_result(data, result, expected) == [], (data, result)


def test_snapshots_without_the_balanced_stage_keep_their_exact_json():
    plain = l5_case()
    encoded = json_value(plain)
    assert "diversification_epsilon" not in encoded["policy"]
    result = plan_procurement(plain, PulpCbcSolver())
    assert all("kind" not in run for run in json_value(result)["runs"])
    assert read_request(encoded) == plain


def test_balanced_records_round_trip():
    data = balanced(l5_case())
    encoded = json_value(data)
    assert encoded["policy"]["diversification_epsilon"] == "0.2"
    assert read_request(encoded) == data
    result = plan_procurement(data, PulpCbcSolver())
    stored = json_value(result)
    assert stored["runs"][-1]["kind"] == "diversified"
    assert read_result(stored) == result


def test_unknown_recorded_kind_is_rejected():
    stored = json_value(plan_procurement(balanced(l5_case()), PulpCbcSolver()))
    stored["runs"][-1]["kind"] = "made_up"
    try:
        read_result(stored)
    except ValueError:
        return
    raise AssertionError("an unknown alternative kind must not be read")


def test_permuted_supplier_order_gives_the_same_balanced_allocation():
    base = balanced(l5_case())
    expected = None
    for order in itertools.permutations(base.suppliers):
        result = plan_procurement(replace(base, suppliers=order), PulpCbcSolver())
        plan = result.alternatives[result.runs[-1].plan_index - 1]
        allocation = {a.supplier_id: a.quantity for a in plan.allocations}
        expected = expected or allocation
        assert allocation == expected
