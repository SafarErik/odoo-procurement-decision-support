"""PuLP/CBC encoding of the supplier selection and order allocation MILP.

The full model, with its business meaning, is in docs/MODEL_MILP.md. This module only
encodes it for CBC and reads the answer back; the planning core (``decision_core``)
decides the stages and rechecks every answer exactly.

Data for one product and suppliers i = 1..N, sorted by supplier id:

    Q          approved demand (integer)
    p_i        unit price;  r_i  risk score from the supplier evaluation (0..1)
    [L_i, U_i] positive-use range from ``rules.bounds``: a used supplier gets at least
               L_i (MOQ, price and delivery ranges) and at most U_i (capacity,
               concentration limit floor(c*Q), price and delivery ranges); U_i = 0 when
               the supplier is excluded
    K          maximum number of suppliers

Decision variables:

    x_i  integer, 0 <= x_i <= U_i   quantity ordered from supplier i
    y_i  binary                      1 when supplier i is used

Constraints of every model:

    sum_i x_i = Q                    demand is met exactly        (approved_demand)
    sum_i y_i <= min(K, N)           supplier count               (max_supplier_count)
    x_i <= U_i * y_i                 no quantity without use      (activation_upper_i)
    x_i >= L_i * y_i                 a used supplier gets >= L_i  (positive_use_lower_i)

For an excluded supplier (U_i = 0) the lower link uses 1 instead of L_i, so y_i = 1
would be infeasible and the supplier stays unused.

Cost C(x) = sum_i p_i x_i; risk R(x) = sum_i r_i x_i, so the plan's risk exposure is
R(x)/Q, the quantity-weighted average score.

Lexicographic phases. Each phase is solved to proven optimality, then its objective is
fixed at that optimum with an equality constraint, so later phases can only choose
among equally good plans:

1. ``minimum_cost``: min C(x) gives C*.
2. ``risk_alternative`` for one cost tolerance eps (epsilon-constraint method):
   add C(x) <= (1 + eps) * C*, then min R(x), then min C(x).
3. ``diversified_alternative`` (balanced plan) for eps_d: add an integer m with
   x_i <= m for all i, C(x) <= (1 + eps_d) * C* and R(x) <= R(x_min) (the minimum-cost
   plan's risk); then min m, then min R(x), then min C(x). m is the most one supplier's
   outage can take from Q.
4. Deterministic tie-break after every phase sequence: in supplier-id order, maximize
   x_i and fix it (the last quantity follows from demand). Equal-cost optima therefore
   always give the same plan, whatever order the suppliers arrived in.

Exact arithmetic: prices and scores are decimals. Each list is scaled to the smallest
integers with the same ratios (p_i = cost_unit * c_i with integer c_i), so CBC only
sees integer coefficients, and the caps are rounded down in those units. After each
run every variable must be integral within the tolerance and every constraint is
rechecked in exact integers. CBC runs single-threaded with a fixed seed and a time
limit equal to what is left of the planning budget; running out of time gives
``NO_PROVEN_OPTIMUM``, never an unproven plan.
"""

import math
import re
import subprocess
import time
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import reduce, wraps

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
    """One CBC model: x_i (``quantities``) in supplier-id order, C(x) and R(x) in integer
    units (``costs``/``risks`` are their coefficients; price = cost_unit * cost)."""

    problem: pulp.LpProblem
    quantities: list[pulp.LpVariable]
    identities: tuple[str, ...]
    cost: pulp.LpAffineExpression
    risk: pulp.LpAffineExpression
    costs: tuple[int, ...]
    risks: tuple[int, ...]
    cost_unit: Fraction
    risk_unit: Fraction


def _failures_as_outcomes(phase):
    """Return failures of a solver phase as an outcome instead of raising.

    Numbers the adapter cannot encode exactly give ``INVALID_INPUT``; a CBC, file or
    answer-verification failure gives ``SOLVER_ERROR``. The planner then records the
    status; it never receives an exception from the adapter.
    """

    @wraps(phase)
    def solve(self, *args, **kwargs) -> SolveOutcome:
        try:
            return phase(self, *args, **kwargs)
        except InvalidPlanningInput as exc:
            return SolveOutcome(PlanningStatus.INVALID_INPUT, code=exc.code)
        except (pulp.PulpSolverError, OSError, ValueError, OverflowError):
            return SolveOutcome(PlanningStatus.SOLVER_ERROR, code="solver_or_verification_failure")

    return solve


class PulpCbcSolver:
    """The ``AllocationSolver`` used in production: one fresh CBC model per phase call."""

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
        """Smallest integers with the same ratios, and the unit: value_i = unit * integer_i."""
        rationals = tuple(self._fraction(v) for v in values)
        denominator = math.lcm(*(v.denominator for v in rationals))
        integers = tuple(v.numerator * (denominator // v.denominator) for v in rationals)
        divisor = reduce(math.gcd, integers, 0) or 1
        return tuple(v // divisor for v in integers), Fraction(divisor, denominator)

    def _model(self, request: PlanningRequest) -> EncodedModel:
        """Variables and the constraints every phase shares; the objective is set later."""
        suppliers = tuple(sorted(request.suppliers, key=lambda s: s.supplier_id))
        costs, cost_unit = self._scale(tuple(s.unit_price for s in suppliers))
        scores = {c.supplier_id: c.value for c in request.risk_coefficients or ()}
        risks, risk_unit = self._scale(
            tuple(scores.get(s.supplier_id, Decimal(0)) for s in suppliers)
        )
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
            risk_unit,
        )

    def _integer_values(self, problem: pulp.LpProblem) -> dict[pulp.LpVariable, int]:
        """CBC's values rounded to integers, after checking every bound and constraint
        exactly; ValueError when CBC's answer does not hold."""
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
        """Solve the current objective with what is left of the budget; verify the answer.

        Infeasible is only a valid answer in the first phase (``initial``): later phases
        keep the minimum-cost plan feasible, so infeasibility there is a solver error.
        """
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
        """Maximize and fix each quantity in supplier-id order (phase 4 above).

        Each step is its own exact solve, so no weighted objective or float scaling is
        involved. Excluded suppliers are skipped and the last quantity follows from
        demand and the earlier locks.
        """
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

    def _minimize_and_fix(
        self, model: EncodedModel, objective, weights, name: str, deadline: float, **run
    ) -> PlanningStatus:
        """One lexicographic phase: minimize ``objective`` (``weights`` are its integer
        coefficients per supplier), then fix it at the optimum as constraint ``name``."""
        model.problem.setObjective(objective)
        status = self._run(model, deadline, **run)
        if status is PlanningStatus.OPTIMAL:
            optimum = sum(w * x for w, x in zip(weights, self._quantities(model), strict=True))
            model.problem += objective == optimum, name
        return status

    def _cost_cap(self, model: EncodedModel, reference_cost: Fraction, epsilon: Decimal) -> int:
        """C(x) <= (1 + epsilon) * C*, in integer cost units, rounded down."""
        cap = int(reference_cost / model.cost_unit * (1 + self._fraction(epsilon)))
        require(
            cap <= self.configuration.exact_integer_budget,
            "unsupported_numeric_contract",
            "Cost-cap RHS exceeds adapter budget.",
        )
        return cap

    @_failures_as_outcomes
    def minimum_cost(self, request: PlanningRequest, deadline: float) -> SolveOutcome:
        """Phase 1: the cheapest plan meeting demand within every supplier limit.

        Infeasible here is a real answer: the hard constraints cannot all hold.
        """
        model = self._model(request)
        status = self._minimize_and_fix(
            model, model.cost, model.costs, "proven_minimum_cost", deadline, initial=True
        )
        if status is not PlanningStatus.OPTIMAL:
            return self._outcome(status, model)
        return self._outcome(self._tie_break(model, deadline), model)

    @_failures_as_outcomes
    def risk_alternative(
        self, request: PlanningRequest, reference_cost: Fraction, epsilon: Decimal, deadline: float
    ) -> SolveOutcome:
        """Phase 2: the lowest-risk plan costing at most (1 + epsilon) times the minimum.

        ``reference_cost`` is the proven minimum cost C*. Among the lowest-risk plans the
        cheapest is taken, then the tie-break.
        """
        require(validate_risk(request), "risk_unavailable", "Risk coefficients are incomplete.")
        model = self._model(request)
        model.problem += (
            model.cost <= self._cost_cap(model, reference_cost, epsilon),
            ("epsilon_cost_cap"),
        )
        for objective, weights, name in (
            (model.risk, model.risks, "proven_minimum_risk"),
            (model.cost, model.costs, "secondary_minimum_cost"),
        ):
            status = self._minimize_and_fix(model, objective, weights, name, deadline)
            if status is not PlanningStatus.OPTIMAL:
                return self._outcome(status, model)
        return self._outcome(self._tie_break(model, deadline), model)

    @_failures_as_outcomes
    def diversified_alternative(
        self,
        request: PlanningRequest,
        reference_cost: Fraction,
        reference_risk: Fraction,
        epsilon: Decimal,
        deadline: float,
    ) -> SolveOutcome:
        """Phase 3: the plan that depends least on any single supplier.

        Within the cost cap and never above the minimum-cost plan's exposure
        ``reference_risk``: min max_i x_i, then min risk, then min cost, then the
        tie-break. ``largest >= x_i`` bounds what one supplier's outage takes from demand.
        """
        require(validate_risk(request), "risk_unavailable", "Risk coefficients are incomplete.")
        model = self._model(request)
        q = request.requirement.approved_quantity
        cap = self._cost_cap(model, reference_cost, epsilon)
        # Exposure is sum(r_i x_i) / Q; the integer risk expression is sum((r_i / risk_unit) x_i).
        risk_cap = math.floor(reference_risk * q / model.risk_unit)
        require(
            risk_cap <= self.configuration.exact_integer_budget,
            "unsupported_numeric_contract",
            "Risk-cap RHS exceeds adapter budget.",
        )
        model.problem += model.cost <= cap, "epsilon_cost_cap"
        model.problem += model.risk <= risk_cap, "reference_risk_cap"
        largest = pulp.LpVariable("largest_quantity", 0, q, cat="Integer")
        for i, x in enumerate(model.quantities):
            model.problem += x <= largest, f"largest_quantity_{i}"
        model.problem.setObjective(largest)
        status = self._run(model, deadline)
        if status is not PlanningStatus.OPTIMAL:
            return self._outcome(status, model)
        model.problem += largest == max(self._quantities(model)), "proven_minimum_largest"
        for objective, weights, name in (
            (model.risk, model.risks, "secondary_minimum_risk"),
            (model.cost, model.costs, "tertiary_minimum_cost"),
        ):
            status = self._minimize_and_fix(model, objective, weights, name, deadline)
            if status is not PlanningStatus.OPTIMAL:
                return self._outcome(status, model)
        return self._outcome(self._tie_break(model, deadline), model)
