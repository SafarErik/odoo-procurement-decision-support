"""Planning HTTP boundary and presentation; no local inference or optimization."""

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
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
    scenario_suppliers: list[dict[str, str]]
    comparison_rows: list[dict[str, str]]


FINAL_DECISION_CONFLICT = (
    "Decision conflict (HTTP 409). The case may already be finalized or the request key "
    "belongs to another intent. Reopen the recorded decision; do not approve again."
)


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
                "Save conflict (HTTP 409). This request key belongs to different inputs. "
                "Do not reuse it for changed inputs. Copy the exact request for support."
            ),
            422: (
                "Inputs rejected (HTTP 422). These inputs are outside the supported planning "
                "or model contract. Check "
                "quantity, terms and the matched saved model."
            ),
            413: "The prepared request exceeds the API size limit.",
        }
        if url.endswith("/from-odoo-history") and response.status_code in (409, 422, 503):
            code = response.json().get("detail", {}).get("code")
            history_errors = {
                "history_profile_changed": (
                    "The configured history profile changed. Reload its preview before saving."
                ),
                "odoo_history_unavailable": (
                    "Odoo history is missing, unavailable or does not match the configured source. "
                    "No case was saved."
                ),
                "odoo_history_model_incompatible": (
                    "The saved model is unavailable or incompatible with this Odoo history. "
                    "No case was saved."
                ),
            }
            if code in history_errors:
                return None, history_errors[code], False
        if response.status_code in errors:
            if url.endswith("/final-decision") and response.status_code in (409, 422):
                return (
                    None,
                    (
                        FINAL_DECISION_CONFLICT
                        if response.status_code == 409
                        else "Finalization was rejected (HTTP 422). Review the explicit plan, "
                        "actor, reason, saved hash and demo acknowledgement."
                    ),
                    False,
                )
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
        catalog = payload.get("catalog_context")
        if catalog is not None and (
            data.get("workspace") != catalog["workspace"]
            or data.get("example_id") != catalog.get("example_id")
        ):
            raise ValueError("Saved classification disagrees with creation intent")
        if url.endswith("/final-decision"):
            intent = dict(payload)
            intent["actor_reference"] = intent["actor_reference"].strip()
            intent["rationale"] = (intent.get("rationale") or "").strip() or None
            if (
                case_id != url.split("/")[-2]
                or data["final_decision"]["intent"] != intent
                or data["final_decision"]["idempotency_key"] != key
            ):
                raise ValueError("Final decision response does not match pending intent")
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
        if url.endswith("/from-odoo-history"):
            facts = data["snapshot"]["facts"]
            capture = json.loads(facts["history"])
            if (
                facts["input_kind"] != "odoo_quotations_odoo_history"
                or capture["evidence"]["profile"]["id"] != payload["profile_id"]
                or capture["evidence"]["profile_revision"] != payload["profile_revision"]
            ):
                raise ValueError("Unexpected Odoo history profile.")
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
                "The outcome is unconfirmed. The API may have saved the case or decision. "
                "Retry the "
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
            "Planning data is unavailable. Retry Load stored case when access returns. "
            "Opening only reads saved work. If it persists, give the case ID to the owner "
            "to check the FastAPI service and planning database.",
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
    if identity.startswith("odoo:res.partner:"):
        return "Supplier " + identity.removeprefix("odoo:res.partner:")
    return (
        "Demo supplier " + identity.removeprefix("synthetic-")
        if identity.startswith("synthetic-")
        else identity
    )


_BUYER_EXPLANATIONS = {
    "zero_in_optimal_plan": (
        "Not selected in this plan; this does not mean the supplier is excluded."
    ),
    "capacity_binding": "Uses all of this supplier's declared capacity.",
    "concentration_binding": "Reaches the maximum quantity allowed for one supplier.",
    "supplier_count_binding": "Uses the maximum allowed number of suppliers.",
    "unavailable": "Excluded: declared unavailable for this saved case.",
    "deadline_ineligible": "Excluded: the promised date is after the required date.",
    "no_valid_quantity": "Excluded: no positive quantity satisfies the recorded limits.",
    "moq_binding": "Reaches this supplier's minimum order quantity.",
    "price_lower_binding": "Reaches the lower quantity limit for the saved price.",
    "price_upper_binding": "Reaches the upper quantity limit for the saved price.",
    "delivery_lower_binding": "Reaches the lower quantity limit for the delivery promise.",
    "delivery_upper_binding": "Reaches the upper quantity limit for the delivery promise.",
    "integer_concentration_ceiling": "Reaches the whole-unit limit for one supplier's share.",
    "insufficient_effective_capacity": "The usable supplier quantities cannot cover demand.",
    "supplier_count_capacity_shortfall": (
        "Demand cannot be covered within the allowed number of suppliers."
    ),
}


def _explanation(entry: dict) -> str:
    return _BUYER_EXPLANATIONS.get(entry["code"], entry["detail"])


def _buyer_explanations(entries: list[dict]) -> str:
    return "\n".join(
        dict.fromkeys(
            ((_supplier_label(e["supplier_id"]) + ": ") if e["supplier_id"] else "")
            + _explanation(e)
            for e in entries
            if e["code"] in _BUYER_EXPLANATIONS
        )
    )


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
    status_labels = {
        "optimal": "Plans ready",
        "infeasible": "No feasible plan",
        "no_proven_optimum": "No proven optimum",
        "solver_error": "Solver unavailable",
        "invalid_input": "Input rejected",
    }
    if status not in status_labels:
        raise ValueError("Unknown planning status")
    kinds = {
        "controlled_synthetic": "Controlled synthetic inputs and ML history",
        "odoo_quotations_synthetic_history": "Captured Odoo quotations; synthetic ML history",
        "odoo_quotations_odoo_history": "Odoo quotations and receipts; controlled synthetic origin",
    }
    currency = _required_string(requirement, "currency")
    parent = payload["parent_id"]
    if parent is not None and str(UUID(parent)) != parent:
        raise ValueError("Invalid parent identity")
    scenario = snapshot["scenario"]
    base_quantity = facts["requirement"]["approved_quantity"]
    _integer(base_quantity)
    if base_quantity <= 0:
        raise ValueError("Invalid base quantity")
    scenario_suppliers = [
        {
            "supplier": _required_string(s["terms"], "supplier_id"),
            "name": _supplier_label(s["terms"]["supplier_id"]),
            "capacity": _integer(s["terms"]["capacity"]),
            "price": str(_decimal(s["terms"]["unit_price"])),
        }
        for s in facts["suppliers"]
    ]
    supplier_ids = {s["supplier"] for s in scenario_suppliers}
    if len(supplier_ids) != len(scenario_suppliers):
        raise ValueError("Duplicate base supplier")
    saved_suppliers = {s["supplier_id"]: s for s in request["suppliers"]}
    if len(saved_suppliers) != len(request["suppliers"]) or set(saved_suppliers) != supplier_ids:
        raise ValueError("Invalid saved supplier join")
    for row in scenario_suppliers:
        saved = saved_suppliers[row["supplier"]]
        row.update(
            saved_price=f"{_decimal(saved['unit_price']):,f}",
            saved_capacity=_integer(saved["capacity"]),
            saved_moq="None"
            if saved["minimum_order"]["quantity"] is None
            else _integer(saved["minimum_order"]["quantity"]),
            saved_date=_required_string(saved, "promised_date"),
            saved_available="Available" if saved["available"] else "Unavailable",
            saved_ranges=(
                f"Price {_integer(saved['price_quantities']['minimum'])}–"
                f"{_integer(saved['price_quantities']['maximum'])}; "
                f"delivery {_integer(saved['delivery_quantities']['minimum'])}–"
                f"{_integer(saved['delivery_quantities']['maximum'])}"
            ),
        )
    policy = request["policy"]
    concentration = policy["concentration_limit"]
    workspace = payload.get("workspace", "unclassified")
    workspace_label = {
        "practice": "Practice",
        "controlled": "Controlled work",
        "unclassified": "Earlier case · Unclassified",
    }[workspace]
    example_id = payload.get("example_id")
    if example_id is not None and (
        workspace != "practice" or not isinstance(example_id, str) or not 1 <= len(example_id) <= 80
    ):
        raise ValueError("Invalid saved example classification")
    details = {
        "workspace": workspace,
        "workspace_label": workspace_label,
        "example_id": example_id or "",
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
        "status_label": status_labels[status],
        "scenario_label": "Base case"
        if scenario is None
        else _required_string(scenario, "kind").replace("_", " ").capitalize(),
        "comparison": "",
        "comparison_display": "",
        "base_quantity": str(base_quantity),
        "base_status": "",
        "base_status_label": "",
        "scenario_status": status.replace("_", " "),
        "scenario_status_label": status_labels[status],
        "base_cost": "Not comparable",
        "scenario_cost": "No proven minimum-cost plan",
        "base_exposure": "Not comparable",
        "scenario_exposure": "Not comparable",
        "assumptions": "",
        "policy": (
            f"Maximum suppliers: {_integer(policy['max_suppliers'])}. "
            + (
                "No concentration limit. "
                if concentration is None
                else f"Maximum share per supplier: {_decimal(concentration) * 100:g}%. "
            )
            + "Alternative cost allowances: "
            + (", ".join(f"{_decimal(e) * 100:g}%" for e in policy["epsilons"]) or "none")
            + "."
        ),
        "alternative_notice": "",
        "chart_min_cost": "",
        "chart_max_cost": "",
        "product_label": "Product "
        + requirement["product_id"].removeprefix("odoo:product.product:")
        if requirement["product_id"].startswith("odoo:product.product:")
        else requirement["product_id"],
        "decision_summary": "",
        "explanations": "\n".join(f"{e['code']}: {e['detail']}" for e in result["explanations"]),
        "buyer_diagnostics": _buyer_explanations(result["explanations"]),
        "snapshot_json": json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False),
    }
    comparison = snapshot["comparison"]
    comparison_rows = []
    if comparison is not None:
        details["base_status"] = _required_string(comparison, "base_status").replace("_", " ")
        details["base_status_label"] = status_labels[comparison["base_status"]]
        delta = comparison["minimum_cost"]
        details["comparison"] = _required_string(comparison, "meaning")
        details["comparison_display"] = (
            "This scenario has no comparable proven minimum-cost plan. "
            "The original base case remains saved."
        )
        if delta is not None:
            cost_delta = _decimal(delta["total_cost_delta"])
            minimum = result["minimum_cost_plan"]
            details["scenario_cost"] = f"{_decimal(minimum['total_cost']):,f} {currency}"
            details["base_cost"] = f"{_decimal(minimum['total_cost']) - cost_delta:,f} {currency}"
            details["scenario_exposure"] = f"{_ratio(minimum['risk_exposure']) * 100:.1f} / 100"
            base_exposure = _ratio(minimum["risk_exposure"]) - _ratio(delta["risk_exposure_delta"])
            details["base_exposure"] = f"{base_exposure * 100:.1f} / 100"
            before, after = {}, {}
            for rows, target in (
                (delta["base_allocations"], before),
                (delta["scenario_allocations"], after),
            ):
                for row in rows:
                    identity = _required_string(row, "supplier_id")
                    _integer(row["quantity"])
                    if identity in target or row["quantity"] < 0:
                        raise ValueError("Invalid comparison allocation")
                    target[identity] = row["quantity"]
                if set(target) != supplier_ids:
                    raise ValueError("Invalid comparison supplier join")
            if sum(before.values()) != base_quantity or sum(after.values()) != quantity:
                raise ValueError("Invalid comparison quantity")
            if after != {a["supplier_id"]: a["quantity"] for a in minimum["allocations"]}:
                raise ValueError("Comparison differs from recorded plan")
            comparison_rows = [
                {
                    "name": _supplier_label(identity),
                    "base": str(before[identity]),
                    "scenario": str(after[identity]),
                    "change": f"{after[identity] - before[identity]:+d}",
                }
                for identity in sorted(supplier_ids)
            ]
            details["comparison_display"] = (
                f"Minimum cost changes by {cost_delta:+,f} {currency}. "
                f"Schedule-watch exposure changes by "
                f"{_ratio(delta['risk_exposure_delta']) * 100:+.1f} points on the 0–100 scale."
            )
            details["comparison"] += (
                f" Cost delta: {_decimal(delta['total_cost_delta']):,f} {currency}; "
                f"exposure delta: {_rational(delta['risk_exposure_delta'])}."
            )
        if base_quantity != quantity:
            details["comparison_display"] += (
                " Demand changed: these totals cover different quantities, "
                "not a like-for-like saving."
            )
    if scenario is not None:
        assumptions = []
        if scenario["approved_quantity"] is not None:
            assumptions.append(f"Demand: {scenario['approved_quantity']} ordered units")
        for change in scenario["suppliers"]:
            name = _supplier_label(_required_string(change, "supplier_id"))
            if change["available"] is False:
                assumptions.append(f"{name}: unavailable")
            if change["capacity"] is not None:
                assumptions.append(f"{name}: capacity {change['capacity']}")
            if change["unit_price"] is not None:
                assumptions.append(
                    f"{name}: price {_decimal(change['unit_price']):,f} {currency} per unit"
                )
        details["assumptions"] = "; ".join(assumptions)
        if facts.get("input_kind") == "odoo_quotations_synthetic_history":
            details["input_kind"] = (
                "Saved Odoo quotations with what-if changes; synthetic ML history"
            )
    plans, allocations = [], []
    minimum = result["minimum_cost_plan"]
    recorded = ([] if minimum is None else [minimum]) + result["alternatives"]
    if recorded:
        costs = [_decimal(p["total_cost"]) for p in recorded]
        if any(cost <= 0 for cost in costs):
            raise ValueError("Invalid recorded plan cost")
        low, high = min(costs), max(costs)
        details["chart_min_cost"] = f"{low:,f} {currency}"
        details["chart_max_cost"] = f"{high:,f} {currency}"
        if len(recorded) == 1:
            details["alternative_notice"] = (
                "Alternative search did not finish successfully. Only the proven minimum-cost "
                "plan is shown; this does not establish that no alternative exists."
                if status != "optimal"
                else "No distinct alternative was found within the recorded cost allowances."
                if policy["epsilons"]
                else "No alternatives were requested for this case."
            )
        else:
            alternative = min(recorded[1:], key=lambda p: _ratio(p["risk_exposure"]))
            reduction = (
                _ratio(minimum["risk_exposure"]) - _ratio(alternative["risk_exposure"])
            ) * 100
            additional_cost = _decimal(alternative["total_cost"]) - _decimal(minimum["total_cost"])
            change = (
                f"reduces simulated exposure by {reduction:.1f} points"
                if reduction > 0
                else f"changes simulated exposure by {-reduction:+.1f} points"
            )
            details["decision_summary"] = (
                f"The lowest-exposure saved alternative costs {additional_cost:,f} {currency} "
                f"more and {change}. Compare its supplier split before choosing a plan."
            )
    for index, plan in enumerate(recorded):
        label = "Minimum cost" if index == 0 else f"Alternative {index}"
        by_supplier = {}
        for allocation in plan["allocations"]:
            identity = _required_string(allocation, "supplier_id")
            _integer(allocation["quantity"])
            if identity in by_supplier or allocation["quantity"] < 0:
                raise ValueError("Invalid recorded allocation")
            by_supplier[identity] = allocation["quantity"]
        if set(by_supplier) != supplier_ids or sum(by_supplier.values()) != quantity:
            raise ValueError("Invalid recorded allocation supplier join or demand total")
        with localcontext() as context:
            context.prec = max(28, len(plan["total_cost"]) + len(minimum["total_cost"]))
            extra_cost = _decimal(plan["total_cost"]) - _decimal(minimum["total_cost"])
        exposure = _ratio(plan["risk_exposure"])
        if not 0 <= exposure <= 1:
            raise ValueError("Invalid recorded exposure")
        plans.append(
            {
                "label": label,
                "number": str(index + 1),
                "index": str(index),
                "chart_x": "50%"
                if high == low
                else f"{100 * (_decimal(plan['total_cost']) - low) / (high - low):.4f}%",
                "chart_y": f"{10 + 80 * (1 - exposure):.4f}%",
                "cost": f"{_decimal(plan['total_cost']):,f} {currency}",
                "cost_exact": plan["total_cost"],
                "exposure": _rational(plan["risk_exposure"]),
                "premium": _rational(plan["cost_premium"]),
                "premium_absolute": f"{extra_cost:+,f} {currency}",
                "premium_exact": (
                    f"{plan['cost_premium']['numerator']}/{plan['cost_premium']['denominator']}"
                ),
                "exposure_exact": (
                    f"{plan['risk_exposure']['numerator']}/{plan['risk_exposure']['denominator']}"
                ),
                "allocation_summary": "; ".join(
                    f"{_supplier_label(identity)}: {by_supplier[identity]} "
                    f"{requirement['quantity_unit']} (promised "
                    f"{saved_suppliers[identity]['promised_date']})"
                    for identity in sorted(by_supplier)
                    if by_supplier[identity] > 0
                ),
                "exposure_display": f"{_ratio(plan['risk_exposure']) * 100:.1f} / 100",
                "premium_display": "Minimum cost for these constraints"
                if index == 0
                else (
                    f"+{extra_cost:,f} "
                    f"{currency} (+{_ratio(plan['cost_premium']) * 100:.1f}%) above minimum"
                ),
                "buyer_notes": _buyer_explanations(plan["explanations"]),
                "explanations": "\n".join(
                    f"{e['supplier_id'] or 'Plan'} — {e['code']}: {e['detail']}"
                    for e in plan["explanations"]
                ),
            }
        )
        allocations.extend(
            {
                "plan": label,
                "supplier": identity,
                "quantity": str(by_supplier[identity]),
                "name": _supplier_label(identity),
                "promised": saved_suppliers[identity]["promised_date"],
                "share": f"{Decimal(by_supplier[identity]) / quantity * 100:.2f}",
            }
            for identity in sorted(by_supplier)
        )
    assessments = []
    for assessment in snapshot["assessments"]:
        feature = assessment["snapshot"]
        expected_source = (
            "odoo_projection"
            if facts.get("input_kind") == "odoo_quotations_odoo_history"
            else "t14_synthetic"
        )
        if feature["source_type"] != expected_source or facts["source_type"] != expected_source:
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
                "class_meaning": (
                    "Training label: at least two of five future synthetic receipts are late."
                    if predicted
                    else "Training label: fewer than two of five future synthetic receipts "
                    "are late."
                ),
                "reference_time": _parse_datetime(feature["cutoff"]).isoformat(),
                "score_display": f"{score * 100:.1f} / 100",
                "history_summary": (
                    f"{feature['values'][0]:g}% on time across "
                    f"{feature['values'][1]:g} "
                    + (
                        "completed purchase lines"
                        if expected_source == "odoo_projection"
                        else "completed receipts"
                    )
                ),
                "history_window": (
                    f"{feature['history_start'][:10]} to {feature['history_end'][:10]}"
                ),
                "class": _integer(assessment["predicted_class"]),
                "model": _required_string(assessment, "model_id"),
                "source": _required_string(feature, "source_reference"),
                "valid_until": _parse_datetime(assessment["valid_until"]).isoformat(),
                "quantity_range": (
                    f"{_integer(assessment['quantities']['minimum'])}–"
                    f"{_integer(assessment['quantities']['maximum'])} units"
                ),
                "path": "\n".join(
                    f"{step['feature']} = {step['value_float32']} "
                    f"{step['operator']} {step['threshold']}"
                    for step in assessment["path"]
                ),
                "readable_path": "\n".join(
                    f"{index + 1}. "
                    + (
                        f"On-time delivery ({step['value_float32']:.2f}%) "
                        f"is {'at most' if step['operator'] == '<=' else 'above'} "
                        f"{step['threshold']:.2f}%."
                        if step["feature"] == "delivery_schedule_adherence"
                        else f"Completed receipts ({step['value_float32']:g}) "
                        f"are {'at most' if step['operator'] == '<=' else 'above'} "
                        f"{step['threshold']:.2f}."
                        if step["feature"] == "historical_completed_count"
                        else f"{step['feature']}: {step['value_float32']} "
                        f"{step['operator']} {step['threshold']}."
                    )
                    for index, step in enumerate(assessment["path"])
                )
                or "The saved tree classifies at its root; no branch conditions were needed.",
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
    details.update(_final_decision_details(payload, recorded))
    return PlanningDisplay(
        details, plans, allocations, assessments, provenance, scenario_suppliers, comparison_rows
    )


def _final_decision_details(payload, plans):
    decision = payload.get("final_decision")
    details = {
        "final_outcome": "",
        "final_plan": "",
        "final_actor": "",
        "final_reason": "",
        "final_recorded_at": "",
        "final_content_hash": "",
        "final_audit": "",
    }
    if decision is None:
        return details
    intent, audit = decision["intent"], decision["audit"]
    if (
        payload["parent_id"] is not None
        or decision["decision_version"] != "t17-final-decision-v1"
        or decision["case_id"] != payload["case_id"]
        or intent["snapshot_hash"] != payload["snapshot_hash"]
        or intent["outcome"] not in {"approve", "no_award"}
        or intent["demonstration_acknowledged"] is not True
        or any(
            audit[k] != intent[k] for k in ("outcome", "plan_index", "actor_reference", "rationale")
        )
    ):
        raise ValueError("Unsupported final decision")
    content = decision["approved_content"]
    index = intent["plan_index"]
    if intent["outcome"] == "approve":
        if (
            type(index) is not int
            or not 0 <= index < len(plans)
            or content["content_version"] != "t17-approved-planning-v1"
            or content["case_id"] != payload["case_id"]
            or content["snapshot_hash"] != payload["snapshot_hash"]
            or content["plan_index"] != index
            or content["selected_plan"] != plans[index]
            or content["planning_snapshot"] != payload["snapshot"]
            or content["human_decision"] != audit
            or hashlib.sha256(
                json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
            != decision["approved_content_hash"]
        ):
            raise ValueError("Invalid approved content")
        details["final_plan"] = "Minimum cost" if index == 0 else f"Alternative {index}"
    elif index is not None or content is not None or decision["approved_content_hash"] is not None:
        raise ValueError("Invalid no-award content")
    else:
        details["final_plan"] = "None (No-award)"
    details.update(
        final_outcome="Approved" if intent["outcome"] == "approve" else "No-award",
        final_actor=_required_string(audit, "actor_reference"),
        final_reason=audit["rationale"] or "No reason required for minimum-cost approval",
        final_recorded_at=_parse_datetime(audit["recorded_at"]).isoformat(),
        final_content_hash=decision["approved_content_hash"] or "No approved content",
        final_audit=json.dumps(decision, indent=2, ensure_ascii=False),
    )
    return details
