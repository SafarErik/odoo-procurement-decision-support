"""Stored library HTTP/presentation boundary; no persistence or model imports."""

import json
from datetime import date
from uuid import UUID

import httpx

from frontend.rfq_client import _parse_datetime, _required_string


async def fetch_library(url, token, params, *, transport=None):
    try:
        async with httpx.AsyncClient(transport=transport, timeout=15, trust_env=False) as client:
            response = await client.get(
                url, params=params, headers={"Authorization": "Bearer " + token}
            )
        if response.status_code != 200:
            return (
                None,
                "Saved cases are unavailable. Check the service, library company and migration, "
                "then Refresh.",
            )
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
        rows = []
        for item in data["items"]:
            case_id = _required_string(item, "case_id")
            if str(UUID(case_id)) != case_id:
                raise ValueError("Invalid identity.")
            parent = item["parent_id"]
            if parent is not None and str(UUID(parent)) != parent:
                raise ValueError("Invalid lineage.")
            if item["origin"] not in {"demo", "odoo"}:
                raise ValueError("Invalid origin.")
            status = {"draft": "Awaiting decision", "approved": "Approved", "no_award": "No-award"}[
                item["decision_status"]
            ]
            outcome = {
                "optimal": "Plans ready",
                "infeasible": "No feasible plan",
                "no_proven_optimum": "No proven optimum",
                "solver_error": "Solver error",
            }[item["planning_status"]]
            quantity = item["approved_quantity"]
            if type(quantity) is not int or quantity <= 0:
                raise ValueError("Invalid demand.")
            date.fromisoformat(item["required_date"])
            rows.append(
                {
                    "case_id": case_id,
                    "parent_id": parent or "",
                    "product": _required_string(item, "product_label"),
                    "context": f"{quantity} {_required_string(item, 'quantity_unit')} · "
                    f"{_required_string(item, 'currency')} · Required {item['required_date']}",
                    "company": _required_string(item, "company_id"),
                    "saved": _parse_datetime(item["created_at"]).isoformat(),
                    "decision": status
                    if parent is None
                    else "Scenario — decision belongs to original",
                    "outcome": outcome,
                    "origin": item["origin"],
                    "source": {
                        "controlled_synthetic": "Synthetic inputs and ML history",
                        "odoo_quotations_odoo_history": (
                            "Odoo quotations and receipts · controlled synthetic origin"
                        ),
                        "odoo_quotations_synthetic_history": (
                            "Captured Odoo quotations · synthetic ML history"
                        ),
                    }[item["source_kind"]],
                    "scenario": (item["scenario_kind"] or "").replace("_", " "),
                    "changes": ""
                    if item["changed_assumptions"] is None
                    else json.dumps(item["changed_assumptions"], sort_keys=True),
                }
            )
        if len({row["case_id"] for row in rows}) != len(rows):
            raise ValueError("Duplicate library row.")
        return {"items": rows, "next_cursor": cursor or ""}, ""
    except httpx.HTTPError:
        return None, "Saved cases are unavailable. Check the backend connection, then Refresh."
    except (ValueError, TypeError, KeyError, AttributeError):
        return (
            None,
            "Saved case data could not be verified. Refresh or ask the owner to check stored data.",
        )
