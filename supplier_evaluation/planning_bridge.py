"""Narrow T14-to-T13 contract adapter, without training, live assembly or orchestration."""

from dataclasses import replace
from datetime import datetime

from application.procurement_planning import ExternalRiskContext
from decision_core.planning.models import PlanningRequest, QuantityRange, RiskCoefficient
from decision_core.planning.rules import validate_risk
from supplier_evaluation.contracts import Assessment, digest, text_identity, utc


def risk_inputs(
    request: PlanningRequest,
    assessments: tuple[Assessment, ...],
    *,
    company_id: str,
    as_of: datetime,
) -> tuple[tuple[RiskCoefficient, ...], ExternalRiskContext]:
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
        f"docs/history/T14_ML_DESIGN.md#{assessments[0].mapping_version}",
        "t14-assessments:" + digest([a.reference for a in ordered]),
        "t14-quantity-independent-controlled-proxy:"
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
