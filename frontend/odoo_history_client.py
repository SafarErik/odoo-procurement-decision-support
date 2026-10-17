"""HTTP-only preview of Odoo purchase history for one quotation group."""

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
