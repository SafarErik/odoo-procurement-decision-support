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
    ProcurementPlan,
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
    def diversified_alternative(
        self,
        request: PlanningRequest,
        reference_cost: Fraction,
        reference_risk: Fraction,
        epsilon: Decimal,
        deadline: float,
    ) -> SolveOutcome: ...


# Wall-clock budget for one planning run (minimum cost plus all alternatives).
SOLVER_TIME_LIMIT_SECONDS = 30.0


def plan_procurement(
    request: PlanningRequest,
    solver: AllocationSolver,
    *,
    time_limit_seconds: float = SOLVER_TIME_LIMIT_SECONDS,
) -> PlanningResult:
    """Solve the minimum-cost plan, then one alternative per stage, all verified exactly.

    Stages (docs/MODEL_MILP.md §3): one lower-risk alternative per cost tolerance
    epsilon, in increasing order, then the balanced (diversified) alternative when the
    policy asks for one. All stages share one wall-clock budget. Every solver answer is
    rechecked with ``checked_plan``; an alternative found twice is recorded as a
    duplicate, never stored twice. If a later stage fails, the verified plans found so
    far are kept and the result's status names the failure.
    """
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
    first = _minimum_cost_stage(request, solver, deadline)
    if isinstance(first, PlanningResult):
        return first
    minimum, diagnostics = first
    distinct, runs = [], []
    signatures = {minimum.allocations: 0}
    status = PlanningStatus.OPTIMAL
    stages = [(epsilon, "risk") for epsilon in sorted(set(request.policy.epsilons))]
    if request.policy.diversification_epsilon is not None:
        stages.append((request.policy.diversification_epsilon, "diversified"))
    for epsilon, kind in stages:
        try:
            plan = _alternative_stage(request, solver, minimum, epsilon, kind, deadline)
            # Anything else is the solver's non-optimal outcome; read it here, in the try.
            failed = None if isinstance(plan, ProcurementPlan) else (plan.status, plan.code)
        except Exception:
            failed = (PlanningStatus.SOLVER_ERROR, "alternative_verification_failed")
        if failed is not None:
            status = failed[0]
            runs.append(AlternativeRun(epsilon, status, None, failed[1], kind))
            break
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
                kind,
            )
        )
    return PlanningResult(status, minimum, tuple(distinct), tuple(runs), diagnostics)


def _minimum_cost_stage(request, solver, deadline):
    """The verified minimum-cost plan and the necessary diagnostics, or the final result.

    Returns a ``PlanningResult`` when planning ends here: the bounds already prove the
    demand cannot be met, the solver finds no optimum, the input is invalid, or the
    solver adapter fails.
    """
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
        return checked_plan(request, outcome.allocations), diagnostics
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


def _alternative_stage(request, solver, minimum, epsilon, kind, deadline):
    """One verified alternative plan, or the non-optimal ``SolveOutcome`` that ends planning.

    The alternative may cost at most ``(1 + epsilon)`` times the minimum cost, may not
    have more risk exposure than the minimum-cost plan, and a balanced one may not
    depend more on one supplier. A broken promise raises ``InvalidPlanningInput``.
    Infeasible is impossible here (the minimum-cost plan itself satisfies every
    constraint), so a solver claiming it is reported as a solver error.
    """
    reference_cost = Fraction(minimum.total_cost)
    if kind == "risk":
        outcome = solver.risk_alternative(request, reference_cost, epsilon, deadline)
    else:
        outcome = solver.diversified_alternative(
            request, reference_cost, minimum.risk_exposure, epsilon, deadline
        )
    if outcome.status is PlanningStatus.INFEASIBLE:
        outcome = SolveOutcome(
            PlanningStatus.SOLVER_ERROR, code="contradictory_alternative_infeasibility"
        )
    if outcome.status is not PlanningStatus.OPTIMAL:
        return outcome
    plan = checked_plan(request, outcome.allocations, reference_cost, epsilon)
    if plan.risk_exposure is None or plan.risk_exposure > minimum.risk_exposure:
        raise InvalidPlanningInput(
            "invalid_solver_output",
            "Alternative worsens the feasible minimum's score exposure.",
        )
    if kind == "diversified" and plan.largest_share > minimum.largest_share:
        raise InvalidPlanningInput(
            "invalid_solver_output",
            "Balanced alternative raises the minimum plan's largest supplier share.",
        )
    return plan
