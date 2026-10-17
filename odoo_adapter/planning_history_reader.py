"""Fixed profile acquisition through existing restricted Odoo read paths."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx

from application.historical_performance import HistoricalPerformanceQuery
from application.planning_history import build_capture
from application.rfqs import ProcurementDataResponseError
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.historical_performance_reader import OdooHistoricalPerformanceReader
from supplier_evaluation.contracts import digest

PROFILE_PATH = Path(__file__).resolve().parents[1] / "config/odoo_history_local_v1.json"


def local_profile():
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


class OdooPlanningHistoryReader:
    def __init__(self, *, base_url, database, api_key, history_key, transport=None):
        self.database, self.base_url, self.api_key = database, base_url.rstrip("/"), api_key
        self.transport = transport
        self.quotations = OdooComparisonCaseReader(
            base_url=base_url, database=database, api_key=api_key, transport=transport
        )
        self.history = OdooHistoricalPerformanceReader(
            base_url=base_url, database=database, api_key=history_key, transport=transport
        )

    async def capture(self, revision):
        profile = local_profile()
        if self.database != profile["database"] or revision != digest(profile):
            raise ValueError("History database or profile revision mismatch.")
        markers = ["V2-SYNTH-HIST-v1-" + r["code"] for r in profile["records"]]
        async with httpx.AsyncClient(
            timeout=15,
            transport=self.transport,
            headers={"Authorization": "Bearer " + self.api_key, "X-Odoo-Database": self.database},
        ) as client:

            async def read(model, payload):
                response = await client.post(
                    f"{self.base_url}/json/2/{model}/search_read", json=payload
                )
                if response.status_code != 200:
                    raise ProcurementDataResponseError(
                        f"Bounded history identity read HTTP {response.status_code}"
                    )
                return response.json()

            orders = await read(
                "purchase.order",
                {
                    "domain": [
                        ["origin", "in", markers],
                        ["company_id", "=", profile["company_id"]],
                    ],
                    "fields": [
                        "id",
                        "origin",
                        "state",
                        "company_id",
                        "partner_id",
                        "currency_id",
                        "purchase_group_id",
                        "order_line",
                    ],
                    "limit": 10,
                    "order": "id asc",
                },
            )
            if len(orders) != 9 or len({o["origin"] for o in orders}) != 9:
                raise ValueError("Missing or duplicate history order markers.")
            lines = await read(
                "purchase.order.line",
                {
                    "domain": [["id", "in", [r["line"] for r in profile["records"]]]],
                    "fields": [
                        "id",
                        "order_id",
                        "product_id",
                        "company_id",
                        "product_uom_id",
                        "product_qty",
                        "qty_received",
                        "qty_received_method",
                        "price_unit",
                        "discount",
                        "tax_ids",
                        "date_planned",
                    ],
                    "limit": 10,
                    "order": "id asc",
                },
            )
        if len(lines) != 9 or len({line["id"] for line in lines}) != 9:
            raise ValueError("Missing or duplicate history lines.")
        by_order, by_line = {o["id"]: o for o in orders}, {line["id"]: line for line in lines}
        for record in profile["records"]:
            order, line = by_order.get(record["order"]), by_line.get(record["line"])
            if (
                not order
                or not line
                or order["origin"] != "V2-SYNTH-HIST-v1-" + record["code"]
                or order["state"] not in {"purchase", "done"}
                or order["order_line"] != [record["line"]]
                or order["company_id"][0] != profile["company_id"]
                or order["partner_id"][0] != record["supplier"]
                or order["currency_id"][0] != profile["currency_id"]
                or order["purchase_group_id"] is not False
                or line["order_id"][0] != record["order"]
                or line["product_id"][0] != profile["product_id"]
                or line["product_uom_id"][0] != profile["unit_id"]
                or line["company_id"][0] != profile["company_id"]
                or line["qty_received_method"] != "stock_moves"
                or line["date_planned"] != record["deadline"]
                or line["tax_ids"]
                or any(
                    Decimal(str(line[k])) != Decimal(v)
                    for k, v in {
                        "product_qty": "100",
                        "qty_received": "100",
                        "price_unit": record["price"],
                        "discount": "0",
                    }.items()
                )
            ):
                raise ValueError("History identity, price, unit or schedule mismatch.")
        case = await self.quotations.read_comparison_case(profile["purchase_group_id"])
        expected_quotes = {
            (
                f"odoo:purchase.order:{q['order']}",
                f"odoo:purchase.order.line:{q['line']}",
                f"odoo:res.partner:{q['supplier']}",
            )
            for q in profile["quotations"]
        }
        if (
            len(case.offers) != 3
            or {(o.offer_id, o.lines[0].line_id, o.supplier_id) for o in case.offers}
            != expected_quotes
            or any(
                len(o.lines) != 1
                or o.company_id != f"odoo:res.company:{profile['company_id']}"
                or o.currency_id != f"odoo:res.currency:{profile['currency_id']}"
                or o.lines[0].product_id != f"odoo:product.product:{profile['product_id']}"
                or o.lines[0].uom_id != f"odoo:uom.uom:{profile['unit_id']}"
                for o in case.offers
            )
        ):
            raise ValueError("Quotation identities or context do not match the history profile.")
        code, observed = await self.quotations.read_currency_code(case.offers[0].currency_id)
        end = datetime.now(UTC).replace(microsecond=0)
        snapshots = []
        for supplier in (51, 52, 53):
            ids = tuple(
                f"odoo:purchase.order.line:{r['line']}"
                for r in profile["records"]
                if r["supplier"] == supplier
            )
            query = HistoricalPerformanceQuery(
                f"odoo:res.partner:{supplier}",
                f"odoo:res.company:{profile['company_id']}",
                ids,
                end - timedelta(days=365),
                end,
                10,
            )
            snapshots.append(await self.history.read_inventory_history(query))
        encoded = build_capture(profile, tuple(snapshots), {"orders": orders, "lines": lines})
        return case, code, observed, encoded
