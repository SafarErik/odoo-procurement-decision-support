"""Stored library HTTP/presentation boundary; no persistence or model imports."""

import json
from datetime import date
from decimal import Decimal
from uuid import UUID

import httpx

from frontend.i18n import day, moment, money, number, tr, unit
from frontend.parsing import parse_datetime, required_string

_DECISIONS = {
    "draft": "decision_draft",
    "approved": "decision_approved",
    "no_award": "decision_no_award",
}
_OUTCOMES = ("optimal", "infeasible", "no_proven_optimum", "solver_error")


def _product(label: str, lang: str) -> str:
    if label.startswith("odoo:product.product:"):
        return tr("product_n", lang, n=label.removeprefix("odoo:product.product:"))
    return label


def library_row(item: dict, lang: str) -> dict[str, str]:
    """One saved case as buyer-readable strings; raises on invalid data."""
    case_id = required_string(item, "case_id")
    if str(UUID(case_id)) != case_id:
        raise ValueError("Invalid identity.")
    parent = item["parent_id"]
    if parent is not None and str(UUID(parent)) != parent:
        raise ValueError("Invalid lineage.")
    if item["origin"] not in {"demo", "odoo"}:
        raise ValueError("Invalid origin.")
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
    if source not in {
        "controlled_synthetic",
        "odoo_quotations_odoo_history",
        "odoo_quotations_synthetic_history",
    }:
        raise ValueError("Invalid source.")
    required_string(item, "quantity_unit")
    return {
        "case_id": case_id,
        "parent_id": parent or "",
        "product": _product(required_string(item, "product_label"), lang),
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
        "origin": item["origin"],
        "badge": {"observed": "", "synthetic": tr("badge_synthetic", lang)}.get(
            item.get("data_origin", "generated"), tr("badge_generated", lang)
        ),
        "scenario": ""
        if item["scenario_kind"] is None
        else tr("kind_" + item["scenario_kind"], lang),
        "changes": ""
        if item["changed_assumptions"] is None
        else json.dumps(item["changed_assumptions"], sort_keys=True),
    }


async def fetch_library(url, token, params, *, lang="en", transport=None):
    try:
        async with httpx.AsyncClient(transport=transport, timeout=15, trust_env=False) as client:
            response = await client.get(
                url, params=params, headers={"Authorization": "Bearer " + token}
            )
        if response.status_code != 200:
            return None, tr("err_library", lang)
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
        return {"items": rows, "raw": data["items"], "next_cursor": cursor or ""}, ""
    except httpx.HTTPError:
        return None, tr("err_library", lang)
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError):
        return None, tr("err_library_data", lang)
