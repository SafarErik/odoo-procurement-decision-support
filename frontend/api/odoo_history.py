"""Odoo-backed resources read live through the backend: open quotation groups and the
purchase-history preview of one group. Nothing is stored or written."""

import re
from decimal import Decimal

from frontend.api import http
from frontend.config import settings
from frontend.i18n import TEXT, day, money, number, tr, unit


def _preview(response) -> dict:
    """The validated history preview of one quotation group."""
    if len(response.content) > 256 * 1024:
        raise ValueError("Oversized history preview.")
    data = response.json()
    if (
        type(data["purchase_group_id"]) is not int
        or re.fullmatch(r"[0-9a-f]{64}", data["capture_hash"]) is None
        or not 1 <= len(data["history"]) <= 10
        or data["model_readiness"] not in {"ready", "model_unavailable"}
    ):
        raise ValueError("Invalid Odoo history preview.")
    return data


async def fetch_odoo_history(group_id: int, *, lang: str = "en"):
    """Purchase-history preview and suggested terms of one Odoo quotation group."""
    return await http.get_json(
        settings.planning_cases_url + "/odoo-history/preview",
        _preview,
        lang=lang,
        params={"purchase_group_id": group_id},
        unavailable="err_preview",
        invalid="err_preview_data",
        timeout=http.LONG_TIMEOUT,
    )


def group_row(item: dict, lang: str) -> dict[str, str]:
    """One open quotation group as buyer-readable strings (values are not stored)."""
    if type(item["purchase_group_id"]) is not int or item["purchase_group_id"] <= 0:
        raise ValueError("Invalid group identity.")
    identity = item["purchase_group_id"]
    name = item["name"]
    if name.startswith("purchase.order.group,"):  # Odoo's technical display name
        name = tr("group_n", lang, n=identity)
    currency = item["currency"] or ""
    unit_name = unit(item["uom_name"] or "", lang)
    prices = []
    for quotation in item["quotations"]:
        price = quotation["lines"][0]["unit_price"] if quotation["lines"] else None
        prices.append(
            {
                "supplier": quotation["supplier_name"],
                "price": "—" if price is None else money(Decimal(price), currency, lang),
            }
        )
    issue = item["issue"]
    return {
        "value": str(identity),
        "name": name,
        "product": item["product_name"] or "—",
        "quantity": "—"
        if item["quantity"] is None
        else tr(
            "pieces",
            lang,
            quantity=number(Decimal(item["quantity"]).normalize(), lang),
            unit=unit_name,
        ),
        "currency": currency,
        "unit": unit_name,
        "supplier_count": str(item["supplier_count"]),
        "suppliers": ", ".join(p["supplier"] for p in prices),
        "offers": " · ".join(f"{p['supplier']} {p['price']}" for p in prices),
        "date": day(item["latest_order_date"], lang),
        "selectable": "yes" if item["selectable"] else "",
        "issue": tr(f"issue_{issue}", lang) if f"issue_{issue}" in TEXT else issue or "",
        "label": f"{name} · {item['product_name'] or '—'}",
    }


def _groups(response, lang: str) -> dict:
    """Validated open quotation groups as rows, raw items and supplier names."""
    if len(response.content) > 512 * 1024:
        raise ValueError("Oversized group listing.")
    data = response.json()
    rows = [group_row(item, lang) for item in data["items"]]
    names = {
        str(item["purchase_group_id"]): {
            q["supplier_id"]: q["supplier_name"] for q in item["quotations"]
        }
        for item in data["items"]
    }
    return {
        "rows": rows,
        "raw": data["items"],
        "names": names,
        "truncated": bool(data.get("truncated")),
        "retrieved_at": data.get("retrieved_at", ""),
        "company_id": data.get("company_id", ""),
    }


async def fetch_quotation_groups(*, lang: str = "en"):
    """Open Odoo quotation groups as display rows; nothing is stored or written."""
    return await http.get_json(
        settings.quotation_groups_url,
        lambda response: _groups(response, lang),
        lang=lang,
        params={"limit": 20},
        unavailable="err_groups",
        invalid="err_groups_data",
        timeout=http.LONG_TIMEOUT,
    )


def quotation_rows(item: dict, lang: str) -> list[dict[str, str]]:
    """Keep quotation identities and quantities visible without regrouping source facts."""
    currency = item.get("currency") or ""
    rows = []
    for quotation in item["quotations"]:
        for line in quotation["lines"]:
            rows.append(
                {
                    "reference": quotation["reference"],
                    "supplier": quotation["supplier_name"],
                    "price": money(Decimal(line["unit_price"]), currency, lang)
                    if currency
                    else str(line["unit_price"]),
                    "quantity": number(Decimal(line["quantity"]).normalize(), lang)
                    + " "
                    + unit(line.get("uom_name") or "", lang),
                    "status": tr(
                        "quotation_" + quotation["state"]
                        if quotation["state"] in {"draft", "sent"}
                        else "quotation_other",
                        lang,
                    ),
                }
            )
    return rows
