"""Exact JSON snapshot encoding and explicit T13/T14 stored-value reconstruction."""

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction

from decision_core.planning.models import (
    Allocation,
    AlternativeRun,
    Explanation,
    MinimumOrder,
    PlanningPolicy,
    PlanningRequest,
    PlanningResult,
    PlanningStatus,
    ProcurementPlan,
    ProcurementRequirement,
    QuantityRange,
    RiskCoefficient,
    SupplierTerms,
)
from supplier_evaluation.contracts import (
    Assessment,
    Context,
    FeatureSnapshot,
    PathStep,
    QuantityValidity,
    utc,
)


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if value == 0 else text


def json_value(value):
    if is_dataclass(value):
        return json_value(asdict(value))
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, datetime):
        utc(value)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def snapshot_json(value) -> str:
    return json.dumps(json_value(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_request(value: dict) -> PlanningRequest:
    r = value["requirement"]
    requirement = ProcurementRequirement(
        r["product_id"],
        r["approved_quantity"],
        r["quantity_unit"],
        r["currency"],
        date.fromisoformat(r["required_date"]),
    )
    suppliers = tuple(
        SupplierTerms(
            s["supplier_id"],
            s["product_id"],
            s["quantity_unit"],
            s["currency"],
            Decimal(s["unit_price"]),
            s["capacity"],
            s["available"],
            MinimumOrder(**s["minimum_order"]),
            QuantityRange(**s["price_quantities"]),
            QuantityRange(**s["delivery_quantities"]),
            date.fromisoformat(s["promised_date"]),
        )
        for s in value["suppliers"]
    )
    p = value["policy"]
    policy = PlanningPolicy(
        p["max_suppliers"],
        None if p["concentration_limit"] is None else Decimal(p["concentration_limit"]),
        tuple(Decimal(e) for e in p["epsilons"]),
    )
    risk = tuple(
        RiskCoefficient(
            c["supplier_id"], Decimal(c["value"]), QuantityRange(**c["valid_quantities"])
        )
        for c in value["risk_coefficients"]
    )
    return PlanningRequest(requirement, suppliers, policy, risk)


def read_assessments(values: list) -> tuple[Assessment, ...]:
    assessments = []
    for value in values:
        s = value["snapshot"]
        snapshot = FeatureSnapshot(
            Context(**s["context"]),
            *(
                datetime.fromisoformat(s[k])
                for k in ("cutoff", "history_start", "history_end", "evidence_available_at")
            ),
            tuple(s["values"]),
            s["source_type"],
            s["source_reference"],
            s["feature_version"],
            tuple(s["feature_names"]),
        )
        assessments.append(
            Assessment(
                snapshot,
                QuantityValidity(**value["quantities"]),
                datetime.fromisoformat(value["valid_until"]),
                value["predicted_class"],
                Decimal(value["score"]),
                value["model_id"],
                value["training_id"],
                value["leaf_id"],
                tuple(value["leaf_counts"]),
                tuple(PathStep(**p) for p in value["path"]),
                value["mapping_version"],
                value["dataset_version"],
                value["label_version"],
            )
        )
    return tuple(assessments)


def read_result(value: dict) -> PlanningResult:
    """Reconstruct recorded values, without recalculating any plan or objective."""

    def fraction(v):
        if (
            set(v) != {"numerator", "denominator"}
            or any(type(x) is not int for x in v.values())
            or v["denominator"] <= 0
        ):
            raise ValueError("Invalid stored rational.")
        return Fraction(v["numerator"], v["denominator"])

    def plan(v):
        allocations = tuple(Allocation(**a) for a in v["allocations"])
        cost = Decimal(v["total_cost"])
        exposure = None if v["risk_exposure"] is None else fraction(v["risk_exposure"])
        share, premium = fraction(v["largest_share"]), fraction(v["cost_premium"])
        if (
            not cost.is_finite()
            or cost <= 0
            or exposure is None
            or not 0 <= exposure <= 1
            or not 0 < share <= 1
            or premium < 0
            or type(v["supplier_count"]) is not int
            or v["supplier_count"] < 1
            or any(type(a.quantity) is not int or a.quantity < 0 for a in allocations)
        ):
            raise ValueError("Invalid stored plan quantities or metrics.")
        return ProcurementPlan(
            allocations,
            cost,
            exposure,
            share,
            v["supplier_count"],
            premium,
            tuple(Explanation(**e) for e in v["explanations"]),
        )

    minimum = None if value["minimum_cost_plan"] is None else plan(value["minimum_cost_plan"])
    alternatives = tuple(plan(p) for p in value["alternatives"])
    runs = tuple(
        AlternativeRun(
            Decimal(r["epsilon"]), PlanningStatus(r["status"]), r["plan_index"], r["code"]
        )
        for r in value["runs"]
    )
    status = PlanningStatus(value["status"])
    if status is PlanningStatus.INVALID_INPUT or (minimum is None and alternatives):
        raise ValueError("Invalid recorded planning result.")
    if (status is PlanningStatus.OPTIMAL and minimum is None) or (
        status is PlanningStatus.INFEASIBLE and minimum is not None
    ):
        raise ValueError("Stored proof status contradicts recorded plans.")
    if (minimum is None and runs) or (
        status is PlanningStatus.OPTIMAL
        and any(r.status is not PlanningStatus.OPTIMAL for r in runs)
    ):
        raise ValueError("Recorded stage proofs contradict the overall status.")
    for run in runs:
        if not run.epsilon.is_finite() or run.epsilon < 0:
            raise ValueError("Invalid recorded epsilon.")
        if run.status is PlanningStatus.OPTIMAL:
            if (
                minimum is None
                or type(run.plan_index) is not int
                or not 0 <= run.plan_index <= len(alternatives)
            ):
                raise ValueError("Invalid proved-plan reference.")
        elif run.plan_index is not None:
            raise ValueError("Unproven incumbent must not be stored as a plan.")
    return PlanningResult(
        status, minimum, alternatives, runs, tuple(Explanation(**e) for e in value["explanations"])
    )
