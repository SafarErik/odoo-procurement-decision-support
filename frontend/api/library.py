"""Saved-case library resource: bounded pages of cases or of one base case's scenarios."""

import json
from datetime import date
from decimal import Decimal

from frontend.api import http
from frontend.api.labels import product_label
from frontend.api.parsing import is_uuid, parse_datetime, required_string
from frontend.config import settings
from frontend.i18n import day, moment, money, number, tr, unit

_DECISIONS = {
    "draft": "decision_draft",
    "approved": "decision_approved",
    "no_award": "decision_no_award",
}
_OUTCOMES = ("optimal", "infeasible", "no_proven_optimum", "solver_error", "invalid_input")


def library_row(item: dict, lang: str) -> dict[str, str]:
    """One saved case as buyer-readable strings; raises on invalid data."""
    case_id = required_string(item, "case_id")
    if not is_uuid(case_id):
        raise ValueError("Invalid identity.")
    parent = item["parent_id"]
    if parent is not None and not is_uuid(parent):
        raise ValueError("Invalid lineage.")
    if item["planning_status"] not in _OUTCOMES:
        raise ValueError("Invalid planning status.")
    quantity = item["approved_quantity"]
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Invalid demand.")
    date.fromisoformat(item["required_date"])
    currency = required_string(item, "currency")
    unit_name = unit(item.get("unit_label") or "Units", lang)
    minimum = item.get("minimum_cost")
    source = item["source_kind"]
    if source != "odoo_quotations_odoo_history":
        raise ValueError("Invalid source.")
    required_string(item, "quantity_unit")
    return {
        "case_id": case_id,
        "short_id": case_id[:8],
        "parent_id": parent or "",
        "product": product_label(required_string(item, "product_label"), lang),
        "quantity": tr("pieces", lang, quantity=number(quantity, lang), unit=unit_name),
        "required": day(item["required_date"], lang),
        "currency": currency,
        "context": f"{number(quantity, lang)} {unit_name} · {currency} · "
        + tr("required_by", lang, date=day(item["required_date"], lang)),
        "company": required_string(item, "company_id"),
        "saved": moment(parse_datetime(item["created_at"]).isoformat(), lang),
        "status": item["decision_status"] if parent is None else "scenario",
        "decision": tr(
            _DECISIONS[item["decision_status"]] if parent is None else "decision_scenario",
            lang,
        ),
        "outcome": tr("status_" + item["planning_status"], lang),
        "minimum_cost": ""
        if minimum is None
        else money(Decimal(required_string(item, "minimum_cost")), currency, lang),
        "badge": "" if item["data_origin"] == "observed" else tr("badge_generated", lang),
        "scenario": ""
        if item["scenario_kind"] is None
        else tr("kind_" + item["scenario_kind"], lang),
        "changes": ""
        if item["changed_assumptions"] is None
        else json.dumps(item["changed_assumptions"], sort_keys=True),
    }


def _page(response, lang: str) -> dict:
    """One validated library page as display rows, raw items and the next cursor."""
    data = response.json()
    if (
        set(data) != {"items", "next_cursor"}
        or not isinstance(data["items"], list)
        or len(data["items"]) > 50
    ):
        raise ValueError("Invalid library page.")
    cursor = data["next_cursor"]
    if cursor is not None and (not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024):
        raise ValueError("Invalid continuation.")
    rows = [library_row(item, lang) for item in data["items"]]
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate library row.")
    return {"items": rows, "raw": data["items"], "next_cursor": cursor or ""}


async def _fetch(url: str, params: dict, lang: str):
    """GET one library page with the library error texts."""
    return await http.get_json(
        url,
        lambda response: _page(response, lang),
        lang=lang,
        params=params,
        unavailable="err_library",
        invalid="err_library_data",
    )


async def fetch_library(params: dict, *, lang: str = "en"):
    """One page of saved base cases (filters ``status``/``q``/``limit``/``cursor``)."""
    return await _fetch(settings.planning_cases_url, params, lang)


async def fetch_scenarios(case_id: str, params: dict, *, lang: str = "en"):
    """One page of the saved scenarios of base case ``case_id``."""
    if not is_uuid(case_id):
        return None, tr("err_library", lang)
    return await _fetch(f"{settings.planning_cases_url}/{case_id}/scenarios", params, lang)
