"""Provisional PuLP 3.3/CBC adapter with exact integer encoding and verified phases."""

import math
import re
import subprocess
import time
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import reduce

import pulp

from decision_core.planning.models import (
    Allocation,
    InvalidPlanningInput,
    PlanningRequest,
    PlanningStatus,
    require,
)
from decision_core.planning.planner import SolveOutcome
from decision_core.planning.rules import bounds, validate_risk


@dataclass(frozen=True, slots=True)
class CbcConfiguration:
    """Infrastructure limits, not permanent procurement business limits."""

    exact_integer_budget: int = 2**40
    decimal_representation_limit: int = 64
    integrality_tolerance: float = 1e-6
    seed: int = 17

    def __post_init__(self):
        if (
            type(self.exact_integer_budget) is not int
            or not 1 <= self.exact_integer_budget <= 2**52
            or type(self.decimal_representation_limit) is not int
            or self.decimal_representation_limit < 1
            or type(self.seed) is not int
            or not 1 <= self.seed < 2**31
            or not math.isfinite(self.integrality_tolerance)
            or not 0 < self.integrality_tolerance < 0.5
        ):
            raise ValueError("Invalid CBC infrastructure configuration.")


@dataclass
class EncodedModel:
    problem: pulp.LpProblem
    quantities: list[pulp.LpVariable]
    identities: tuple[str, ...]
    cost: pulp.LpAffineExpression
    risk: pulp.LpAffineExpression
    costs: tuple[int, ...]
    risks: tuple[int, ...]
    cost_unit: Fraction


class PulpCbcSolver:
    def __init__(self, configuration: CbcConfiguration | None = None):
        self.configuration = configuration or CbcConfiguration()

    def runtime_info(self) -> dict[str, str]:
        solver = self._solver(5)
        executable = solver.available()
        if not executable:
            raise RuntimeError("CBC executable is unavailable.")
        response = subprocess.run(
            [str(executable), "-stop"], capture_output=True, text=True, check=True, timeout=5
        )
        version = re.search(r"Version:\s*([^\s]+)", response.stdout)
        if version is None:
            raise RuntimeError("CBC version could not be established.")
        return {
            "pulp": pulp.__version__,
            "cbc": version[1],
            "threads": "1",
            "seed": str(self.configuration.seed),
        }

    def _solver(self, remaining: float):
        return pulp.PULP_CBC_CMD(
            msg=False,
            threads=1,
            timeLimit=remaining,
            gapRel=0,
            gapAbs=0,
            timeMode="elapsed",
            options=[
                f"randomSeed {self.configuration.seed}",
                f"randomCbcSeed {self.configuration.seed}",
                f"integerTolerance {self.configuration.integrality_tolerance}",
            ],
        )

    def _fraction(self, value: Decimal) -> Fraction:
        digits = value.as_tuple()
        require(
            len(digits.digits) <= self.configuration.decimal_representation_limit
            and abs(digits.exponent) <= self.configuration.decimal_representation_limit,
            "unsupported_numeric_contract",
            "Decimal representation exceeds adapter budget.",
        )
        return Fraction(value)

    def _scale(self, values: tuple[Decimal, ...]) -> tuple[tuple[int, ...], Fraction]:
        rationals = tuple(self._fraction(v) for v in values)
        denominator = math.lcm(*(v.denominator for v in rationals))
        integers = tuple(v.numerator * (denominator // v.denominator) for v in rationals)
        divisor = reduce(math.gcd, integers, 0) or 1
        return tuple(v // divisor for v in integers), Fraction(divisor, denominator)

    def _model(self, request: PlanningRequest) -> EncodedModel:
        suppliers = tuple(sorted(request.suppliers, key=lambda s: s.supplier_id))
        costs, cost_unit = self._scale(tuple(s.unit_price for s in suppliers))
        scores = {c.supplier_id: c.value for c in request.risk_coefficients or ()}
        risks, _ = self._scale(tuple(scores.get(s.supplier_id, Decimal(0)) for s in suppliers))
        # Risk zero here is an unused internal cost-only expression, not an asserted missing score.
        q = request.requirement.approved_quantity
        require(
            max(q, max(costs) * q, max(risks) * q, len(suppliers))
            <= self.configuration.exact_integer_budget,
            "unsupported_numeric_contract",
            "Integer objective/RHS envelope exceeds CBC adapter budget.",
        )
        limits = bounds(request)
        problem = pulp.LpProblem("v2_single_product", pulp.LpMinimize)
        x = [
            pulp.LpVariable(f"quantity_{i}", 0, b.upper, cat="Integer")
            for i, b in enumerate(limits)
        ]
        y = [pulp.LpVariable(f"active_{i}", cat="Binary") for i in range(len(limits))]
        problem += pulp.lpSum(x) == q, "approved_demand"
        problem += (
            pulp.lpSum(y) <= min(request.policy.max_suppliers, len(suppliers)),
            "max_supplier_count",
        )
        for i, b in enumerate(limits):
            problem += x[i] <= b.upper * y[i], f"activation_upper_{i}"
            problem += x[i] >= (b.lower if b.upper else 1) * y[i], f"positive_use_lower_{i}"
        cost = pulp.lpSum(c * v for c, v in zip(costs, x, strict=True))
        risk = pulp.lpSum(c * v for c, v in zip(risks, x, strict=True))
        return EncodedModel(
            problem,
            x,
            tuple(s.supplier_id for s in suppliers),
            cost,
            risk,
            costs,
            risks,
            cost_unit,
        )

    def _integer_values(self, problem: pulp.LpProblem) -> dict[pulp.LpVariable, int]:
        values = {}
        for variable in problem.variables():
            if variable.name == "__dummy":
                if variable.lowBound != 0 or variable.upBound != 0:
                    raise ValueError("Unexpected constant objective variable.")
                values[variable] = 0
                continue
            raw = variable.value()
            if (
                raw is None
                or not math.isfinite(raw)
                or abs(raw - round(raw)) > self.configuration.integrality_tolerance
            ):
                raise ValueError("Solver returned a missing/noninteger value.")
            value = round(raw)
            if (variable.lowBound is not None and value < variable.lowBound) or (
                variable.upBound is not None and value > variable.upBound
            ):
                raise ValueError("Exact variable bound violated.")
            values[variable] = value
        for constraint in problem.constraints.values():
            if (
                any(not float(c).is_integer() for c in constraint.values())
                or not float(constraint.constant).is_integer()
            ):
                raise ValueError("Noninteger model encoding.")
            residual = sum(int(c) * values[v] for v, c in constraint.items()) + int(
                constraint.constant
            )
            if (
                (constraint.sense == pulp.LpConstraintEQ and residual != 0)
                or (constraint.sense == pulp.LpConstraintLE and residual > 0)
                or (constraint.sense == pulp.LpConstraintGE and residual < 0)
            ):
                raise ValueError("Exact model constraint or objective lock violated.")
        return values

    def _run(
        self, model: EncodedModel, deadline: float, *, initial: bool = False
    ) -> PlanningStatus:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return PlanningStatus.NO_PROVEN_OPTIMUM
        solver = self._solver(remaining)
        if not solver.available():
            return PlanningStatus.SOLVER_ERROR
        model.problem.solve(solver)
        if time.monotonic() > deadline:
            return PlanningStatus.NO_PROVEN_OPTIMUM
        if model.problem.status == pulp.LpStatusInfeasible:
            return PlanningStatus.INFEASIBLE if initial else PlanningStatus.SOLVER_ERROR
        if (
            model.problem.status == pulp.LpStatusOptimal
            and model.problem.sol_status == pulp.LpSolutionOptimal
        ):
            self._integer_values(model.problem)
            return PlanningStatus.OPTIMAL
        return PlanningStatus.NO_PROVEN_OPTIMUM

    def _quantities(self, model: EncodedModel) -> tuple[int, ...]:
        values = self._integer_values(model.problem)
        return tuple(values[x] for x in model.quantities)

    def _tie_break(self, model: EncodedModel, deadline: float) -> PlanningStatus:
        # The last quantity follows from demand and earlier locks.
        for i, variable in enumerate(model.quantities[:-1]):
            if variable.upBound == 0:
                continue
            model.problem.setObjective(-variable)
            status = self._run(model, deadline)
            if status is not PlanningStatus.OPTIMAL:
                return status
            model.problem += variable == self._quantities(model)[i], f"stable_quantity_{i}"
        return PlanningStatus.OPTIMAL

    def _outcome(self, status: PlanningStatus, model: EncodedModel) -> SolveOutcome:
        if status is not PlanningStatus.OPTIMAL:
            code = (
                "interacting_constraints_infeasible"
                if status is PlanningStatus.INFEASIBLE
                else status.value
            )
            return SolveOutcome(status, code=code)
        return SolveOutcome(
            status,
            tuple(
                Allocation(i, q)
                for i, q in zip(model.identities, self._quantities(model), strict=True)
            ),
        )

    def minimum_cost(self, request: PlanningRequest, deadline: float) -> SolveOutcome:
        try:
            model = self._model(request)
            model.problem.setObjective(model.cost)
            status = self._run(model, deadline, initial=True)
            if status is not PlanningStatus.OPTIMAL:
                return self._outcome(status, model)
            optimum = sum(c * x for c, x in zip(model.costs, self._quantities(model), strict=True))
            model.problem += model.cost == optimum, "proven_minimum_cost"
            return self._outcome(self._tie_break(model, deadline), model)
        except InvalidPlanningInput as exc:
            return SolveOutcome(PlanningStatus.INVALID_INPUT, code=exc.code)
        except (pulp.PulpSolverError, OSError, ValueError, OverflowError):
            return SolveOutcome(PlanningStatus.SOLVER_ERROR, code="solver_or_verification_failure")

    def risk_alternative(
        self, request: PlanningRequest, reference_cost: Fraction, epsilon: Decimal, deadline: float
    ) -> SolveOutcome:
        try:
            require(validate_risk(request), "risk_unavailable", "Risk coefficients are incomplete.")
            model = self._model(request)
            cap = int(reference_cost / model.cost_unit * (1 + self._fraction(epsilon)))
            require(
                cap <= self.configuration.exact_integer_budget,
                "unsupported_numeric_contract",
                "Cost-cap RHS exceeds adapter budget.",
            )
            model.problem += model.cost <= cap, "epsilon_cost_cap"
            model.problem.setObjective(model.risk)
            status = self._run(model, deadline)
            if status is not PlanningStatus.OPTIMAL:
                return self._outcome(status, model)
            optimum = sum(c * x for c, x in zip(model.risks, self._quantities(model), strict=True))
            model.problem += model.risk == optimum, "proven_minimum_risk"
            model.problem.setObjective(model.cost)
            status = self._run(model, deadline)
            if status is not PlanningStatus.OPTIMAL:
                return self._outcome(status, model)
            cost = sum(c * x for c, x in zip(model.costs, self._quantities(model), strict=True))
            model.problem += model.cost == cost, "secondary_minimum_cost"
            return self._outcome(self._tie_break(model, deadline), model)
        except InvalidPlanningInput as exc:
            return SolveOutcome(PlanningStatus.INVALID_INPUT, code=exc.code)
        except (pulp.PulpSolverError, OSError, ValueError, OverflowError):
            return SolveOutcome(PlanningStatus.SOLVER_ERROR, code="solver_or_verification_failure")
