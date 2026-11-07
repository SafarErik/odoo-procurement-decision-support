"""Planning use-case entry point and the bridge from supplier assessments to MILP risk inputs.

No concrete solver, ERP, persistence or scikit-learn imports: the assessments arrive as
plain contract objects from ``supplier_evaluation.contracts``.
"""

from dataclasses import dataclass, replace
from datetime import datetime

from application.stored_contracts import (
    ASSESSMENTS_REFERENCE_PREFIX,
    VALIDITY_REFERENCE_PREFIX,
)
from decision_core.planning.models import (
    Explanation,
    PlanningRequest,
    PlanningResult,
    PlanningStatus,
    QuantityRange,
    RiskCoefficient,
)
from decision_core.planning.planner import (
    SOLVER_TIME_LIMIT_SECONDS,
    AllocationSolver,
    plan_procurement,
)
from decision_core.planning.rules import validate_risk
from supplier_evaluation.contracts import (
    HISTORY_MAPPING_VERSION,
    Assessment,
    digest,
    text_identity,
    utc,
)


@dataclass(frozen=True, slots=True)
class ExternalRiskContext:
    """Application-owned score definition and validity evidence, not calibration proof."""

    definition_reference: str
    assessment_reference: str
    validity_reference: str
    controlled_fixture: bool

    def __post_init__(self):
        for value in (
            self.definition_reference,
            self.assessment_reference,
            self.validity_reference,
        ):
            text_identity(value)
        if type(self.controlled_fixture) is not bool:
            raise ValueError("The controlled-fixture flag must be a bool.")


@dataclass(frozen=True, slots=True)
class PlanningCommand:
    request: PlanningRequest
    risk_context: ExternalRiskContext | None


def create_procurement_plans(
    command: PlanningCommand,
    solver: AllocationSolver,
    *,
    time_limit_seconds: float = SOLVER_TIME_LIMIT_SECONDS,
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


def risk_inputs(
    request: PlanningRequest,
    assessments: tuple[Assessment, ...],
    *,
    company_id: str,
    as_of: datetime,
) -> tuple[tuple[RiskCoefficient, ...], ExternalRiskContext]:
    """Turn one assessment per supplier into MILP risk coefficients and their evidence.

    Raises ValueError when an assessment is missing, mixes model versions, or does not
    cover the request's company, product, unit and dates; there is no zero-risk fallback.
    """
    utc(as_of)
    text_identity(company_id)
    if not isinstance(request, PlanningRequest) or request.risk_coefficients is not None:
        raise ValueError("Explicit planning input without preexisting risk coefficients required.")
    if (
        not isinstance(assessments, tuple)
        or not assessments
        or any(not isinstance(a, Assessment) for a in assessments)
    ):
        raise ValueError("Absent or invalid ML assessment; no zero-risk fallback.")
    ids = [a.snapshot.context.supplier_id for a in assessments]
    if len(set(ids)) != len(ids) or set(ids) != {s.supplier_id for s in request.suppliers}:
        raise ValueError("Complete exact supplier assessment join required.")
    if len({(a.model_id, a.training_id) for a in assessments}) != 1:
        raise ValueError("Mixed model/training versions are incompatible.")
    if len({a.mapping_version for a in assessments}) != 1:
        raise ValueError("Mixed assessment mappings are incompatible.")
    requirement = request.requirement
    for a in assessments:
        # Recheck contract at the consumption boundary, even for constructed assessments.
        a.__post_init__()
        if (
            a.snapshot.context.domain
            != (company_id, requirement.product_id, requirement.quantity_unit)
            or not a.snapshot.cutoff <= as_of < a.valid_until
            or not as_of.date() <= requirement.required_date < a.valid_until.date()
        ):
            raise ValueError("Risk assessment context or temporal validity mismatch.")
    ordered = sorted(assessments, key=lambda a: a.snapshot.context.supplier_id)
    coefficients = tuple(
        RiskCoefficient(
            a.snapshot.context.supplier_id,
            a.score,
            QuantityRange(a.quantities.minimum, a.quantities.maximum),
        )
        for a in ordered
    )
    validate_risk(replace(request, risk_coefficients=coefficients))
    context = ExternalRiskContext(
        f"docs/MODEL_ML.md#{HISTORY_MAPPING_VERSION}",
        ASSESSMENTS_REFERENCE_PREFIX + digest([a.reference for a in ordered]),
        VALIDITY_REFERENCE_PREFIX
        + digest(
            [
                (
                    a.quantities.reference,
                    a.quantities.minimum,
                    a.quantities.maximum,
                    a.snapshot.cutoff,
                    a.valid_until,
                )
                for a in ordered
            ]
        ),
        True,
    )
    return coefficients, context
