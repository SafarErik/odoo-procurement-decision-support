"""Per-supplier read model of one stored case (P2 API); the browser never sees the token."""

from uuid import UUID

import httpx

from frontend.i18n import day, money, number, percent, tr, unit

# KPIs compared across suppliers on the Suppliers tab: (feature, scale, higher_is_better).
CHART_KPIS = (
    ("on_time_rate", 100, True),
    ("fill_rate", 100, True),
    ("mean_lateness_days", 1, False),
)


async def fetch_supplier_overview(cases_url, case_id, token, *, lang="hu", transport=None):
    try:
        if str(UUID(case_id)) != case_id or lang not in ("hu", "en"):
            raise ValueError("Invalid request")
        async with httpx.AsyncClient(timeout=10, transport=transport, trust_env=False) as client:
            response = await client.get(
                f"{cases_url.rstrip('/')}/{case_id}/suppliers",
                params={"language": lang},
                headers={"Authorization": "Bearer " + token},
            )
        if response.status_code != 200:
            return None, tr("err_suppliers", lang)
        return map_overview(response.json(), lang), ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError, ArithmeticError):
        return None, tr("err_suppliers", lang)


def _name(row, lang):
    if row["supplier_name"]:
        return row["supplier_name"]
    identity = row["supplier_id"]
    if identity.startswith("odoo:res.partner:"):
        return tr("supplier_n", lang, n=identity.removeprefix("odoo:res.partner:"))
    if identity.startswith("synthetic-"):
        return tr("demo_supplier", lang, n=identity.removeprefix("synthetic-"))
    return identity


def map_overview(data: dict, lang: str) -> dict:
    """Cards and chart rows; values come from the stored snapshot through the API only."""
    if data["language"] != lang:
        raise ValueError("Language mismatch")
    first = data["suppliers"][0] if data["suppliers"] else {}
    unit_name = unit(first.get("unit_name") or "Units", lang)
    cards, charts = [], {feature: [] for feature, _, _ in CHART_KPIS}
    for row in data["suppliers"]:
        name = _name(row, lang)
        assessment, terms, history = row["assessment"], row["terms"], row["history"]
        metrics = {m["feature"]: m for m in history["metrics"]}
        for feature, scale, _ in CHART_KPIS:
            if feature in metrics:
                charts[feature].append(
                    {"name": name, "value": round(float(metrics[feature]["value"]) * scale, 2)}
                )
        allocation = row["allocation"]["minimum_cost_quantity"]
        cards.append(
            {
                "supplier": row["supplier_id"],
                "name": name,
                "class_key": assessment["class"],
                "class_label": assessment["class_label"],
                "score_display": number(float(assessment["score"]) * 100, lang, 1) + " / 100",
                "summary": assessment["summary"],
                "price": money(terms["unit_price"], row["currency"], lang),
                "capacity": tr(
                    "pieces", lang, quantity=number(terms["capacity"], lang), unit=unit_name
                ),
                "moq": tr("none", lang)
                if terms["minimum_order_quantity"] is None
                else number(terms["minimum_order_quantity"], lang),
                "promised": day(terms["promised_date"], lang),
                "available": tr("available" if terms["available"] else "not_available", lang),
                "offer": row["offer_reference"] or "",
                "planned": ""
                if allocation is None
                else tr("pieces", lang, quantity=number(allocation, lang), unit=unit_name),
                "window": day(history["window_start"], lang)
                + " – "
                + day(history["window_end"], lang),
                "metrics": [
                    {"label": m["label"], "display": m["display"]} for m in history["metrics"]
                ],
                "path": [step["text"] for step in assessment["path"]],
                "share_text": percent(
                    assessment["problematic_cases"] / max(1, assessment["similar_cases"]), lang, 0
                ),
            }
        )
    return {"cards": cards, "charts": charts}
