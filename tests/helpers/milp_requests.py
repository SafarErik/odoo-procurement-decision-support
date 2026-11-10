"""Small MILP planning requests and an exhaustive reference optimum, independent of the core."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from itertools import product

from decision_core.planning.models import (
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    ProcurementRequirement,
    QuantityRange,
    RiskCoefficient,
    SupplierTerms,
)

DAY = date(2026, 10, 21)

# Wall-clock budget for tests that check what the solver returns, not how fast. These
# problems solve in well under a second, but on an overloaded CI runner (2026-11-06 and
# 2026-11-09) the production budget ran out and CBC honestly answered no_proven_optimum.
# Only tests about the budget itself use the production limit.
CORRECTNESS_BUDGET_SECONDS = 600


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
