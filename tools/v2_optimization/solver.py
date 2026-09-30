"""Local MILP proof with exact integer objectives and lexicographic tie-breaking."""

from decimal import Decimal, localcontext
from fractions import Fraction

import pulp

from tools.v2_optimization.models import (
    MONEY_SCALE,
    RATIO_SCALE,
    Explanation,
    OptimizationResult,
    PriceTier,
    ProcurementOptimizationInput,
    ProcurementPlan,
    Status,
    Supplier,
    scaled,
)


def _ratio(numerator: int, denominator: int) -> Decimal:
    with localcontext() as context:
        context.prec = 40
        return Decimal(numerator) / denominator


def _concentration_ceiling(data: ProcurementOptimizationInput) -> int:
    if data.concentration_limit is None:
        return data.required_quantity
    limit = scaled(data.concentration_limit, "Concentration", RATIO_SCALE, 1, RATIO_SCALE)
    return limit * data.required_quantity // RATIO_SCALE


def _upper(data: ProcurementOptimizationInput, supplier: Supplier) -> int:
    if not supplier.available or not supplier.deadline_eligible:
        return 0
    upper = min(supplier.capacity, _concentration_ceiling(data), data.required_quantity)
    return upper if upper >= max(1, supplier.minimum_quantity) else 0


def _risk_coefficient(supplier: Supplier) -> int:
    assert supplier.historical_adherence is not None
    return RATIO_SCALE - scaled(
        supplier.historical_adherence, "Historical adherence", RATIO_SCALE, 0, RATIO_SCALE
    )


def _price(supplier: Supplier, quantity: int) -> int:
    tiers = supplier.price_tiers or (PriceTier(1, supplier.unit_cost),)
    chosen = tiers[0]
    for tier in tiers:
        if quantity >= tier.minimum_quantity:
            chosen = tier
    return scaled(chosen.unit_cost, "Unit cost", MONEY_SCALE, 1, 100_000_000)


def _diagnostics(data: ProcurementOptimizationInput) -> tuple[Explanation, ...]:
    ceilings = sorted((_upper(data, s) for s in data.suppliers), reverse=True)
    result = []
    for supplier in sorted(data.suppliers, key=lambda s: s.supplier_id):
        if not supplier.available:
            result.append(
                Explanation(supplier.supplier_id, "unavailable", "Availability forbids use.")
            )
        elif not supplier.deadline_eligible:
            result.append(
                Explanation(
                    supplier.supplier_id, "deadline_ineligible", "Hard deadline forbids use."
                )
            )
        elif _upper(data, supplier) == 0:
            result.append(
                Explanation(
                    supplier.supplier_id,
                    "no_usable_quantity",
                    "Capacity/demand/concentration ceiling is below the positive-order/MOQ floor.",
                )
            )
    if sum(ceilings) < data.required_quantity:
        result.append(
            Explanation(
                None,
                "insufficient_effective_capacity",
                f"Effective ceilings sum to {sum(ceilings)} < demand {data.required_quantity}.",
            )
        )
    elif sum(ceilings[: data.max_suppliers]) < data.required_quantity:
        result.append(
            Explanation(
                None,
                "supplier_count_capacity_shortfall",
                f"Largest {data.max_suppliers} effective ceilings cannot fulfill demand.",
            )
        )
    return tuple(result)


def _run(problem: pulp.LpProblem, solver: pulp.PULP_CBC_CMD) -> Status:
    try:
        problem.solve(solver)
    except pulp.PulpSolverError:
        return Status.SOLVER_ERROR
    # CBC can report LpStatusOptimal with only an incumbent after a time limit.
    # Require both problem and solution status to claim an optimum.
    if problem.status == pulp.LpStatusInfeasible:
        return Status.INFEASIBLE
    if problem.status == pulp.LpStatusOptimal and problem.sol_status == pulp.LpSolutionOptimal:
        return Status.OPTIMAL
    return Status.NO_SOLUTION


def _quantities(variables: list[pulp.LpVariable]) -> list[int]:
    values = [variable.value() for variable in variables]
    if any(value is None or abs(value - round(value)) > 1e-6 for value in values):
        raise ValueError("Solver returned a missing or noninteger allocation.")
    return [round(value) for value in values]


def _validate_model(problem: pulp.LpProblem) -> None:
    """Verify every integer primal bound/constraint, including tier variables and locks."""
    values = {}
    for variable in problem.variables():
        if variable.name == "__dummy":
            # PuLP introduces this fixed zero variable for a constant objective.
            if variable.lowBound != 0 or variable.upBound != 0:
                raise ValueError("Unexpected bounds on the solver's constant-objective variable.")
            values[variable] = 0
            continue
        value = _quantities([variable])[0]
        if variable.lowBound is not None and value < variable.lowBound:
            raise ValueError("Solver variable violates its exact lower bound.")
        if variable.upBound is not None and value > variable.upBound:
            raise ValueError("Solver variable violates its exact upper bound.")
        values[variable] = value
    for name, constraint in problem.constraints.items():
        residual = sum(int(coefficient) * values[var] for var, coefficient in constraint.items())
        residual += int(constraint.constant)
        if (
            (constraint.sense == pulp.LpConstraintEQ and residual != 0)
            or (constraint.sense == pulp.LpConstraintLE and residual > 0)
            or (constraint.sense == pulp.LpConstraintGE and residual < 0)
        ):
            raise ValueError(f"Solver solution violates exact model constraint: {name}.")


def _plan(
    data: ProcurementOptimizationInput,
    suppliers: tuple[Supplier, ...],
    quantities: list[int],
    minimum_cost_cents: int | None,
) -> ProcurementPlan:
    if sum(quantities) != data.required_quantity:
        raise ValueError("Solver allocation does not fulfill exact demand.")
    selected = tuple(s.supplier_id for s, x in zip(suppliers, quantities, strict=True) if x)
    if len(selected) > data.max_suppliers:
        raise ValueError("Solver allocation exceeds supplier count.")
    reasons = list(_diagnostics(data))
    for supplier, quantity in zip(suppliers, quantities, strict=True):
        if quantity < 0 or quantity > _upper(data, supplier):
            raise ValueError("Solver allocation exceeds a hard upper bound.")
        if quantity and quantity < max(1, supplier.minimum_quantity):
            raise ValueError("Solver allocation violates MOQ.")
        if quantity == 0 and _upper(data, supplier) > 0:
            reasons.append(
                Explanation(
                    supplier.supplier_id,
                    "zero_in_optimal_plan",
                    "Zero in the objective/tie-break solution; "
                    "this is not a causal exclusion proof.",
                )
            )
        if quantity and quantity == supplier.capacity:
            reasons.append(
                Explanation(
                    supplier.supplier_id, "capacity_binding", f"Capacity reached: {quantity}."
                )
            )
        if quantity and quantity == supplier.minimum_quantity:
            reasons.append(
                Explanation(supplier.supplier_id, "moq_binding", f"MOQ reached: {quantity}.")
            )
        if quantity and data.concentration_limit is not None:
            limit = scaled(data.concentration_limit, "Concentration", RATIO_SCALE, 1, RATIO_SCALE)
            if quantity * RATIO_SCALE == limit * data.required_quantity:
                reasons.append(
                    Explanation(
                        supplier.supplier_id,
                        "concentration_binding",
                        "Concentration bound reached.",
                    )
                )
            elif quantity == _concentration_ceiling(data):
                reasons.append(
                    Explanation(
                        supplier.supplier_id,
                        "integer_concentration_ceiling",
                        "Largest integer allocation below the fractional concentration bound.",
                    )
                )
    cents = sum(_price(s, x) * x for s, x in zip(suppliers, quantities, strict=True))
    history_complete = all(
        s.historical_adherence is not None and s.sample_size >= 3
        for s in suppliers
        if _upper(data, s) > 0
    )
    risk = None
    if history_complete:
        risk_units = sum(
            _risk_coefficient(s) * x for s, x in zip(suppliers, quantities, strict=True) if x
        )
        risk = _ratio(risk_units, data.required_quantity * RATIO_SCALE)
    premium = None
    if minimum_cost_cents is not None:
        premium = _ratio(cents - minimum_cost_cents, minimum_cost_cents)
        reasons.append(
            Explanation(
                None,
                "cost_premium",
                f"Extra cost {_ratio(cents - minimum_cost_cents, MONEY_SCALE):f}; "
                f"relative premium {premium:f} over the minimum-cost plan.",
            )
        )
    return ProcurementPlan(
        allocations=tuple((s.supplier_id, x) for s, x in zip(suppliers, quantities, strict=True)),
        total_quantity=sum(quantities),
        total_cost=_ratio(cents, MONEY_SCALE),
        selected_suppliers=selected,
        risk_proxy=risk,
        concentration=_ratio(max(quantities), data.required_quantity),
        selected_supplier_count=len(selected),
        cost_premium=premium,
        explanations=tuple(reasons),
    )


def optimize(
    data: ProcurementOptimizationInput,
    *,
    epsilon: Decimal | None = None,
) -> OptimizationResult:
    """Minimize cost, or risk within a cap derived from a newly proven minimum cost.

    Identical canonical input yields identical allocation through lexicographic
    maximization by sorted supplier ID after exact primary/secondary objective locks.
    A nonoptimal phase returns no plan. Ten seconds is a per-phase limit.
    """
    if epsilon is not None:
        epsilon_units = scaled(epsilon, "Epsilon", RATIO_SCALE, 0, RATIO_SCALE)
    suppliers = tuple(sorted(data.suppliers, key=lambda s: s.supplier_id))
    diagnostics = _diagnostics(data)
    if any(
        reason.code in {"insufficient_effective_capacity", "supplier_count_capacity_shortfall"}
        for reason in diagnostics
    ):
        return OptimizationResult(Status.INFEASIBLE, reasons=diagnostics)
    if epsilon is not None and any(
        s.historical_adherence is None or s.sample_size < 3
        for s in suppliers
        if _upper(data, s) > 0
    ):
        return OptimizationResult(
            Status.HISTORY_UNAVAILABLE,
            reasons=(
                Explanation(None, "history_unavailable", "Eligible history requires sample >=3."),
            ),
        )

    problem = pulp.LpProblem("single_product_allocation", pulp.LpMinimize)
    x = [
        pulp.LpVariable(f"x_{i}", 0, _upper(data, s), cat="Integer")
        for i, s in enumerate(suppliers)
    ]
    y = [pulp.LpVariable(f"y_{i}", cat="Binary") for i in range(len(suppliers))]
    problem += pulp.lpSum(x) == data.required_quantity, "demand"
    problem += pulp.lpSum(y) <= data.max_suppliers, "max_suppliers"
    cost_terms = []
    for i, supplier in enumerate(suppliers):
        problem += x[i] <= supplier.capacity * y[i], f"capacity_{i}"
        problem += x[i] >= max(1, supplier.minimum_quantity) * y[i], f"moq_positive_use_{i}"
        if data.concentration_limit is not None:
            limit = scaled(data.concentration_limit, "Concentration", RATIO_SCALE, 1, RATIO_SCALE)
            problem += RATIO_SCALE * x[i] <= limit * data.required_quantity, f"concentration_{i}"
        if not supplier.price_tiers:
            cost_terms.append(_price(supplier, 1) * x[i])
            continue
        z = []
        q = []
        for k, tier in enumerate(supplier.price_tiers):
            active = pulp.LpVariable(f"z_{i}_{k}", cat="Binary")
            quantity = pulp.LpVariable(f"q_{i}_{k}", lowBound=0, cat="Integer")
            next_threshold = (
                supplier.price_tiers[k + 1].minimum_quantity
                if k + 1 < len(supplier.price_tiers)
                else data.required_quantity + 1
            )
            upper = min(_upper(data, supplier), next_threshold - 1)
            problem += quantity >= tier.minimum_quantity * active, f"tier_lower_{i}_{k}"
            problem += quantity <= upper * active, f"tier_upper_{i}_{k}"
            z.append(active)
            q.append(quantity)
            cost_terms.append(
                scaled(tier.unit_cost, "Price", MONEY_SCALE, 1, 100_000_000) * quantity
            )
        problem += pulp.lpSum(z) == y[i], f"one_tier_{i}"
        problem += pulp.lpSum(q) == x[i], f"tier_quantity_{i}"
    cost = pulp.lpSum(cost_terms)
    solver = pulp.PULP_CBC_CMD(
        msg=False,
        threads=1,
        timeLimit=10,
        gapRel=0,
        gapAbs=0,
        options=["randomSeed 1", "randomCbcSeed 1"],
    )

    def failed(status: Status) -> OptimizationResult:
        detail = (
            "Solver proved infeasibility from interacting demand, MOQ, count and upper bounds; "
            "no minimal conflict set is available."
            if status is Status.INFEASIBLE
            else "A solve phase did not prove an optimum; no plan is returned."
        )
        return OptimizationResult(
            status, reasons=diagnostics + (Explanation(None, status, detail),)
        )

    problem.setObjective(cost)
    status = _run(problem, solver)
    if status is not Status.OPTIMAL:
        return failed(status)
    try:
        _validate_model(problem)
        first = _plan(data, suppliers, _quantities(x), None)
        minimum_cents = int(Fraction(first.total_cost) * MONEY_SCALE)
        risk_optimum = None
        if epsilon is None:
            problem += cost == minimum_cents, "cost_optimum"
        else:
            # Floor to cents: a fractional-cent cap cannot buy another cent of cost.
            cap = minimum_cents * (RATIO_SCALE + epsilon_units) // RATIO_SCALE
            problem += cost <= cap, "epsilon_cost_cap"
            risk = pulp.lpSum(
                _risk_coefficient(s) * x[i] for i, s in enumerate(suppliers) if _upper(data, s) > 0
            )
            problem.setObjective(risk)
            status = _run(problem, solver)
            if status is not Status.OPTIMAL:
                return failed(status)
            _validate_model(problem)
            quantities = _quantities(x)
            risk_optimum = sum(
                _risk_coefficient(s) * quantity
                for s, quantity in zip(suppliers, quantities, strict=True)
                if quantity
            )
            problem += risk == risk_optimum, "risk_optimum"
            # Remove weakly dominated, unnecessarily expensive equal-risk plans.
            problem.setObjective(cost)
            status = _run(problem, solver)
            if status is not Status.OPTIMAL:
                return failed(status)
            _validate_model(problem)
            best = _plan(data, suppliers, _quantities(x), minimum_cents)
            problem += (
                cost == int(Fraction(best.total_cost) * MONEY_SCALE),
                "secondary_cost_optimum",
            )
        # Sequential objectives avoid tiny weighted perturbations and huge tie-break weights.
        for i, variable in enumerate(x):
            problem.setObjective(-variable)
            status = _run(problem, solver)
            if status is not Status.OPTIMAL:
                return failed(status)
            _validate_model(problem)
            quantities = _quantities(x)
            problem += variable == quantities[i], f"lexicographic_{i}"
        plan = _plan(
            data, suppliers, _quantities(x), minimum_cents if epsilon is not None else None
        )
        if epsilon is None and int(Fraction(plan.total_cost) * MONEY_SCALE) != minimum_cents:
            raise ValueError("Exact cost optimum was not preserved.")
        if epsilon is not None:
            if int(Fraction(plan.total_cost) * MONEY_SCALE) > cap:
                raise ValueError("Exact epsilon cap was violated.")
            actual_risk = sum(
                _risk_coefficient(s) * quantity
                for s, quantity in zip(suppliers, _quantities(x), strict=True)
                if quantity
            )
            if actual_risk != risk_optimum:
                raise ValueError("Exact risk optimum was not preserved.")
        return OptimizationResult(Status.OPTIMAL, plan)
    except ValueError as error:
        return OptimizationResult(
            Status.NO_SOLUTION, reasons=(Explanation(None, "verification_failed", str(error)),)
        )
