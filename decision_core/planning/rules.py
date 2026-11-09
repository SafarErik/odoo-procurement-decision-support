"""Exact business feasibility and deterministic output checks, without solver imports."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from decision_core.planning.models import (
    Allocation,
    Explanation,
    PlanningRequest,
    ProcurementPlan,
    require,
)


@dataclass(frozen=True, slots=True)
class SupplierBounds:
    supplier_id: str
    lower: int
    upper: int
    exclusions: tuple[Explanation, ...]


def bounds(request: PlanningRequest) -> tuple[SupplierBounds, ...]:
    r, p = request.requirement, request.policy
    ceiling = r.approved_quantity
    if p.concentration_limit is not None:
        ceiling = int(Fraction(p.concentration_limit) * r.approved_quantity)
    values = []
    for s in sorted(request.suppliers, key=lambda s: s.supplier_id):
        lower = max(
            1,
            s.minimum_order.quantity or 1,
            s.price_quantities.minimum,
            s.delivery_quantities.minimum,
        )
        upper = min(s.capacity, ceiling, s.price_quantities.maximum, s.delivery_quantities.maximum)
        exclusions = []
        if not s.available:
            exclusions.append(
                Explanation("unavailable", "Explicit availability forbids use.", s.supplier_id)
            )
        if s.promised_date > r.required_date:
            exclusions.append(
                Explanation(
                    "deadline_ineligible",
                    "The quantity-specific promise is after the required date.",
                    s.supplier_id,
                )
            )
        if lower > upper:
            exclusions.append(
                Explanation(
                    "no_valid_quantity",
                    f"Positive-use lower bound {lower} exceeds effective ceiling {upper}.",
                    s.supplier_id,
                )
            )
        values.append(
            SupplierBounds(s.supplier_id, lower, 0 if exclusions else upper, tuple(exclusions))
        )
    return tuple(values)


def validate_risk(request: PlanningRequest) -> bool:
    """Never narrow physical feasibility or extrapolate quantity-dependent scores."""
    scores = {c.supplier_id: c for c in request.risk_coefficients or ()}
    usable = [b for b in bounds(request) if b.upper > 0]
    complete = all(b.supplier_id in scores for b in usable)
    if request.policy.epsilons or request.policy.diversification_epsilon is not None:
        require(
            complete and request.risk_coefficients is not None,
            "risk_unavailable",
            "Epsilon alternatives require explicit scores for every usable supplier.",
        )
    for b in usable:
        if b.supplier_id in scores:
            validity = scores[b.supplier_id].valid_quantities
            require(
                validity.minimum <= b.lower and validity.maximum >= b.upper,
                "risk_quantity_context_mismatch",
                "A coefficient must cover every feasible positive quantity; no extrapolation.",
            )
    return complete and request.risk_coefficients is not None


def necessary_diagnostics(request: PlanningRequest) -> tuple[Explanation, ...]:
    limits = bounds(request)
    reasons = [e for b in limits for e in b.exclusions]
    ceilings = sorted((b.upper for b in limits), reverse=True)
    if sum(ceilings) < request.requirement.approved_quantity:
        reasons.append(
            Explanation(
                "insufficient_effective_capacity",
                "Sum of effective ceilings is below approved demand.",
            )
        )
    elif sum(ceilings[: request.policy.max_suppliers]) < request.requirement.approved_quantity:
        reasons.append(
            Explanation(
                "supplier_count_capacity_shortfall",
                "Largest permitted supplier ceilings cannot meet approved demand.",
            )
        )
    return tuple(reasons)


def exact_decimal(value: Fraction) -> Decimal:
    """Convert a terminating money rational without ambient Decimal-context rounding."""
    denominator, twos, fives = value.denominator, 0, 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    require(denominator == 1, "invalid_money", "Monetary values must terminate as Decimal.")
    places = max(twos, fives)
    integer = value.numerator * 2 ** (places - twos) * 5 ** (places - fives)
    return Decimal((int(integer < 0), tuple(int(d) for d in str(abs(integer))), -places))


def checked_plan(
    request: PlanningRequest,
    allocations: tuple[Allocation, ...],
    reference_cost: Fraction | None = None,
    epsilon: Decimal | None = None,
) -> ProcurementPlan:
    """Verify a solver's allocation exactly and turn it into a plan with its explanations.

    The solver's answer is never trusted: every business rule is rechecked here with
    exact integer/rational arithmetic, and the metrics (cost, exposure, largest share,
    premium) are recomputed. With ``reference_cost`` (the proven minimum cost) the plan
    may not be cheaper than it, and with ``epsilon`` not dearer than
    ``reference_cost * (1 + epsilon)``. A violation raises ``InvalidPlanningInput`` with
    code ``invalid_solver_output``.
    """
    ordered = tuple(sorted(request.suppliers, key=lambda s: s.supplier_id))
    limits = bounds(request)
    _check_allocations(request, allocations, ordered, limits)
    q = request.requirement.approved_quantity
    cost = sum(
        (Fraction(s.unit_price) * a.quantity for s, a in zip(ordered, allocations, strict=True)),
        Fraction(),
    )
    if reference_cost is not None:
        require(
            cost >= reference_cost, "invalid_solver_output", "Cost is below the proven reference."
        )
        if epsilon is not None:
            require(
                cost <= reference_cost * (1 + Fraction(epsilon)),
                "invalid_solver_output",
                "Exact epsilon cost cap is violated.",
            )
    premium = Fraction() if reference_cost is None else (cost - reference_cost) / reference_cost
    complete = validate_risk(request)
    scores = {c.supplier_id: Fraction(c.value) for c in request.risk_coefficients or ()}
    exposure = (
        sum((scores[a.supplier_id] * a.quantity for a in allocations if a.quantity), Fraction()) / q
        if complete
        else None
    )
    count = sum(a.quantity > 0 for a in allocations)
    reasons = list(necessary_diagnostics(request))
    for s, a, b in zip(ordered, allocations, limits, strict=True):
        reasons += _supplier_explanations(request, s, a.quantity, b)
    reasons += _plan_explanations(request, count, premium, exposure)
    return ProcurementPlan(
        allocations,
        exact_decimal(cost),
        exposure,
        Fraction(max(a.quantity for a in allocations), q),
        count,
        premium,
        tuple(reasons),
    )


def _check_allocations(request, allocations, ordered, limits) -> None:
    """One integer quantity per supplier in id order, within its bounds, meeting demand
    exactly and using at most the allowed number of suppliers."""
    require(
        isinstance(allocations, tuple) and all(isinstance(a, Allocation) for a in allocations),
        "invalid_solver_output",
        "Allocations must be immutable typed values.",
    )
    require(
        tuple(a.supplier_id for a in allocations) == tuple(s.supplier_id for s in ordered),
        "invalid_solver_output",
        "Every supplier must appear exactly once in stable order.",
    )
    for a, b in zip(allocations, limits, strict=True):
        require(
            type(a.quantity) is int
            and 0 <= a.quantity <= b.upper
            and (a.quantity == 0 or a.quantity >= b.lower),
            "invalid_solver_output",
            "Allocation violates exact positive-use business bounds.",
        )
    count = sum(a.quantity > 0 for a in allocations)
    require(
        sum(a.quantity for a in allocations) == request.requirement.approved_quantity
        and count <= request.policy.max_suppliers,
        "invalid_solver_output",
        "Demand or maximum supplier count is violated.",
    )


def _supplier_explanations(request, supplier, quantity: int, limit) -> list[Explanation]:
    """What one supplier got and which of its limits the quantity reached."""
    q = request.requirement.approved_quantity
    identity = supplier.supplier_id
    reasons = [Explanation("allocation", f"Allocated {quantity} of {q} integer units.", identity)]
    if limit.upper > 0:
        reasons.append(
            Explanation(
                "effective_bounds",
                f"Positive-use range [{limit.lower}, {limit.upper}]; "
                f"upper slack {limit.upper - quantity}.",
                identity,
            )
        )
    if not quantity and limit.upper > 0:
        reasons.append(
            Explanation(
                "zero_in_optimal_plan",
                "Zero in the objective/tie-break solution; not a hard exclusion or causal proof.",
                identity,
            )
        )
    if not quantity:
        return reasons
    for code, bound in (
        ("capacity_binding", supplier.capacity),
        ("moq_binding", supplier.minimum_order.quantity),
        ("price_lower_binding", supplier.price_quantities.minimum),
        ("price_upper_binding", supplier.price_quantities.maximum),
        ("delivery_lower_binding", supplier.delivery_quantities.minimum),
        ("delivery_upper_binding", supplier.delivery_quantities.maximum),
    ):
        if quantity == bound:
            reasons.append(
                Explanation(code, f"Allocation reaches explicit bound {bound}.", identity)
            )
    limit_share = request.policy.concentration_limit
    if limit_share is not None and quantity == int(Fraction(limit_share) * q):
        # The integer ceiling floor(c * Q) can sit just below the exact share c * Q.
        code = (
            "concentration_binding"
            if Fraction(quantity, q) == Fraction(limit_share)
            else "integer_concentration_ceiling"
        )
        reasons.append(Explanation(code, "Integer concentration ceiling reached.", identity))
    return reasons


def _plan_explanations(request, count, premium, exposure) -> list[Explanation]:
    """Plan-level notes: supplier-count limit reached, cost premium, exposure meaning."""
    reasons = []
    if count == request.policy.max_suppliers:
        reasons.append(Explanation("supplier_count_binding", "Maximum supplier count reached."))
    reasons.append(
        Explanation("cost_premium", f"Exact relative premium {premium} over minimum cost.")
    )
    if exposure is None:
        reasons.append(
            Explanation(
                "risk_not_evaluated",
                "Explicit cost-only result; no complete valid risk exposure is asserted.",
            )
        )
    else:
        reasons.append(
            Explanation(
                "external_risk_exposure",
                "Quantity-weighted external score exposure, not a calibrated failure probability.",
            )
        )
    return reasons
