"""ERP-neutral planning orchestration over a replaceable solver port."""

import math
import time
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Protocol

from decision_core.planning.models import (
    Allocation,
    AlternativeRun,
    Explanation,
    InvalidPlanningInput,
    PlanningRequest,
    PlanningResult,
    PlanningStatus,
)
from decision_core.planning.rules import checked_plan, necessary_diagnostics, validate_risk


@dataclass(frozen=True, slots=True)
class SolveOutcome:
    status: PlanningStatus
    allocations: tuple[Allocation, ...] = ()
    code: str = ""


class AllocationSolver(Protocol):
    def minimum_cost(self, request: PlanningRequest, deadline: float) -> SolveOutcome: ...
    def risk_alternative(
        self, request: PlanningRequest, reference_cost: Fraction, epsilon: Decimal, deadline: float
    ) -> SolveOutcome: ...


def plan_procurement(
    request: PlanningRequest, solver: AllocationSolver, *, time_limit_seconds: float = 30.0
) -> PlanningResult:
    """One shared wall-clock budget; verified reference survives failed alternative work."""
    if (
        not isinstance(request, PlanningRequest)
        or type(time_limit_seconds) not in (int, float)
        or not math.isfinite(time_limit_seconds)
        or time_limit_seconds <= 0
    ):
        return PlanningResult(
            PlanningStatus.INVALID_INPUT,
            explanations=(
                Explanation(
                    "invalid_request", "Supply a typed request and positive finite time budget."
                ),
            ),
        )
    deadline = time.monotonic() + time_limit_seconds
    try:
        validate_risk(request)
        diagnostics = necessary_diagnostics(request)
        if any(
            e.code in ("insufficient_effective_capacity", "supplier_count_capacity_shortfall")
            for e in diagnostics
        ):
            return PlanningResult(PlanningStatus.INFEASIBLE, explanations=diagnostics)
        outcome = solver.minimum_cost(request, deadline)
        if outcome.status is not PlanningStatus.OPTIMAL:
            return PlanningResult(
                outcome.status,
                explanations=diagnostics
                + (
                    Explanation(
                        outcome.code or outcome.status.value,
                        (
                            "The solver proved the combined hard constraints infeasible; "
                            "no minimal conflict set was computed."
                            if outcome.status is PlanningStatus.INFEASIBLE
                            else "No verified minimum-cost plan is available."
                        ),
                    ),
                ),
            )
        minimum = checked_plan(request, outcome.allocations)
    except InvalidPlanningInput as exc:
        status = (
            PlanningStatus.SOLVER_ERROR
            if exc.code == "invalid_solver_output"
            else PlanningStatus.INVALID_INPUT
        )
        return PlanningResult(status, explanations=(Explanation(exc.code, str(exc)),))
    except Exception:
        return PlanningResult(
            PlanningStatus.SOLVER_ERROR,
            explanations=(
                Explanation("solver_failure", "Solver adapter failed; no plan is returned."),
            ),
        )
    distinct, runs = [], []
    signatures = {minimum.allocations: 0}
    status = PlanningStatus.OPTIMAL
    for epsilon in sorted(set(request.policy.epsilons)):
        try:
            outcome = solver.risk_alternative(
                request, Fraction(minimum.total_cost), epsilon, deadline
            )
            if outcome.status is PlanningStatus.INFEASIBLE:
                outcome = SolveOutcome(
                    PlanningStatus.SOLVER_ERROR, code="contradictory_alternative_infeasibility"
                )
            if outcome.status is not PlanningStatus.OPTIMAL:
                status = outcome.status
                runs.append(AlternativeRun(epsilon, status, None, outcome.code))
                break
            plan = checked_plan(request, outcome.allocations, Fraction(minimum.total_cost), epsilon)
            if plan.risk_exposure is None or plan.risk_exposure > minimum.risk_exposure:
                raise InvalidPlanningInput(
                    "invalid_solver_output",
                    "Alternative worsens the feasible minimum's score exposure.",
                )
            duplicate = plan.allocations in signatures
            if not duplicate:
                distinct.append(plan)
                signatures[plan.allocations] = len(distinct)
            runs.append(
                AlternativeRun(
                    epsilon,
                    PlanningStatus.OPTIMAL,
                    signatures[plan.allocations],
                    "duplicate_allocation" if duplicate else "distinct_alternative",
                )
            )
        except Exception:
            status = PlanningStatus.SOLVER_ERROR
            runs.append(AlternativeRun(epsilon, status, None, "alternative_verification_failed"))
            break
    return PlanningResult(status, minimum, tuple(distinct), tuple(runs), diagnostics)
