"""Independent small-instance oracle and strict V2 business/status boundaries."""

from dataclasses import FrozenInstanceError, replace
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import permutations, product

import pytest

from application.procurement_planning import (
    ExternalRiskContext,
    PlanningCommand,
    create_procurement_plans,
)
from decision_core.planning.models import (
    Allocation,
    InvalidPlanningInput,
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    PlanningStatus,
    ProcurementRequirement,
    QuantityRange,
    RiskCoefficient,
    SupplierTerms,
)
from decision_core.planning.planner import SolveOutcome, plan_procurement
from optimization_adapter.pulp_cbc import CbcConfiguration, PulpCbcSolver

DAY = date(2026, 10, 21)


def supplier(identity, price, capacity, **changes):
    return replace(
        SupplierTerms(
            identity,
            "P",
            "unit",
            "EUR",
            Decimal(price),
            capacity,
            True,
            MinimumOrder(None),
            QuantityRange(1, 1000),
            QuantityRange(1, 1000),
            DAY,
        ),
        **changes,
    )


def request(
    *, quantity=10, suppliers=None, max_suppliers=2, concentration=None, epsilons=(), scores=None
):
    return PlanningRequest(
        ProcurementRequirement("P", quantity, "unit", "EUR", DAY),
        suppliers or (supplier("A", "2", 6), supplier("B", "3", 8), supplier("C", "4", 10)),
        PlanningPolicy(max_suppliers, concentration, epsilons),
        scores,
    )


def scored(data, values=("0.8", "0.2", "0"), epsilons=(Decimal("0.10"),)):
    return replace(
        data,
        policy=replace(data.policy, epsilons=epsilons),
        risk_coefficients=tuple(
            RiskCoefficient(s.supplier_id, Decimal(v), QuantityRange(1, 1000))
            for s, v in zip(data.suppliers, values, strict=True)
        ),
    )


def solve(data):
    result = plan_procurement(data, PulpCbcSolver())
    assert result.status is PlanningStatus.OPTIMAL, result
    return result


def quantities(plan):
    return tuple(a.quantity for a in plan.allocations)


def exhaustive(data, epsilon=None, reference=None):
    """Enumerate directly from input facts, without importing core bounds/solver rules."""
    suppliers = sorted(data.suppliers, key=lambda s: s.supplier_id)
    q = data.requirement.approved_quantity
    scores = {c.supplier_id: Fraction(c.value) for c in data.risk_coefficients or ()}
    candidates = []
    for amounts in product(range(q + 1), repeat=len(suppliers)):
        if sum(amounts) != q or sum(x > 0 for x in amounts) > data.policy.max_suppliers:
            continue
        valid = True
        for s, x in zip(suppliers, amounts, strict=True):
            if x and (
                not s.available
                or s.promised_date > data.requirement.required_date
                or x > s.capacity
                or x < (s.minimum_order.quantity or 1)
                or not s.price_quantities.minimum <= x <= s.price_quantities.maximum
                or not s.delivery_quantities.minimum <= x <= s.delivery_quantities.maximum
                or (
                    data.policy.concentration_limit is not None
                    and Fraction(x, q) > Fraction(data.policy.concentration_limit)
                )
            ):
                valid = False
        if not valid:
            continue
        cost = sum(Fraction(s.unit_price) * x for s, x in zip(suppliers, amounts, strict=True))
        if epsilon is not None and cost > reference * (1 + Fraction(epsilon)):
            continue
        tie = tuple(-x for x in amounts)
        risk = sum(
            scores.get(s.supplier_id, Fraction()) * x
            for s, x in zip(suppliers, amounts, strict=True)
        )
        candidates.append(((cost, tie) if epsilon is None else (risk, cost, tie), amounts))
    return min(candidates)[1] if candidates else None


def test_three_supplier_genuine_split_matches_hand_and_exhaustive_optimum():
    data = request()
    result = solve(data)
    assert quantities(result.minimum_cost_plan) == (6, 4, 0) == exhaustive(data)
    assert result.minimum_cost_plan.total_cost == Decimal("24")
    assert result.minimum_cost_plan.risk_exposure is None
    with pytest.raises(FrozenInstanceError):
        data.suppliers[0].capacity = 99
    with pytest.raises(FrozenInstanceError):
        result.minimum_cost_plan.allocations[0].quantity = 99


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"available": False}, (0, 8, 2)),
        ({"promised_date": date(2026, 10, 22)}, (0, 8, 2)),
        ({"capacity": 3}, (3, 7, 0)),
        ({"minimum_order": MinimumOrder(7)}, (0, 8, 2)),
        ({"price_quantities": QuantityRange(4, 5)}, (5, 5, 0)),
        ({"delivery_quantities": QuantityRange(4, 5)}, (5, 5, 0)),
        ({"price_quantities": QuantityRange(7, 9)}, (0, 8, 2)),
        ({"delivery_quantities": QuantityRange(7, 9)}, (0, 8, 2)),
    ],
)
def test_supplier_capacity_moq_eligibility_and_quantity_applicability(changes, expected):
    data = request()
    data = replace(data, suppliers=(replace(data.suppliers[0], **changes), *data.suppliers[1:]))
    assert quantities(solve(data).minimum_cost_plan) == expected == exhaustive(data)


@pytest.mark.parametrize(
    "count,limit,expected",
    [
        (1, None, (0, 0, 10)),
        (2, Decimal("0.6"), (6, 4, 0)),
        (3, Decimal("0.4"), (4, 4, 2)),
        (3, Decimal("0.3333"), None),
    ],
)
def test_supplier_count_and_integer_concentration(count, limit, expected):
    data = request(max_suppliers=count, concentration=limit)
    result = plan_procurement(data, PulpCbcSolver())
    assert exhaustive(data) == expected
    if expected is None:
        assert result.status is PlanningStatus.INFEASIBLE and result.minimum_cost_plan is None
    else:
        assert quantities(result.minimum_cost_plan) == expected


def test_moq_combination_is_proven_infeasible_not_capacity_shortfall():
    data = request(
        quantity=5,
        suppliers=(
            supplier("A", "1", 3, minimum_order=MinimumOrder(3)),
            supplier("B", "2", 3, minimum_order=MinimumOrder(3)),
        ),
    )
    result = plan_procurement(data, PulpCbcSolver())
    assert result.status is PlanningStatus.INFEASIBLE
    assert result.minimum_cost_plan is None and exhaustive(data) is None
    assert "interacting_constraints_infeasible" in {e.code for e in result.explanations}
    assert not {"insufficient_effective_capacity", "supplier_count_capacity_shortfall"} & {
        e.code for e in result.explanations
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"available": None},
        {"available": 1},
        {"capacity": None},
        {"capacity": True},
        {"capacity": -1},
        {"minimum_order": None},
        {"price_quantities": None},
        {"delivery_quantities": None},
        {"promised_date": None},
        {"unit_price": Decimal("NaN")},
        {"unit_price": Decimal("0")},
        {"unit_price": 2.5},
    ],
)
def test_unknown_critical_supplier_inputs_fail_closed(changes):
    with pytest.raises(InvalidPlanningInput):
        replace(supplier("A", "1", 10), **changes)


@pytest.mark.parametrize(
    "field,value", [("currency", "USD"), ("quantity_unit", "box"), ("product_id", "Q")]
)
def test_no_implicit_commercial_context_conversion(field, value):
    data = request()
    with pytest.raises(InvalidPlanningInput, match="must match"):
        replace(data, suppliers=(replace(data.suppliers[0], **{field: value}), *data.suppliers[1:]))


@pytest.mark.parametrize(
    "change",
    [
        {"approved_quantity": 0},
        {"approved_quantity": True},
        {"approved_quantity": Decimal("3")},
        {"required_date": None},
        {"currency": "eur"},
    ],
)
def test_requirement_is_explicit_and_integer(change):
    with pytest.raises(InvalidPlanningInput):
        replace(request().requirement, **change)


def test_distinct_alternatives_and_exact_small_instance_oracle():
    data = scored(request(), epsilons=(Decimal("0.50"), Decimal("0.10")))
    result = solve(data)
    assert quantities(result.minimum_cost_plan) == exhaustive(data)
    assert len(result.alternatives) == 2
    for run in result.runs:
        plan = (result.minimum_cost_plan, *result.alternatives)[run.plan_index]
        assert quantities(plan) == exhaustive(
            data, run.epsilon, Fraction(result.minimum_cost_plan.total_cost)
        )
        assert plan.cost_premium <= Fraction(run.epsilon)
    assert result.minimum_cost_plan.total_cost == Decimal("24")


def test_cumulative_ml_spike_external_score_interface_is_retained_without_training():
    data = request(
        quantity=100,
        suppliers=(supplier("A", "10", 60), supplier("B", "10.5", 80), supplier("C", "11", 100)),
        concentration=Decimal("0.8"),
    )
    data = scored(data, ("0.2921", "0.2921", "0"), (Decimal("0.02"), Decimal("0.05")))
    result = solve(data)
    assert [
        (quantities(p), p.total_cost) for p in (result.minimum_cost_plan, *result.alternatives)
    ] == [
        ((60, 40, 0), Decimal("1020")),
        ((60, 0, 40), Decimal("1040")),
        ((29, 0, 71), Decimal("1071")),
    ]
    assert result.alternatives[-1].risk_exposure == Fraction(Decimal("0.084709"))


def test_identical_alternatives_deduplicate_without_inventing_plans():
    data = scored(
        request(), ("0", "0", "0"), (Decimal("0"), Decimal("0.1"), Decimal("0.10"), Decimal("2"))
    )
    result = solve(data)
    assert result.alternatives == () and len(result.runs) == 3
    assert all(r.plan_index == 0 and r.code == "duplicate_allocation" for r in result.runs)


def test_input_order_invariance_and_equal_objective_lexicographic_ties():
    data = scored(
        request(suppliers=tuple(supplier(i, "2", 6) for i in ("A", "B", "C"))),
        ("0.5", "0.5", "0.5"),
        (Decimal("0.1"),),
    )
    reference = solve(data)
    for ordering in permutations(data.suppliers):
        result = solve(
            replace(
                data, suppliers=ordering, risk_coefficients=tuple(reversed(data.risk_coefficients))
            )
        )
        assert result == reference
    assert quantities(reference.minimum_cost_plan) == (6, 4, 0)


def test_risk_missing_and_quantity_100_only_scores_never_become_zero_or_extrapolated():
    data = scored(request())
    missing = replace(data, risk_coefficients=data.risk_coefficients[:1])
    assert plan_procurement(missing, PulpCbcSolver()).status is PlanningStatus.INVALID_INPUT
    incompatible = replace(
        data,
        risk_coefficients=tuple(
            replace(c, valid_quantities=QuantityRange(100, 100)) for c in data.risk_coefficients
        ),
    )
    result = plan_procurement(incompatible, PulpCbcSolver())
    assert result.status is PlanningStatus.INVALID_INPUT and result.minimum_cost_plan is None
    assert result.explanations[0].code == "risk_quantity_context_mismatch"
    cost_only = replace(missing, policy=replace(missing.policy, epsilons=()))
    assert solve(cost_only).minimum_cost_plan.risk_exposure is None


def test_risk_for_hard_excluded_supplier_is_not_required():
    data = scored(request())
    data = replace(
        data,
        suppliers=(*data.suppliers[:2], replace(data.suppliers[2], available=False)),
        risk_coefficients=data.risk_coefficients[:2],
    )
    assert solve(data).minimum_cost_plan.risk_exposure is not None


def test_decimal_precision_is_dynamic_and_money_ignores_ambient_rounding():
    data = request(suppliers=(supplier("A", "1.123456", 6), supplier("B", "2.345678", 10)))
    with localcontext() as context:
        context.prec = 3
        result = solve(data)
    assert result.minimum_cost_plan.total_cost == Decimal("16.123448")
    assert quantities(result.minimum_cost_plan) == (6, 4)


def test_numeric_adapter_limit_is_invalid_input_not_infeasibility():
    result = plan_procurement(request(), PulpCbcSolver(CbcConfiguration(exact_integer_budget=10)))
    assert result.status is PlanningStatus.INVALID_INPUT and result.minimum_cost_plan is None
    assert result.explanations[-1].code == "unsupported_numeric_contract"


def test_explanations_distinguish_hard_exclusion_zero_and_binding_bounds():
    data = request()
    data = replace(data, suppliers=(*data.suppliers, supplier("D", "1", 10, available=False)))
    plan = solve(data).minimum_cost_plan
    codes = {(e.supplier_id, e.code) for e in plan.explanations}
    assert ("D", "unavailable") in codes and ("D", "zero_in_optimal_plan") not in codes
    assert ("C", "zero_in_optimal_plan") in codes and ("A", "capacity_binding") in codes
    assert (None, "supplier_count_binding") in codes


class FailingSolver:
    def __init__(self, status):
        self.status = status

    def minimum_cost(self, request, deadline):
        return SolveOutcome(self.status, code="controlled_failure")


@pytest.mark.parametrize("status", [PlanningStatus.NO_PROVEN_OPTIMUM, PlanningStatus.SOLVER_ERROR])
def test_failed_or_unproven_solver_has_no_fabricated_plan(status):
    result = plan_procurement(request(), FailingSolver(status))
    assert (
        result.status is status and result.minimum_cost_plan is None and result.alternatives == ()
    )


def test_invalid_port_output_is_never_accepted_as_a_plan():
    class BrokenSolver:
        def minimum_cost(self, request, deadline):
            return SolveOutcome(
                PlanningStatus.OPTIMAL,
                (Allocation("A", 10), Allocation("B", 0), Allocation("C", 0)),
            )

    result = plan_procurement(request(), BrokenSolver())
    assert result.status is PlanningStatus.SOLVER_ERROR and result.minimum_cost_plan is None


def test_verified_minimum_survives_alternative_timeout_with_partial_status():
    class PartialSolver(PulpCbcSolver):
        def risk_alternative(self, request, reference_cost, epsilon, deadline):
            return SolveOutcome(PlanningStatus.NO_PROVEN_OPTIMUM, code="time_budget_exhausted")

    result = plan_procurement(scored(request()), PartialSolver())
    assert result.status is PlanningStatus.NO_PROVEN_OPTIMUM
    assert result.minimum_cost_plan.total_cost == Decimal("24") and result.alternatives == ()
    assert result.runs[0].plan_index is None


def test_later_infeasibility_is_solver_failure_not_business_infeasibility():
    class ContradictorySolver(PulpCbcSolver):
        def risk_alternative(self, request, reference_cost, epsilon, deadline):
            return SolveOutcome(PlanningStatus.INFEASIBLE)

    result = plan_procurement(scored(request()), ContradictorySolver())
    assert result.status is PlanningStatus.SOLVER_ERROR and result.minimum_cost_plan is not None


def test_application_requires_external_risk_context_without_concrete_adapter_coupling():
    data = scored(request())
    assert (
        create_procurement_plans(PlanningCommand(data, None), PulpCbcSolver()).status
        is PlanningStatus.INVALID_INPUT
    )
    context = ExternalRiskContext(
        "controlled-score-v1", "fixture-T13", "explicit-constant-range", True
    )
    assert (
        create_procurement_plans(PlanningCommand(data, context), PulpCbcSolver()).status
        is PlanningStatus.OPTIMAL
    )
