"""Planning HTTP boundary and presentation; no local inference or optimization."""

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


async def submit_planning_request(
    url: str,
    payload: dict,
    key: str,
    token: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[PlanningDisplay | None, str, bool]:
    """One explicit POST. The caller retains exact intent for uncertain outcomes."""
    try:
        if str(UUID(key)) != key:
            raise ValueError("Invalid key")
    except (ValueError, TypeError, AttributeError):
        return None, "The request key is invalid. Prepare a new request.", False
    if not token or not token.isascii() or any(c.isspace() for c in token):
        return (
            None,
            "Planning access is not configured. Set the service token on the Reflex server.",
            False,
        )
    try:
        async with httpx.AsyncClient(
            timeout=45, transport=transport, follow_redirects=False
        ) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": key,
                },
            )
        errors = {
            401: "Planning access was rejected. Check the server-side service token.",
            403: "Planning access was rejected. Check the server-side service token.",
            404: "The base case was not found in this database. Load it again.",
            409: (
                "This request key belongs to different inputs. Do not reuse it for changed inputs."
            ),
            422: (
                "These inputs are outside the supported planning or model contract. Check "
                "quantity, terms and the matched saved model."
            ),
            413: "The prepared request exceeds the API size limit.",
        }
        if response.status_code in errors:
            if response.status_code == 422 and url.endswith("/from-odoo"):
                return (
                    None,
                    (
                        "Odoo quotations or planning terms no longer match the prepared inputs. "
                        "Review the terms and re-prepare changed quotations offline; check the "
                        "matching saved model."
                    ),
                    False,
                )
            return None, errors[response.status_code], False
        if response.status_code not in (200, 201):
            raise ValueError("Uncertain response")
        data = response.json()
        case_id = _required_string(data, "case_id")
        if str(UUID(case_id)) != case_id:
            raise ValueError("Invalid response identity")
        display = _map_case(data, case_id)
        if url.endswith("/scenarios") and display.details["parent_id"] != url.split("/")[-2]:
            raise ValueError("Unexpected parent")
        if not url.endswith("/scenarios") and data["parent_id"] is not None:
            raise ValueError("Unexpected base")
        if url.endswith("/from-odoo") and (
            data["snapshot"]["facts"]["input_kind"] != "odoo_quotations_synthetic_history"
            or data["snapshot"]["facts"]["comparison_case_id"]
            != f"odoo:purchase.order.group:{payload['purchase_group_id']}"
        ):
            raise ValueError("Unexpected Odoo comparison")
        return display, "", False
    except (
        httpx.HTTPError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        InvalidOperation,
        OverflowError,
    ):
        return (
            None,
            (
                "The outcome is unconfirmed. The API may have saved the case. Retry the "
                "same request to recover it; do not create a replacement."
            ),
            True,
        )


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


def _ratio(value: dict) -> Decimal:
    _rational(value)
    return Decimal(value["numerator"]) / Decimal(value["denominator"])


def _supplier_label(identity: str) -> str:
    return (
        "Demo supplier " + identity.removeprefix("synthetic-")
        if identity.startswith("synthetic-")
        else identity
    )


def _explanation(entry: dict) -> str:
    phrases = {
        "zero_in_optimal_plan": (
            "Not selected in this plan; this does not mean the supplier is excluded."
        ),
        "capacity_binding": "Uses all of this supplier's declared capacity.",
        "concentration_binding": "Reaches the maximum quantity allowed for one supplier.",
        "supplier_count_binding": "Uses the maximum allowed number of suppliers.",
    }
    return phrases.get(entry["code"], entry["detail"])


def _map_case(payload: dict, expected_id: str) -> PlanningDisplay:
    if _required_string(payload, "case_id") != expected_id:
        raise ValueError("Response identity mismatch")
    snapshot = payload["snapshot"]
    if snapshot["snapshot_version"] != "t15-controlled-planning-v1":
        raise ValueError("Unsupported snapshot version")
    facts, request, result = snapshot["facts"], snapshot["request"], snapshot["result"]
    requirement = request["requirement"]
    quantity = requirement["approved_quantity"]
    _integer(quantity)
    if quantity <= 0:
        raise ValueError("Invalid recorded demand")
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
        "base_id": parent or expected_id,
        "currency": currency,
        "status_label": {
            "optimal": "Plans ready",
            "infeasible": "No feasible plan",
            "no_proven_optimum": "No proven optimum",
            "solver_error": "Solver unavailable",
            "invalid_input": "Input rejected",
        }[status],
        "scenario_label": "Base case"
        if scenario is None
        else _required_string(scenario, "kind").replace("_", " ").capitalize(),
        "comparison": "",
        "comparison_display": "",
        "explanations": "\n".join(f"{e['code']}: {e['detail']}" for e in result["explanations"]),
    }
    comparison = snapshot["comparison"]
    if comparison is not None:
        delta = comparison["minimum_cost"]
        details["comparison"] = _required_string(comparison, "meaning")
        details["comparison_display"] = (
            "This scenario has no comparable proven minimum-cost plan. "
            "The original base case remains saved."
        )
        if delta is not None:
            cost_delta = _decimal(delta["total_cost_delta"])
            details["comparison_display"] = (
                f"Minimum cost changes by {cost_delta:+,f} {currency}. "
                f"Schedule-watch exposure changes by "
                f"{_ratio(delta['risk_exposure_delta']) * 100:+.1f} points on the 0–100 scale."
            )
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
                "exposure_display": f"{_ratio(plan['risk_exposure']) * 100:.1f} / 100",
                "premium_display": "Minimum cost for these constraints"
                if index == 0
                else (
                    f"+{_decimal(plan['total_cost']) - _decimal(minimum['total_cost']):,f} "
                    f"{currency} (+{_ratio(plan['cost_premium']) * 100:.1f}%) above minimum"
                ),
                "buyer_notes": "\n".join(
                    dict.fromkeys(
                        ((_supplier_label(e["supplier_id"]) + ": ") if e["supplier_id"] else "")
                        + _explanation(e)
                        for e in plan["explanations"]
                        if e["code"]
                        in {
                            "zero_in_optimal_plan",
                            "capacity_binding",
                            "concentration_binding",
                            "supplier_count_binding",
                        }
                    )
                ),
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
                "name": _supplier_label(a["supplier_id"]),
                "share": f"{Decimal(a['quantity']) / requirement['approved_quantity'] * 100:.2f}",
            }
            for a in plan["allocations"]
        )
    assessments = []
    for assessment in snapshot["assessments"]:
        feature = assessment["snapshot"]
        if feature["source_type"] != "t14_synthetic":
            raise ValueError("Unsupported ML source")
        predicted = assessment["predicted_class"]
        score = _decimal(assessment["score"])
        if type(predicted) is not int or predicted not in (0, 1) or not 0 <= score <= 1:
            raise ValueError("Unsupported assessment")
        assessments.append(
            {
                "supplier": _required_string(feature["context"], "supplier_id"),
                "score": str(_decimal(assessment["score"])),
                "name": _supplier_label(feature["context"]["supplier_id"]),
                "class_label": "Schedule watch" if predicted else "Schedule regular",
                "score_display": f"{score * 100:.1f} / 100",
                "history_summary": (
                    f"{feature['values'][0]:g}% on time across "
                    f"{feature['values'][1]:g} completed receipts"
                ),
                "history_window": (
                    f"{feature['history_start'][:10]} to {feature['history_end'][:10]}"
                ),
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
