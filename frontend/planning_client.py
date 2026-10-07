"""Stored-case HTTP client and display mapping; no planning or upstream access."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from uuid import UUID

import httpx

from frontend.rfq_client import _parse_datetime, _required_string


@dataclass(frozen=True, slots=True)
class PlanningDisplay:
    details: dict[str, str]
    plans: list[dict[str, str]]
    allocations: list[dict[str, str]]
    assessments: list[dict[str, str]]
    provenance: list[dict[str, str]]


async def fetch_planning_case(
    cases_url: str,
    case_id: str,
    token: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[PlanningDisplay | None, str]:
    """Issue one authenticated GET; never follow redirects or retry automatically."""
    try:
        if str(UUID(case_id)) != case_id:
            raise ValueError("Noncanonical identity")
    except (ValueError, TypeError, AttributeError):
        return None, "Enter a canonical planning case UUID from a completed run."
    if not token or not token.isascii() or any(c.isspace() for c in token):
        return (
            None,
            "Planning access is not configured. Set the service token on the Reflex server.",
        )
    try:
        async with httpx.AsyncClient(
            timeout=7.0, transport=transport, follow_redirects=False
        ) as client:
            response = await client.get(
                f"{cases_url.rstrip('/')}/{case_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 404:
                return None, "This planning case was not found. Check the UUID and database."
            if response.status_code in (401, 403):
                return None, "Planning access was rejected. Check the server-side service token."
            response.raise_for_status()
    except httpx.HTTPError:
        return (
            None,
            "Planning data is unavailable. Check the FastAPI service and planning database.",
        )
    try:
        return _map_case(response.json(), case_id), ""
    except (KeyError, TypeError, ValueError, AttributeError, InvalidOperation, OverflowError):
        return None, "The backend returned an unsupported or incomplete planning snapshot."


def _integer(value: object) -> str:
    if type(value) is not int:
        raise ValueError("Expected an integer")
    return str(value)


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Expected an exact decimal string")
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError("Expected a finite decimal")
    return number


def _rational(value: dict) -> str:
    numerator, denominator = value["numerator"], value["denominator"]
    _integer(numerator)
    _integer(denominator)
    if denominator <= 0:
        raise ValueError("Invalid recorded rational")
    return f"{numerator}/{denominator} ≈ {Decimal(numerator) / Decimal(denominator):.4f}"


def _map_case(payload: dict, expected_id: str) -> PlanningDisplay:
    if _required_string(payload, "case_id") != expected_id:
        raise ValueError("Response identity mismatch")
    snapshot = payload["snapshot"]
    if snapshot["snapshot_version"] != "t15-controlled-planning-v1":
        raise ValueError("Unsupported snapshot version")
    facts, request, result = snapshot["facts"], snapshot["request"], snapshot["result"]
    requirement = request["requirement"]
    status = _required_string(result, "status")
    if status not in {
        "optimal",
        "infeasible",
        "no_proven_optimum",
        "solver_error",
        "invalid_input",
    }:
        raise ValueError("Unknown planning status")
    kinds = {
        "controlled_synthetic": "Controlled synthetic inputs and ML history",
        "odoo_quotations_synthetic_history": "Live Odoo quotations; synthetic ML history",
    }
    currency = _required_string(requirement, "currency")
    parent = payload["parent_id"]
    if parent is not None and str(UUID(parent)) != parent:
        raise ValueError("Invalid parent identity")
    scenario = snapshot["scenario"]
    details = {
        "case_id": expected_id,
        "parent_id": parent or "Base case",
        "created_at": _parse_datetime(payload["created_at"]).isoformat(),
        "snapshot_hash": _required_string(payload, "snapshot_hash"),
        "status": status.replace("_", " "),
        "input_kind": kinds[facts.get("input_kind", "controlled_synthetic")],
        "company": _required_string(facts, "company_id"),
        "product": _required_string(requirement, "product_id"),
        "quantity": _integer(requirement["approved_quantity"]),
        "unit": _required_string(requirement, "quantity_unit"),
        "required_date": _required_string(requirement, "required_date"),
        "as_of": _parse_datetime(facts["as_of"]).isoformat(),
        "scenario": "Base case" if scenario is None else _required_string(scenario, "kind"),
        "comparison": "",
        "explanations": "\n".join(f"{e['code']}: {e['detail']}" for e in result["explanations"]),
    }
    comparison = snapshot["comparison"]
    if comparison is not None:
        delta = comparison["minimum_cost"]
        details["comparison"] = _required_string(comparison, "meaning")
        if delta is not None:
            details["comparison"] += (
                f" Cost delta: {_decimal(delta['total_cost_delta']):,f} {currency}; "
                f"exposure delta: {_rational(delta['risk_exposure_delta'])}."
            )
    plans, allocations = [], []
    minimum = result["minimum_cost_plan"]
    recorded = ([] if minimum is None else [minimum]) + result["alternatives"]
    for index, plan in enumerate(recorded):
        label = "Minimum cost" if index == 0 else f"Alternative {index}"
        plans.append(
            {
                "label": label,
                "cost": f"{_decimal(plan['total_cost']):,f} {currency}",
                "exposure": _rational(plan["risk_exposure"]),
                "premium": _rational(plan["cost_premium"]),
                "explanations": "\n".join(
                    f"{e['supplier_id'] or 'Plan'} — {e['code']}: {e['detail']}"
                    for e in plan["explanations"]
                ),
            }
        )
        allocations.extend(
            {
                "plan": label,
                "supplier": _required_string(a, "supplier_id"),
                "quantity": _integer(a["quantity"]),
            }
            for a in plan["allocations"]
        )
    assessments = []
    for assessment in snapshot["assessments"]:
        feature = assessment["snapshot"]
        if feature["source_type"] != "t14_synthetic":
            raise ValueError("Unsupported ML source")
        assessments.append(
            {
                "supplier": _required_string(feature["context"], "supplier_id"),
                "score": str(_decimal(assessment["score"])),
                "class": _integer(assessment["predicted_class"]),
                "model": _required_string(assessment, "model_id"),
                "source": _required_string(feature, "source_reference"),
                "valid_until": _parse_datetime(assessment["valid_until"]).isoformat(),
                "path": "\n".join(
                    f"{step['feature']} = {step['value_float32']} "
                    f"{step['operator']} {step['threshold']}"
                    for step in assessment["path"]
                ),
            }
        )
    provenance = [
        {
            "field": _required_string(entry, "canonical_path"),
            "type": _required_string(entry, "source_type"),
            "reference": _required_string(entry, "source_reference"),
            "observed_at": _parse_datetime(entry["observed_at"]).isoformat(),
        }
        for entry in snapshot["provenance"]["entries"]
    ]
    return PlanningDisplay(details, plans, allocations, assessments, provenance)
