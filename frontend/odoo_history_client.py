"""HTTP-only Odoo quotation-group listing and purchase-history preview."""

import re
from decimal import Decimal

import httpx

from frontend.i18n import day, money, number, tr, unit

ISSUES = {
    "unsupported_offer_count": (
        "Kettőnél kevesebb vagy túl sok ajánlat",
        "Too few or too many quotations",
    ),
    "not_all_open": ("Nem minden ajánlat nyitott", "Not every quotation is open"),
    "not_single_line": ("Az ajánlatok nem egysorosak", "Quotations are not single-line"),
    "duplicate_supplier": ("Egy szállító többször szerepel", "A supplier appears twice"),
    "mixed_context": ("Eltérő termék, egység vagy pénznem", "Different product, unit or currency"),
    "discount_or_tax": ("Kedvezményt vagy adót tartalmaz", "Contains a discount or tax"),
}


async def fetch_odoo_history(url, token, *, lang="en", transport=None):
    try:
        async with httpx.AsyncClient(timeout=30, transport=transport, trust_env=False) as client:
            response = await client.get(url, headers={"Authorization": "Bearer " + token})
        if response.status_code != 200:
            return None, tr("err_preview", lang)
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
        return data, ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None, tr("err_preview_data", lang)


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
        "issue": "" if not issue else ISSUES.get(issue, (issue, issue))[0 if lang == "hu" else 1],
        "label": f"{name} · {item['product_name'] or '—'}",
    }


async def fetch_quotation_groups(url, token, *, lang="en", transport=None):
    """Open Odoo quotation groups as display rows; nothing is stored or written."""
    try:
        async with httpx.AsyncClient(timeout=30, transport=transport, trust_env=False) as client:
            response = await client.get(
                url, params={"limit": 20}, headers={"Authorization": "Bearer " + token}
            )
        if response.status_code != 200:
            return None, tr("err_groups", lang)
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
        }, ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError, ArithmeticError):
        return None, tr("err_groups_data", lang)
