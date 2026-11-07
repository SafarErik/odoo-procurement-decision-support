"""One stored planning case as display rows; no local inference or optimization.

``validate_case`` checks every cross-field invariant of the stored record (identity,
versions, supplier joins, demand totals, approved content). The section functions
below only format; they still parse single values strictly and raise on malformed ones.
"""

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, localcontext

from frontend.api.labels import product_label, supplier_label
from frontend.api.parsing import is_uuid, parse_datetime, required_string
from frontend.i18n import day, moment, money, number, percent, tr, unit

STATUSES = ("optimal", "infeasible", "no_proven_optimum", "solver_error", "invalid_input")
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


def map_case(payload: dict, expected_id: str, lang: str = "en") -> PlanningDisplay:
    """Validate a stored case and format every section in ``lang``; raises on invalid data."""
    validate_case(payload, expected_id)
    case = _Case(payload, lang)
    plans, allocations = plan_rows(case)
    comparison_rows, scenario_details = scenario_comparison(case)
    assessments, provenance, audit_details = audit(case)
    details = {
        **summary(case),
        **alternatives(case),
        **scenario_details,
        **audit_details,
        **decision(payload, case.recorded, lang),
    }
    return PlanningDisplay(
        details,
        plans,
        allocations,
        assessments,
        provenance,
        suppliers(case),
        comparison_rows,
        payload,
    )


# Strict single-value parsing.


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


def _allocation(rows: list[dict], message: str) -> dict[str, int]:
    by_supplier = {}
    for row in rows:
        identity = required_string(row, "supplier_id")
        _integer(row["quantity"])
        if identity in by_supplier or row["quantity"] < 0:
            raise ValueError(message)
        by_supplier[identity] = row["quantity"]
    return by_supplier


def _recorded_plans(result: dict) -> list[dict]:
    minimum = result["minimum_cost_plan"]
    return ([] if minimum is None else [minimum]) + result["alternatives"]


# Validation.


def validate_case(payload: dict, expected_id: str) -> None:
    """Raise ``ValueError``/``KeyError``/``TypeError`` unless the stored case is consistent."""
    if required_string(payload, "case_id") != expected_id:
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
    if required_string(result, "status") not in STATUSES:
        raise ValueError("Unknown planning status")
    if facts["input_kind"] != "odoo_quotations_odoo_history":
        raise ValueError("Unsupported input kind")
    required_string(requirement, "currency")
    required_string(requirement, "quantity_unit")
    parent = payload["parent_id"]
    if parent is not None and not is_uuid(parent):
        raise ValueError("Invalid parent identity")
    base_quantity = facts["requirement"]["approved_quantity"]
    _integer(base_quantity)
    if base_quantity <= 0:
        raise ValueError("Invalid base quantity")
    supplier_ids = [required_string(s["terms"], "supplier_id") for s in facts["suppliers"]]
    if len(set(supplier_ids)) != len(supplier_ids):
        raise ValueError("Duplicate base supplier")
    saved = {s["supplier_id"] for s in request["suppliers"]}
    if len(saved) != len(request["suppliers"]) or saved != set(supplier_ids):
        raise ValueError("Invalid saved supplier join")
    _validate_comparison(snapshot["comparison"], result, set(supplier_ids), base_quantity, quantity)
    recorded = _recorded_plans(result)
    if any(_decimal(p["total_cost"]) <= 0 for p in recorded):
        raise ValueError("Invalid recorded plan cost")
    for plan in recorded:
        by_supplier = _allocation(plan["allocations"], "Invalid recorded allocation")
        if set(by_supplier) != set(supplier_ids) or sum(by_supplier.values()) != quantity:
            raise ValueError("Invalid recorded allocation supplier join or demand total")
        if not 0 <= _ratio(plan["risk_exposure"]) <= 1:
            raise ValueError("Invalid recorded exposure")
    for assessment in snapshot["assessments"]:
        if assessment["snapshot"]["source_type"] != "odoo_purchase_history" or facts[
            "source_type"
        ] != ("odoo_purchase_history"):
            raise ValueError("Unsupported ML source")
        predicted = assessment["predicted_class"]
        if type(predicted) is not int or predicted not in (0, 1):
            raise ValueError("Unsupported assessment")
        if not 0 <= _decimal(assessment["score"]) <= 1:
            raise ValueError("Unsupported assessment")
    _validate_decision(payload, recorded)


def _validate_comparison(comparison, result, supplier_ids, base_quantity, quantity):
    if comparison is None or comparison["minimum_cost"] is None:
        return
    delta = comparison["minimum_cost"]
    before = _allocation(delta["base_allocations"], "Invalid comparison allocation")
    after = _allocation(delta["scenario_allocations"], "Invalid comparison allocation")
    if set(before) != supplier_ids or set(after) != supplier_ids:
        raise ValueError("Invalid comparison supplier join")
    if sum(before.values()) != base_quantity or sum(after.values()) != quantity:
        raise ValueError("Invalid comparison quantity")
    minimum = result["minimum_cost_plan"]
    if after != {a["supplier_id"]: a["quantity"] for a in minimum["allocations"]}:
        raise ValueError("Comparison differs from recorded plan")


def _validate_decision(payload, plans):
    decision = payload.get("final_decision")
    if decision is None:
        return
    intent, audit_ = decision["intent"], decision["audit"]
    if (
        payload["parent_id"] is not None
        or decision["decision_version"] != "t17-final-decision-v1"
        or decision["case_id"] != payload["case_id"]
        or intent["snapshot_hash"] != payload["snapshot_hash"]
        or intent["outcome"] not in {"approve", "no_award"}
        or intent["demonstration_acknowledged"] is not True
        or any(
            audit_[k] != intent[k]
            for k in ("outcome", "plan_index", "actor_reference", "rationale")
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
            or content["human_decision"] != audit_
            or hashlib.sha256(
                json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
            != decision["approved_content_hash"]
        ):
            raise ValueError("Invalid approved content")
    elif index is not None or content is not None or decision["approved_content_hash"] is not None:
        raise ValueError("Invalid no-award content")


# Formatting context shared by the sections.


class _Case:
    """A validated case plus the labels and units every section formats with."""

    def __init__(self, payload: dict, lang: str):
        self.payload, self.lang = payload, lang
        self.snapshot = snapshot = payload["snapshot"]
        self.facts, self.request, self.result = (
            snapshot["facts"],
            snapshot["request"],
            snapshot["result"],
        )
        self.requirement = self.request["requirement"]
        self.names = {key: value for key, value in self.facts.get("labels", ())}
        self.quantity = self.requirement["approved_quantity"]
        self.base_quantity = self.facts["requirement"]["approved_quantity"]
        self.currency = self.requirement["currency"]
        self.unit_name = _unit_label(self.requirement["quantity_unit"], lang, self.names)
        self.supplier_ids = {s["terms"]["supplier_id"] for s in self.facts["suppliers"]}
        self.saved_suppliers = {s["supplier_id"]: s for s in self.request["suppliers"]}
        self.recorded = _recorded_plans(self.result)
        self.minimum = self.result["minimum_cost_plan"]

    def name(self, identity: str) -> str:
        return supplier_label(identity, self.lang, self.names)

    def amount(self, value, signed: bool = False) -> str:
        return money(value, self.currency, self.lang, signed=signed)

    def pieces(self, value) -> str:
        return tr("pieces", self.lang, quantity=number(value, self.lang), unit=self.unit_name)


def _unit_label(identity: str, lang: str, names: dict) -> str:
    if names.get(identity):
        return unit(names[identity], lang)
    # Without a saved name the unit is not known to mean pieces; keep the identity visible.
    return identity if identity.startswith("odoo:uom.uom:") else unit(identity, lang)


def _buyer_explanations(entries: list[dict], lang: str = "en", names: dict | None = None) -> str:
    return "\n".join(
        dict.fromkeys(
            ((supplier_label(e["supplier_id"], lang, names) + ": ") if e["supplier_id"] else "")
            + tr(key, lang)
            for e in entries
            if (key := "why_" + e["code"]) in _WHY
        )
    )


def _data_origin(snapshot: dict) -> str:
    """Same rule as the PDF: the history model records where its Odoo data came from."""
    origin = snapshot.get("model_manifest", {}).get("metadata", {}).get("data_origin")
    return origin if origin in ("generated", "observed") else "generated"


def _balanced_only(result: dict) -> set[int]:
    """Alternatives proved only by the balanced (min–max share) stage, never by a risk stage."""
    runs = result.get("runs", [])
    risk = {r["plan_index"] for r in runs if r.get("kind", "risk") == "risk"}
    return {
        r["plan_index"]
        for r in runs
        if r.get("kind") == "diversified" and r["plan_index"] and r["plan_index"] not in risk
    }


def _plan_title(result: dict, index: int, lang: str) -> str:
    if index == 0:
        return tr("plan_minimum", lang)
    if index in _balanced_only(result):
        return tr("plan_balanced", lang)
    return tr("plan_alternative", lang, n=index)


# Sections.


def summary(case: _Case) -> dict[str, str]:
    """Overview facts: identity, demand, dates, status, policy and solver diagnostics."""
    lang, payload, facts, requirement = case.lang, case.payload, case.facts, case.requirement
    status = case.result["status"]
    parent = payload["parent_id"]
    scenario = case.snapshot["scenario"]
    policy = case.request["policy"]
    concentration = policy["concentration_limit"]
    data_origin = _data_origin(case.snapshot)
    status_label = tr("status_" + status, lang)
    return {
        "data_origin": data_origin,
        "origin_badge": "" if data_origin == "observed" else tr("badge_generated", lang),
        "origin_note": "" if data_origin == "observed" else tr("generated_note", lang),
        "case_id": payload["case_id"],
        "parent_id": parent or "Base case",
        "created_at": parse_datetime(payload["created_at"]).isoformat(),
        "created_display": moment(payload["created_at"], lang),
        "snapshot_hash": required_string(payload, "snapshot_hash"),
        "status": status.replace("_", " "),
        "status_code": status,
        "input_kind": "Odoo quotations and Odoo purchase history",
        "company": required_string(facts, "company_id"),
        "product": required_string(requirement, "product_id"),
        "quantity": _integer(case.quantity),
        "quantity_display": case.pieces(case.quantity),
        "unit": requirement["quantity_unit"],
        "unit_label": case.unit_name,
        "required_date": required_string(requirement, "required_date"),
        "required_display": day(requirement["required_date"], lang),
        "as_of": parse_datetime(facts["as_of"]).isoformat(),
        "as_of_display": moment(facts["as_of"], lang),
        "scenario": "Base case" if scenario is None else required_string(scenario, "kind"),
        "base_id": parent or payload["case_id"],
        "currency": case.currency,
        "status_label": status_label,
        "scenario_label": "" if scenario is None else tr("kind_" + scenario["kind"], lang),
        "base_quantity": str(case.base_quantity),
        "base_quantity_display": case.pieces(case.base_quantity),
        "scenario_status": status.replace("_", " "),
        "scenario_status_label": status_label,
        "policy": tr(
            "policy_text",
            lang,
            suppliers=_integer(policy["max_suppliers"]),
            share=tr("policy_no_share", lang)
            if concentration is None
            else percent(_decimal(concentration), lang, 0),
            allowance=", ".join(percent(_decimal(e), lang, 0) for e in policy["epsilons"])
            or tr("none", lang),
        )
        + (
            ""
            if policy.get("diversification_epsilon") is None
            else tr(
                "policy_balanced",
                lang,
                allowance=percent(_decimal(policy["diversification_epsilon"]), lang, 0),
            )
        ),
        "product_label": product_label(requirement["product_id"], lang, case.names),
        "buyer_diagnostics": _buyer_explanations(case.result["explanations"], lang, case.names),
    }


def suppliers(case: _Case) -> list[dict[str, str]]:
    """Base supplier terms next to the terms saved for this case (what-if form rows)."""
    rows = []
    for s in case.facts["suppliers"]:
        identity = s["terms"]["supplier_id"]
        saved = case.saved_suppliers[identity]
        rows.append(
            {
                "supplier": identity,
                "name": case.name(identity),
                "capacity": _integer(s["terms"]["capacity"]),
                "price": str(_decimal(s["terms"]["unit_price"])),
                "price_display": case.amount(_decimal(s["terms"]["unit_price"])),
                "saved_price": case.amount(_decimal(saved["unit_price"])),
                "saved_capacity": _integer(saved["capacity"]),
                "saved_moq": tr("none", case.lang)
                if saved["minimum_order"]["quantity"] is None
                else _integer(saved["minimum_order"]["quantity"]),
                "saved_date": day(required_string(saved, "promised_date"), case.lang),
                "saved_available": tr(
                    "available" if saved["available"] else "not_available", case.lang
                ),
                "saved_ranges": (
                    f"{_integer(saved['price_quantities']['minimum'])}–"
                    f"{_integer(saved['price_quantities']['maximum'])} / "
                    f"{_integer(saved['delivery_quantities']['minimum'])}–"
                    f"{_integer(saved['delivery_quantities']['maximum'])}"
                ),
            }
        )
    return rows


def alternatives(case: _Case) -> dict[str, str]:
    """Plan count, minimum cost and the cost/risk trade-off sentence or why none exists."""
    lang, recorded, minimum = case.lang, case.recorded, case.minimum
    details = {
        "plan_count": str(len(recorded)),
        "min_cost_display": "",
        "alternative_notice": "",
        "decision_summary": "",
    }
    if not recorded:
        return details
    details["min_cost_display"] = case.amount(_decimal(recorded[0]["total_cost"]))
    if len(recorded) == 1:
        details["alternative_notice"] = tr(
            "no_alternative_failed"
            if case.result["status"] != "optimal"
            else "no_alternative_found"
            if case.request["policy"]["epsilons"]
            else "no_alternative_requested",
            lang,
        )
        return details
    alternative = min(recorded[1:], key=lambda p: _ratio(p["risk_exposure"]))
    reduction = (_ratio(minimum["risk_exposure"]) - _ratio(alternative["risk_exposure"])) * 100
    additional_cost = _decimal(alternative["total_cost"]) - _decimal(minimum["total_cost"])
    details["decision_summary"] = tr(
        "tradeoff_summary" if reduction > 0 else "tradeoff_summary_up",
        lang,
        amount=case.amount(additional_cost),
        points=number(abs(reduction) if reduction > 0 else -reduction, lang, 1),
    )
    return details


def plan_rows(case: _Case) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """One row per recorded plan (cost, exposure, premium, notes) and its allocation rows."""
    lang, result, minimum, quantity = case.lang, case.result, case.minimum, case.quantity
    recorded = case.recorded
    lowest = min(
        range(len(recorded)), key=lambda i: _ratio(recorded[i]["risk_exposure"]), default=0
    )
    # Keep the tightest allowance that proves each plan, independent of run order.
    budgets = {}
    for run in result.get("runs", []):
        if run.get("plan_index"):
            epsilon = _decimal(run["epsilon"])
            budgets[run["plan_index"]] = min(epsilon, budgets.get(run["plan_index"], epsilon))
    balanced_only = _balanced_only(result)
    balanced = {r["plan_index"] for r in result.get("runs", []) if r.get("kind") == "diversified"}
    balanced -= {0}
    plans, allocations = [], []
    for index, plan in enumerate(recorded):
        label = "Minimum cost" if index == 0 else f"Alternative {index}"
        by_supplier = {a["supplier_id"]: a["quantity"] for a in plan["allocations"]}
        with localcontext() as context:
            context.prec = max(28, len(plan["total_cost"]) + len(minimum["total_cost"]))
            extra_cost = _decimal(plan["total_cost"]) - _decimal(minimum["total_cost"])
        exposure = _ratio(plan["risk_exposure"])
        used = [i for i in sorted(by_supplier) if by_supplier[i] > 0]
        plans.append(
            {
                "label": label,
                "title": _plan_title(result, index, lang),
                "stage": "balanced" if index in balanced_only else "",
                "hint": tr("plan_lower_risk", lang) if index == lowest and index else "",
                "balanced": tr("plan_balanced_hint", lang)
                if index in balanced - balanced_only
                else "",
                "largest_share": percent(_ratio(plan["largest_share"]), lang, 0),
                "budget": tr("plan_budget", lang, allowance=percent(budgets[index], lang, 0))
                if index in budgets
                else "",
                "number": str(index + 1),
                "index": str(index),
                "cost": case.amount(_decimal(plan["total_cost"])),
                "cost_exact": plan["total_cost"],
                "cost_number": f"{_decimal(plan['total_cost']):f}",
                "exposure": _rational(plan["risk_exposure"]),
                "exposure_number": f"{exposure * 100:.1f}",
                "premium": _rational(plan["cost_premium"]),
                "premium_absolute": case.amount(extra_cost, signed=True),
                "premium_exact": (
                    f"{plan['cost_premium']['numerator']}/{plan['cost_premium']['denominator']}"
                ),
                "exposure_exact": (
                    f"{plan['risk_exposure']['numerator']}/{plan['risk_exposure']['denominator']}"
                ),
                "supplier_count": str(len(used)),
                "allocation_summary": "; ".join(
                    f"{case.name(identity)}: {case.pieces(by_supplier[identity])}"
                    for identity in used
                ),
                "exposure_display": tr(
                    "exposure_value", lang, value=number(exposure * 100, lang, 1)
                ),
                "premium_display": tr("minimum_for_limits", lang)
                if index == 0
                else tr(
                    "above_minimum",
                    lang,
                    amount=f"{case.amount(extra_cost, signed=True)} "
                    f"({percent(_ratio(plan['cost_premium']), lang)})",
                ),
                "buyer_notes": _buyer_explanations(plan["explanations"], lang, case.names),
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
                "quantity_display": case.pieces(by_supplier[identity]),
                "name": case.name(identity),
                "promised": day(case.saved_suppliers[identity]["promised_date"], lang),
                "share": f"{Decimal(by_supplier[identity]) / quantity * 100:.2f}",
                "share_display": percent(Decimal(by_supplier[identity]) / quantity, lang, 0),
            }
            for identity in sorted(by_supplier)
        )
    return plans, allocations


def scenario_comparison(case: _Case) -> tuple[list[dict[str, str]], dict[str, str]]:
    """A what-if child against its base: changed assumptions, deltas, per-supplier change."""
    lang = case.lang
    comparison, scenario = case.snapshot["comparison"], case.snapshot["scenario"]
    details = {
        "comparison": "",
        "comparison_display": "",
        "base_status": "",
        "base_status_label": "",
        "assumptions": "",
    }
    rows = []
    if comparison is not None:
        details["base_status"] = required_string(comparison, "base_status").replace("_", " ")
        details["base_status_label"] = tr("status_" + comparison["base_status"], lang)
        details["comparison"] = required_string(comparison, "meaning")
        delta = comparison["minimum_cost"]
        if delta is not None:
            before = {r["supplier_id"]: r["quantity"] for r in delta["base_allocations"]}
            after = {r["supplier_id"]: r["quantity"] for r in delta["scenario_allocations"]}
            rows = [
                {
                    "name": case.name(identity),
                    "base": str(before[identity]),
                    "scenario": str(after[identity]),
                    "change": f"{after[identity] - before[identity]:+d}",
                }
                for identity in sorted(case.supplier_ids)
            ]
            details["comparison"] += (
                f" Cost delta: {_decimal(delta['total_cost_delta']):,f} {case.currency}; "
                f"exposure delta: {_rational(delta['risk_exposure_delta'])}."
            )
            if case.recorded:
                details["comparison_display"] = tr(
                    "scenario_delta",
                    lang,
                    amount=case.amount(_decimal(delta["total_cost_delta"]), signed=True),
                    points=number(_ratio(delta["risk_exposure_delta"]) * 100, lang, 1),
                )
            else:
                details["comparison_display"] = tr("scenario_no_plan", lang)
        else:
            details["comparison_display"] = tr("scenario_no_plan", lang)
        if case.base_quantity != case.quantity:
            details["comparison_display"] += " " + tr("scenario_demand_changed", lang)
    if scenario is not None:
        assumptions = []
        if scenario["approved_quantity"] is not None:
            assumptions.append(
                tr("assume_demand", lang, quantity=case.pieces(scenario["approved_quantity"]))
            )
        for change in scenario["suppliers"]:
            supplier = case.name(required_string(change, "supplier_id"))
            if change["available"] is False:
                assumptions.append(tr("assume_outage", lang, name=supplier))
            if change["capacity"] is not None:
                assumptions.append(
                    tr(
                        "assume_capacity",
                        lang,
                        name=supplier,
                        quantity=case.pieces(change["capacity"]),
                    )
                )
            if change["unit_price"] is not None:
                assumptions.append(
                    tr(
                        "assume_price",
                        lang,
                        name=supplier,
                        price=case.amount(_decimal(change["unit_price"])),
                    )
                )
        details["assumptions"] = "; ".join(assumptions)
    return rows, details


def audit(case: _Case) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    """Decision Tree assessments, provenance entries, raw explanations and the snapshot JSON."""
    lang, snapshot = case.lang, case.snapshot
    assessments = []
    for assessment in snapshot["assessments"]:
        feature = assessment["snapshot"]
        assessments.append(
            {
                "supplier": required_string(feature["context"], "supplier_id"),
                "score": str(_decimal(assessment["score"])),
                "name": case.name(feature["context"]["supplier_id"]),
                "reference_time": parse_datetime(feature["cutoff"]).isoformat(),
                "history_window": (
                    f"{day(feature['history_start'], lang)} – {day(feature['history_end'], lang)}"
                ),
                "class": _integer(assessment["predicted_class"]),
                "model": required_string(assessment, "model_id"),
                "source": required_string(feature, "source_reference"),
                "valid_until": parse_datetime(assessment["valid_until"]).isoformat(),
                "quantity_range": (
                    f"{_integer(assessment['quantities']['minimum'])}–"
                    f"{_integer(assessment['quantities']['maximum'])} {case.unit_name}"
                ),
                "path": "\n".join(
                    f"{step['feature']} = {step['value_float32']} "
                    f"{step['operator']} {step['threshold']}"
                    for step in assessment["path"]
                ),
            }
        )
    provenance = [
        {
            "field": required_string(entry, "canonical_path"),
            "type": required_string(entry, "source_type"),
            "reference": required_string(entry, "source_reference"),
            "observed_at": parse_datetime(entry["observed_at"]).isoformat(),
        }
        for entry in snapshot["provenance"]["entries"]
    ]
    details = {
        "explanations": "\n".join(
            f"{e['code']}: {e['detail']}" for e in case.result["explanations"]
        ),
        "snapshot_json": json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False),
    }
    return assessments, provenance, details


def decision(payload: dict, plans: list[dict], lang: str = "en") -> dict[str, str]:
    """The recorded human decision (approve a plan or No-award) and its audit record."""
    decision_ = payload.get("final_decision")
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
    if decision_ is None:
        return details
    intent, audit_ = decision_["intent"], decision_["audit"]
    index = intent["plan_index"]
    if intent["outcome"] == "approve":
        details["final_plan"] = "Minimum cost" if index == 0 else f"Alternative {index}"
        details["final_plan_title"] = _plan_title(payload["snapshot"]["result"], index, lang)
    else:
        details["final_plan"] = "None (No-award)"
        details["final_plan_title"] = tr("decision_no_award", lang)
    details.update(
        final_outcome="Approved" if intent["outcome"] == "approve" else "No-award",
        final_outcome_label=tr(
            "decision_approved" if intent["outcome"] == "approve" else "decision_no_award", lang
        ),
        final_actor=required_string(audit_, "actor_reference"),
        final_reason=audit_["rationale"] or "",
        final_recorded_at=parse_datetime(audit_["recorded_at"]).isoformat(),
        final_recorded_display=moment(audit_["recorded_at"], lang),
        final_content_hash=decision_["approved_content_hash"] or "",
        final_audit=json.dumps(decision_, indent=2, ensure_ascii=False),
    )
    return details
