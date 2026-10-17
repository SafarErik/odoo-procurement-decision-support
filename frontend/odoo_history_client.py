"""HTTP-only preview of the server-owned Odoo history profile."""

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
            data["profile_id"] != "local-v1"
            or re.fullmatch(r"[0-9a-f]{64}", data["profile_revision"]) is None
            or data["origin"] != "controlled_synthetic"
            or len(data["history"]) != 3
            or data["model_readiness"] not in {"ready", "model_unavailable"}
        ):
            raise ValueError("Invalid configured history profile.")
        return data, ""
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return (
            None,
            "The Odoo history preview could not be verified. Reload before creating a case.",
        )
