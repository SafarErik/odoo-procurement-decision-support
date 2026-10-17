"""HTTP-only Odoo quotation-group listing and purchase-history preview."""

import re

import httpx


async def fetch_odoo_history(url, token, *, transport=None):
    try:
        async with httpx.AsyncClient(timeout=30, transport=transport, trust_env=False) as client:
            response = await client.get(url, headers={"Authorization": "Bearer " + token})
        if response.status_code != 200:
            return (
                None,
                "Odoo history unavailable. Check the dedicated reader, database "
                "and model configuration.",
            )
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
        return (
            None,
            "The Odoo history preview could not be verified. Reload before creating a case.",
        )


async def fetch_quotation_groups(url, token, *, transport=None):
    """Open Odoo quotation groups as select options; nothing is stored or written."""
    try:
        async with httpx.AsyncClient(timeout=30, transport=transport, trust_env=False) as client:
            response = await client.get(
                url, params={"limit": 20}, headers={"Authorization": "Bearer " + token}
            )
        if response.status_code != 200:
            return None, "Open Odoo quotation groups are unavailable. Check the Odoo connection."
        if len(response.content) > 512 * 1024:
            raise ValueError("Oversized group listing.")
        rows = []
        for item in response.json()["items"]:
            if type(item["purchase_group_id"]) is not int or item["purchase_group_id"] <= 0:
                raise ValueError("Invalid group identity.")
            suppliers = ", ".join(q["supplier_name"] for q in item["quotations"])
            name = item["name"]
            if name.startswith("purchase.order.group,"):  # Odoo's technical display name
                name = f"Group {item['purchase_group_id']}"
            label = (
                f"{name} · {item['product_name'] or '—'} · "
                f"{item['quantity'] or '—'} {item['uom_name'] or ''} · {item['currency'] or ''}"
                f" · {item['supplier_count']} suppliers ({suppliers})"
            )
            if not item["selectable"]:
                label += f" — not usable: {item['issue']}"
            rows.append(
                {
                    "value": str(item["purchase_group_id"]),
                    "label": label,
                    "selectable": "yes" if item["selectable"] else "",
                }
            )
        return rows, ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None, "The Odoo quotation-group listing could not be verified. Reload it."
