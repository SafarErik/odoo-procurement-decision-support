"""Planning HTTP boundary and presentation; no local inference or optimization."""

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, localcontext
from uuid import UUID

import httpx

from frontend.i18n import day, moment, money, number, percent, tr, unit
from frontend.parsing import parse_datetime as _parse_datetime
from frontend.parsing import required_string as _required_string


@dataclass(frozen=True, slots=True)
class PlanningDisplay:
    details: dict[str, str]
    plans: list[dict[str, str]]
    allocations: list[dict[str, str]]
    assessments: list[dict[str, str]]
    provenance: list[dict[str, str]]
    scenario_suppliers: list[dict[str, str]]
    comparison_rows: list[dict[str, str]]
    # The validated API payload, kept so a language switch re-labels without a new request.
    raw: dict = field(default_factory=dict, compare=False)


# Stable marker the state compares against; the shown text is localized separately.
FINAL_DECISION_CONFLICT = "decision_conflict"


async def submit_planning_request(
    url: str,
    payload: dict,
    key: str,
    token: str,
    *,
    lang: str = "en",
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[PlanningDisplay | None, str, bool]:
    """One explicit POST. The caller retains exact intent for uncertain outcomes."""
    try:
        if str(UUID(key)) != key:
            raise ValueError("Invalid key")
    except (ValueError, TypeError, AttributeError):
        return None, tr("err_key", lang), False
    if not token or not token.isascii() or any(c.isspace() for c in token):
        return None, tr("err_token", lang), False
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
            401: "err_rejected",
            403: "err_rejected",
            404: "err_base_missing",
            409: "err_key_conflict",
            422: "err_rejected_inputs",
            413: "err_too_large",
        }
        if url.endswith("/from-odoo-history") and response.status_code in (409, 422, 503):
            code = response.json().get("detail", {}).get("code")
            history_errors = {
                "odoo_history_insufficient": "err_history_insufficient",
                "odoo_history_unavailable": "err_history_unavailable",
                "odoo_history_model_incompatible": "err_history_model",
            }
            if code in history_errors:
                return None, tr(history_errors[code], lang), False
        if response.status_code in errors:
            if url.endswith("/final-decision") and response.status_code in (409, 422):
                return (
                    None,
                    FINAL_DECISION_CONFLICT
                    if response.status_code == 409
                    else tr("err_decision_rejected", lang),
                    False,
                )
            if response.status_code == 422 and url.endswith("/from-odoo-history"):
                return None, tr("err_odoo_changed", lang), False
            return None, tr(errors[response.status_code], lang), False
        if response.status_code not in (200, 201):
            raise ValueError("Uncertain response")
        data = response.json()
        case_id = _required_string(data, "case_id")
        if str(UUID(case_id)) != case_id:
            raise ValueError("Invalid response identity")
        display = _map_case(data, case_id, lang)
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
        if url.endswith("/from-odoo-history"):
            facts = data["snapshot"]["facts"]
            capture = json.loads(facts["history"])
            if (
                facts["input_kind"] != "odoo_quotations_odoo_history"
                or facts["comparison_case_id"]
                != f"odoo:purchase.order.group:{payload['purchase_group_id']}"
                or capture["evidence"]["version"] != "odoo-purchase-history-capture-v2"
            ):
                raise ValueError("Unexpected Odoo history capture.")
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
        return None, tr("err_uncertain", lang), True


async def fetch_planning_case(
    cases_url: str,
    case_id: str,
    token: str,
    *,
    lang: str = "en",
    transport: httpx.AsyncBaseTransport | None = None,
) -> tuple[PlanningDisplay | None, str]:
    """Issue one authenticated GET; never follow redirects or retry automatically."""
    try:
        if str(UUID(case_id)) != case_id:
            raise ValueError("Noncanonical identity")
    except (ValueError, TypeError, AttributeError):
        return None, tr("err_case_id", lang)
    if not token or not token.isascii() or any(c.isspace() for c in token):
        return None, tr("err_token", lang)
    try:
        async with httpx.AsyncClient(
            timeout=7.0, transport=transport, follow_redirects=False
        ) as client:
            response = await client.get(
                f"{cases_url.rstrip('/')}/{case_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 404:
                return None, tr("err_case_missing", lang)
            if response.status_code in (401, 403):
                return None, tr("err_rejected", lang)
            response.raise_for_status()
    except httpx.HTTPError:
        return None, tr("err_case_unavailable", lang)
    try:
        return _map_case(response.json(), case_id, lang), ""
    except (KeyError, TypeError, ValueError, AttributeError, InvalidOperation, OverflowError):
        return None, tr("err_case_invalid", lang)


def _integer(value: object) -> str:
    if type(value) is not int:
        raise ValueError("Expected an integer")
    return str(value)


def _decimal(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Expected an exact decimal string")
    number_ = Decimal(value)
    if not number_.is_finite():
        raise ValueError("Expected a finite decimal")
    return number_


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


def _supplier_label(identity: str, lang: str = "en", names: dict | None = None) -> str:
    """Odoo display name when stored, otherwise a readable label for the identity."""
    if names and names.get(identity):
        return names[identity]
    if identity.startswith("odoo:res.partner:"):
        return tr("supplier_n", lang, n=identity.removeprefix("odoo:res.partner:"))
    if identity.startswith("synthetic-"):
        return tr("demo_supplier", lang, n=identity.removeprefix("synthetic-"))
    return identity


def _product_label(identity: str, lang: str, names: dict) -> str:
    if names.get(identity):
        return names[identity]
    if identity.startswith("odoo:product.product:"):
        return tr("product_n", lang, n=identity.removeprefix("odoo:product.product:"))
    return identity


def _unit_label(identity: str, lang: str, names: dict) -> str:
    if names.get(identity):
        return unit(names[identity], lang)
    return unit("Units" if identity.startswith("odoo:uom.uom:") else identity, lang)


def _explanation(entry: dict, lang: str) -> str | None:
    key = "why_" + entry["code"]
    return None if key not in _WHY else tr(key, lang)


_WHY = {
    "why_" + code
    for code in (
        "zero_in_optimal_plan",
        "capacity_binding",
        "concentration_binding",
        "supplier_count_binding",
        "unavailable",
        "deadline_ineligible",
        "no_valid_quantity",
        "moq_binding",
        "price_lower_binding",
        "price_upper_binding",
        "delivery_lower_binding",
        "delivery_upper_binding",
        "integer_concentration_ceiling",
        "insufficient_effective_capacity",
        "supplier_count_capacity_shortfall",
    )
}


def _buyer_explanations(entries: list[dict], lang: str = "en", names: dict | None = None) -> str:
    return "\n".join(
        dict.fromkeys(
            ((_supplier_label(e["supplier_id"], lang, names) + ": ") if e["supplier_id"] else "")
            + text
            for e in entries
            if (text := _explanation(e, lang)) is not None
        )
    )


_HISTORY_STEPS = {
    "on_time_rate": ("Határidőre teljesített szállítások aránya", "On-time delivery rate", "pct"),
    "mean_lateness_days": ("Átlagos késés", "Average lateness", "days"),
    "lateness_spread_days": ("Késés szórása", "Lateness spread", "days"),
    "fill_rate": ("Mennyiségi teljesítési arány", "Fill rate", "pct"),
    "partial_share": ("Részszállítások aránya", "Share of partial deliveries", "pct"),
    "order_count": ("Lezárt beszerzési sorok", "Settled purchase lines", "int"),
    "days_since_last_receipt": ("Napok az utolsó átvétel óta", "Days since last receipt", "int"),
    "delivery_schedule_adherence": ("Határidőre teljesítés", "On-time delivery", "percent100"),
    "historical_completed_count": ("Teljesített átvételek", "Completed receipts", "int"),
}


def _metric(kind: str, value, lang: str) -> str:
    if kind == "pct":
        return percent(value, lang)
    if kind == "percent100":
        return percent(Decimal(str(value)) / 100, lang, 2)
    if kind == "days":
        return tr("days", lang, value=number(value, lang, 1))
    return number(value, lang, 0)


def _history_step(step, lang: str = "en") -> str:
    """Readable condition for a tree split (stored values only)."""
    hu, en, kind = _HISTORY_STEPS.get(step["feature"], (step["feature"], step["feature"], "num"))
    name = hu if lang == "hu" else en
    if kind == "num":
        value, threshold = str(step["value_float32"]), str(step["threshold"])
    else:
        value = _metric(kind, step["value_float32"], lang)
        threshold = (
            number(step["threshold"], lang, 2)
            if kind == "int" and step["threshold"] % 1
            else _metric(kind, step["threshold"], lang)
        )
        if value == threshold:  # rounding hid the difference; show the stored values
            value, threshold = f"{step['value_float32']:.4f}", f"{step['threshold']:.4f}"
    if lang == "hu":
        relation = "legfeljebb" if step["operator"] == "<=" else "több mint"
        return f"{name}: {value} – {relation} {threshold}."
    relation = "is at most" if step["operator"] == "<=" else "is above"
    return f"{name} ({value}) {relation} {threshold}."


def _data_origin(snapshot: dict) -> str:
    """Same rule as the PDF: generated/observed Odoo history, or the synthetic demo model."""
    if snapshot["facts"].get("input_kind") != "odoo_quotations_odoo_history":
        return "synthetic"
    origin = snapshot.get("model_manifest", {}).get("metadata", {}).get("data_origin")
    return origin if origin in ("generated", "observed") else "generated"


def _map_case(payload: dict, expected_id: str, lang: str = "en") -> PlanningDisplay:
    if _required_string(payload, "case_id") != expected_id:
        raise ValueError("Response identity mismatch")
    snapshot = payload["snapshot"]
    if snapshot["snapshot_version"] != "t15-controlled-planning-v1":
        raise ValueError("Unsupported snapshot version")
    facts, request, result = snapshot["facts"], snapshot["request"], snapshot["result"]
    names = {key: value for key, value in facts.get("labels", ())}
    requirement = request["requirement"]
    quantity = requirement["approved_quantity"]
    _integer(quantity)
    if quantity <= 0:
        raise ValueError("Invalid recorded demand")
    status = _required_string(result, "status")
    if status not in (
        "optimal",
        "infeasible",
        "no_proven_optimum",
        "solver_error",
        "invalid_input",
    ):
        raise ValueError("Unknown planning status")
    kinds = {
        "controlled_synthetic": "Controlled synthetic inputs and ML history",
        "odoo_quotations_synthetic_history": "Captured Odoo quotations; synthetic ML history",
        "odoo_quotations_odoo_history": "Odoo quotations and Odoo purchase history",
    }
    currency = _required_string(requirement, "currency")
    unit_name = _unit_label(_required_string(requirement, "quantity_unit"), lang, names)
    parent = payload["parent_id"]
    if parent is not None and str(UUID(parent)) != parent:
        raise ValueError("Invalid parent identity")
    scenario = snapshot["scenario"]
    base_quantity = facts["requirement"]["approved_quantity"]
    _integer(base_quantity)
    if base_quantity <= 0:
        raise ValueError("Invalid base quantity")

    def name(identity):
        return _supplier_label(identity, lang, names)

    def amount(value, signed=False):
        return money(value, currency, lang, signed=signed)

    def pieces(value):
        return tr("pieces", lang, quantity=number(value, lang), unit=unit_name)

    scenario_suppliers = [
        {
            "supplier": _required_string(s["terms"], "supplier_id"),
            "name": name(s["terms"]["supplier_id"]),
            "capacity": _integer(s["terms"]["capacity"]),
            "price": str(_decimal(s["terms"]["unit_price"])),
            "price_display": amount(_decimal(s["terms"]["unit_price"])),
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
            saved_price=amount(_decimal(saved["unit_price"])),
            saved_capacity=_integer(saved["capacity"]),
            saved_moq=tr("none", lang)
            if saved["minimum_order"]["quantity"] is None
            else _integer(saved["minimum_order"]["quantity"]),
            saved_date=day(_required_string(saved, "promised_date"), lang),
            saved_available=tr("available" if saved["available"] else "not_available", lang),
            saved_ranges=(
                f"{_integer(saved['price_quantities']['minimum'])}–"
                f"{_integer(saved['price_quantities']['maximum'])} / "
                f"{_integer(saved['delivery_quantities']['minimum'])}–"
                f"{_integer(saved['delivery_quantities']['maximum'])}"
            ),
        )
    policy = request["policy"]
    concentration = policy["concentration_limit"]
    origin = payload["origin"]
    data_origin = _data_origin(snapshot)
    status_label = tr("status_" + status, lang)
    details = {
        "origin": origin,
        "data_origin": data_origin,
        "origin_badge": ""
        if data_origin == "observed"
        else tr("badge_generated" if data_origin == "generated" else "badge_synthetic", lang),
        "origin_note": ""
        if data_origin == "observed"
        else tr("generated_note" if data_origin == "generated" else "synthetic_note", lang),
        "case_id": expected_id,
        "parent_id": parent or "Base case",
        "created_at": _parse_datetime(payload["created_at"]).isoformat(),
        "created_display": moment(payload["created_at"], lang),
        "snapshot_hash": _required_string(payload, "snapshot_hash"),
        "status": status.replace("_", " "),
        "status_code": status,
        "input_kind": kinds[facts.get("input_kind", "controlled_synthetic")],
        "company": _required_string(facts, "company_id"),
        "product": _required_string(requirement, "product_id"),
        "quantity": _integer(requirement["approved_quantity"]),
        "quantity_display": pieces(quantity),
        "unit": _required_string(requirement, "quantity_unit"),
        "unit_label": unit_name,
        "required_date": _required_string(requirement, "required_date"),
        "required_display": day(requirement["required_date"], lang),
        "as_of": _parse_datetime(facts["as_of"]).isoformat(),
        "as_of_display": moment(facts["as_of"], lang),
        "scenario": "Base case" if scenario is None else _required_string(scenario, "kind"),
        "base_id": parent or expected_id,
        "currency": currency,
        "status_label": status_label,
        "scenario_label": "" if scenario is None else tr("kind_" + scenario["kind"], lang),
        "comparison": "",
        "comparison_display": "",
        "base_quantity": str(base_quantity),
        "base_quantity_display": pieces(base_quantity),
        "base_status": "",
        "base_status_label": "",
        "scenario_status": status.replace("_", " "),
        "scenario_status_label": status_label,
        "assumptions": "",
        "policy": tr(
            "policy_text",
            lang,
            suppliers=_integer(policy["max_suppliers"]),
            share=tr("policy_no_share", lang)
            if concentration is None
            else percent(_decimal(concentration), lang, 0),
            allowance=", ".join(percent(_decimal(e), lang, 0) for e in policy["epsilons"])
            or tr("none", lang),
        ),
        "alternative_notice": "",
        "product_label": _product_label(requirement["product_id"], lang, names),
        "decision_summary": "",
        "min_cost_display": "",
        "plan_count": "0",
        "explanations": "\n".join(f"{e['code']}: {e['detail']}" for e in result["explanations"]),
        "buyer_diagnostics": _buyer_explanations(result["explanations"], lang, names),
        "snapshot_json": json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False),
    }
    comparison = snapshot["comparison"]
    comparison_rows = []
    if comparison is not None:
        details["base_status"] = _required_string(comparison, "base_status").replace("_", " ")
        details["base_status_label"] = tr("status_" + comparison["base_status"], lang)
        delta = comparison["minimum_cost"]
        details["comparison"] = _required_string(comparison, "meaning")
        if delta is not None:
            cost_delta = _decimal(delta["total_cost_delta"])
            minimum = result["minimum_cost_plan"]
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
                    "name": name(identity),
                    "base": str(before[identity]),
                    "scenario": str(after[identity]),
                    "change": f"{after[identity] - before[identity]:+d}",
                }
                for identity in sorted(supplier_ids)
            ]
            details["comparison"] += (
                f" Cost delta: {cost_delta:,f} {currency}; "
                f"exposure delta: {_rational(delta['risk_exposure_delta'])}."
            )
    if scenario is not None:
        assumptions = []
        if scenario["approved_quantity"] is not None:
            assumptions.append(
                tr("assume_demand", lang, quantity=pieces(scenario["approved_quantity"]))
            )
        for change in scenario["suppliers"]:
            supplier = name(_required_string(change, "supplier_id"))
            if change["available"] is False:
                assumptions.append(tr("assume_outage", lang, name=supplier))
            if change["capacity"] is not None:
                assumptions.append(
                    tr("assume_capacity", lang, name=supplier, quantity=pieces(change["capacity"]))
                )
            if change["unit_price"] is not None:
                assumptions.append(
                    tr(
                        "assume_price",
                        lang,
                        name=supplier,
                        price=amount(_decimal(change["unit_price"])),
                    )
                )
        details["assumptions"] = "; ".join(assumptions)
        if facts.get("input_kind") == "odoo_quotations_synthetic_history":
            details["input_kind"] = (
                "Saved Odoo quotations with what-if changes; synthetic ML history"
            )
    plans, allocations = [], []
    minimum = result["minimum_cost_plan"]
    recorded = ([] if minimum is None else [minimum]) + result["alternatives"]
    details["plan_count"] = str(len(recorded))
    if recorded:
        costs = [_decimal(p["total_cost"]) for p in recorded]
        if any(cost <= 0 for cost in costs):
            raise ValueError("Invalid recorded plan cost")
        details["min_cost_display"] = amount(costs[0])
        if len(recorded) == 1:
            details["alternative_notice"] = tr(
                "no_alternative_failed"
                if status != "optimal"
                else "no_alternative_found"
                if policy["epsilons"]
                else "no_alternative_requested",
                lang,
            )
        else:
            alternative = min(recorded[1:], key=lambda p: _ratio(p["risk_exposure"]))
            reduction = (
                _ratio(minimum["risk_exposure"]) - _ratio(alternative["risk_exposure"])
            ) * 100
            additional_cost = _decimal(alternative["total_cost"]) - _decimal(minimum["total_cost"])
            details["decision_summary"] = tr(
                "tradeoff_summary" if reduction > 0 else "tradeoff_summary_up",
                lang,
                amount=amount(additional_cost),
                points=number(abs(reduction) if reduction > 0 else -reduction, lang, 1),
            )
    lowest = min(
        range(len(recorded)), key=lambda i: _ratio(recorded[i]["risk_exposure"]), default=0
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
        used = [i for i in sorted(by_supplier) if by_supplier[i] > 0]
        plans.append(
            {
                "label": label,
                "title": tr("plan_minimum", lang)
                if index == 0
                else tr("plan_alternative", lang, n=index),
                "hint": tr("plan_lower_risk", lang) if index == lowest and index else "",
                "number": str(index + 1),
                "index": str(index),
                "cost": amount(_decimal(plan["total_cost"])),
                "cost_exact": plan["total_cost"],
                "cost_number": f"{_decimal(plan['total_cost']):f}",
                "exposure": _rational(plan["risk_exposure"]),
                "exposure_number": f"{exposure * 100:.1f}",
                "premium": _rational(plan["cost_premium"]),
                "premium_absolute": amount(extra_cost, signed=True),
                "premium_exact": (
                    f"{plan['cost_premium']['numerator']}/{plan['cost_premium']['denominator']}"
                ),
                "exposure_exact": (
                    f"{plan['risk_exposure']['numerator']}/{plan['risk_exposure']['denominator']}"
                ),
                "supplier_count": str(len(used)),
                "allocation_summary": "; ".join(
                    f"{name(identity)}: {pieces(by_supplier[identity])}" for identity in used
                ),
                "exposure_display": tr(
                    "exposure_value", lang, value=number(exposure * 100, lang, 1)
                ),
                "premium_display": tr("minimum_for_limits", lang)
                if index == 0
                else tr(
                    "above_minimum",
                    lang,
                    amount=f"{amount(extra_cost, signed=True)} "
                    f"({percent(_ratio(plan['cost_premium']), lang)})",
                ),
                "buyer_notes": _buyer_explanations(plan["explanations"], lang, names),
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
                "quantity_display": pieces(by_supplier[identity]),
                "name": name(identity),
                "promised": day(saved_suppliers[identity]["promised_date"], lang),
                "share": f"{Decimal(by_supplier[identity]) / quantity * 100:.2f}",
                "share_display": percent(Decimal(by_supplier[identity]) / quantity, lang, 0),
            }
            for identity in sorted(by_supplier)
        )
    if comparison is not None and comparison["minimum_cost"] is not None and plans:
        delta = comparison["minimum_cost"]
        details["comparison_display"] = tr(
            "scenario_delta",
            lang,
            amount=amount(_decimal(delta["total_cost_delta"]), signed=True),
            points=number(_ratio(delta["risk_exposure_delta"]) * 100, lang, 1),
        )
    elif comparison is not None:
        details["comparison_display"] = tr("scenario_no_plan", lang)
    if comparison is not None and base_quantity != quantity:
        details["comparison_display"] += " " + tr("scenario_demand_changed", lang)
    assessments = []
    history = facts.get("input_kind") == "odoo_quotations_odoo_history"
    for assessment in snapshot["assessments"]:
        feature = assessment["snapshot"]
        expected_source = "odoo_purchase_history" if history else "t14_synthetic"
        if feature["source_type"] != expected_source or facts["source_type"] != expected_source:
            raise ValueError("Unsupported ML source")
        predicted = assessment["predicted_class"]
        score = _decimal(assessment["score"])
        if type(predicted) is not int or predicted not in (0, 1) or not 0 <= score <= 1:
            raise ValueError("Unsupported assessment")
        values = feature["values"]
        class_key = (
            ("problematic" if predicted else "regular")
            if history
            else ("schedule_watch" if predicted else "schedule_regular")
        )
        assessments.append(
            {
                "supplier": _required_string(feature["context"], "supplier_id"),
                "score": str(_decimal(assessment["score"])),
                "name": name(feature["context"]["supplier_id"]),
                "class_key": class_key,
                "class_label": tr("class_" + class_key, lang),
                "class_meaning": tr(
                    "class_meaning_history" if history else "class_meaning_synthetic", lang
                ),
                "reference_time": _parse_datetime(feature["cutoff"]).isoformat(),
                "score_display": tr("exposure_value", lang, value=number(score * 100, lang, 1)),
                "history_summary": (
                    tr(
                        "history_summary",
                        lang,
                        on_time=percent(values[0], lang, 0),
                        late=tr("days", lang, value=number(values[1], lang, 1)),
                        fill=percent(values[3], lang, 0),
                        lines=number(values[5], lang, 0),
                    )
                    if history
                    else tr(
                        "history_summary_synthetic",
                        lang,
                        on_time=percent(Decimal(str(values[0])) / 100, lang, 0),
                        receipts=number(values[1], lang, 0),
                    )
                ),
                "history_window": (
                    f"{day(feature['history_start'], lang)} – {day(feature['history_end'], lang)}"
                ),
                "class": _integer(assessment["predicted_class"]),
                "model": _required_string(assessment, "model_id"),
                "source": _required_string(feature, "source_reference"),
                "valid_until": _parse_datetime(assessment["valid_until"]).isoformat(),
                "quantity_range": (
                    f"{_integer(assessment['quantities']['minimum'])}–"
                    f"{_integer(assessment['quantities']['maximum'])} {unit_name}"
                ),
                "path": "\n".join(
                    f"{step['feature']} = {step['value_float32']} "
                    f"{step['operator']} {step['threshold']}"
                    for step in assessment["path"]
                ),
                "readable_path": "\n".join(
                    f"{index + 1}. {_history_step(step, lang)}"
                    for index, step in enumerate(assessment["path"])
                )
                or tr("path_root", lang),
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
    details.update(_final_decision_details(payload, recorded, lang))
    return PlanningDisplay(
        details,
        plans,
        allocations,
        assessments,
        provenance,
        scenario_suppliers,
        comparison_rows,
        payload,
    )


def _final_decision_details(payload, plans, lang="en"):
    decision = payload.get("final_decision")
    details = {
        "final_outcome": "",
        "final_outcome_label": tr("decision_draft", lang)
        if payload["parent_id"] is None
        else tr("decision_scenario", lang),
        "final_plan": "",
        "final_plan_title": "",
        "final_actor": "",
        "final_reason": "",
        "final_recorded_at": "",
        "final_recorded_display": "",
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
        details["final_plan_title"] = (
            tr("plan_minimum", lang) if index == 0 else tr("plan_alternative", lang, n=index)
        )
    elif index is not None or content is not None or decision["approved_content_hash"] is not None:
        raise ValueError("Invalid no-award content")
    else:
        details["final_plan"] = "None (No-award)"
        details["final_plan_title"] = tr("decision_no_award", lang)
    details.update(
        final_outcome="Approved" if intent["outcome"] == "approve" else "No-award",
        final_outcome_label=tr(
            "decision_approved" if intent["outcome"] == "approve" else "decision_no_award", lang
        ),
        final_actor=_required_string(audit, "actor_reference"),
        final_reason=audit["rationale"] or "",
        final_recorded_at=_parse_datetime(audit["recorded_at"]).isoformat(),
        final_recorded_display=moment(audit["recorded_at"], lang),
        final_content_hash=decision["approved_content_hash"] or "",
        final_audit=json.dumps(decision, indent=2, ensure_ascii=False),
    )
    return details
