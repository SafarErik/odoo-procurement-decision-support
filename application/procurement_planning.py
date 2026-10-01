"""T13 use-case entry point; no concrete solver, ERP, persistence or ML imports."""

from dataclasses import dataclass

from decision_core.planning.models import (
    Explanation,
    PlanningRequest,
    PlanningResult,
    PlanningStatus,
)
from decision_core.planning.planner import AllocationSolver, plan_procurement


@dataclass(frozen=True, slots=True)
class ExternalRiskContext:
    """Application-owned score definition and validity evidence, not calibration proof."""

    definition_reference: str
    assessment_reference: str
    validity_reference: str
    controlled_fixture: bool

    def __post_init__(self):
        if (
            any(
                not isinstance(x, str) or not x.strip()
                for x in (
                    self.definition_reference,
                    self.assessment_reference,
                    self.validity_reference,
                )
            )
            or type(self.controlled_fixture) is not bool
        ):
            raise ValueError(
                "Explicit risk definition, assessment and validity references are required."
            )


@dataclass(frozen=True, slots=True)
class PlanningCommand:
    request: PlanningRequest
    risk_context: ExternalRiskContext | None


def create_procurement_plans(
    command: PlanningCommand, solver: AllocationSolver, *, time_limit_seconds: float = 30.0
) -> PlanningResult:
    if (
        not isinstance(command, PlanningCommand)
        or not isinstance(command.request, PlanningRequest)
        or (
            command.request.risk_coefficients is not None
            and not isinstance(command.risk_context, ExternalRiskContext)
        )
    ):
        return PlanningResult(
            PlanningStatus.INVALID_INPUT,
            explanations=(
                Explanation(
                    "risk_context_required",
                    "Supplied risk coefficients require explicit application-side context.",
                ),
            ),
        )
    return plan_procurement(command.request, solver, time_limit_seconds=time_limit_seconds)
