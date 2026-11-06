"""Fake read-only Odoo: quotation group 501, generated purchase history, trained model.

``build_history`` turns the seeder's generated plan into Odoo-shaped history and trains the
supplier tree on it; ``install_fake_odoo`` answers every Odoo read the backend makes from it.
"""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from pydantic import SecretStr

from application.purchase_history import PurchaseLineHistory, ReceiptEvent
from backend.app.config import settings
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.product_history_reader import OdooProductHistoryReader
from supplier_evaluation.history_model import save_model, train
from supplier_evaluation.purchase_history import build_rows, split_rows
from tools.seed_odoo_history import ALLOWED_DATABASE, build_plan

DATABASE = ALLOWED_DATABASE
COMPANY = "odoo:res.company:1"
PRODUCTS = {"PRD-01": 42, "PRD-02": 43, "PRD-03": 44}
QUOTED = (1, 4, 6)  # SUP-01 reliable, SUP-04 steady late, SUP-06 deteriorating; all sell PRD-01


def quotation_payloads() -> dict[str, object]:
    """Odoo JSON-2 records of open quotation group 501: three quotations of one product."""
    orders = [
        {
            "id": 101,
            "name": "T6-RFQ-A",
            "partner_id": [301, "T6 Supplier A"],
            "state": "draft",
            "currency_id": [2, "USD"],
            "company_id": [1, "My Company"],
            "purchase_group_id": [501, "T6-COMP-001"],
            "order_line": [201],
        },
        {
            "id": 102,
            "name": "T6-RFQ-B",
            "partner_id": [302, "T6 Supplier B"],
            "state": "sent",
            "currency_id": [2, "USD"],
            "company_id": [1, "My Company"],
            "purchase_group_id": [501, "T6-COMP-001"],
            "order_line": [202],
        },
        {
            "id": 103,
            "name": "T6-RFQ-C",
            "partner_id": [303, "T6 Supplier C"],
            "state": "to approve",
            "currency_id": [2, "USD"],
            "company_id": [1, "My Company"],
            "purchase_group_id": [501, "T6-COMP-001"],
            "order_line": [203],
        },
    ]
    lines = [
        {
            "id": 201 + index,
            "order_id": [101 + index, f"T6-RFQ-{letter}"],
            "product_id": [42, "T6 Comparison Product"],
            "product_uom_id": [1, "Units"],
            "product_qty": 100.0,
            "price_unit": price,
            "discount": 0.0,
            "tax_ids": [],
            "currency_id": [2, "USD"],
            "company_id": [1, "My Company"],
        }
        for index, (letter, price) in enumerate((("A", 10.0), ("B", 12.0), ("C", 9.0)))
    ]
    partners = [
        {"id": 301 + index, "commercial_partner_id": [301 + index, f"T6 Supplier {letter}"]}
        for index, letter in enumerate(("A", "B", "C"))
    ]
    return {"orders": orders, "lines": lines, "partners": partners}


def plan_lines(now):
    """The seeder's generated plan as neutral Odoo-shaped history (no Odoo involved)."""
    plan = build_plan(now)
    out = []
    for n, order in enumerate(plan.orders, 1):
        out.append(
            PurchaseLineHistory(
                f"odoo:purchase.order.line:{n}",
                f"odoo:purchase.order:{n}",
                COMPANY,
                f"odoo:res.partner:{300 + int(order.supplier[4:])}",
                f"odoo:product.product:{PRODUCTS[order.product]}",
                "odoo:uom.uom:1",
                Decimal(order.quantity),
                order.expected_at,
                order.ordered_at + timedelta(hours=2),
                tuple(
                    ReceiptEvent(f"odoo:stock.move:{n}{i}", r.at, Decimal(r.quantity))
                    for i, r in enumerate(order.receipts)
                ),
            )
        )
    return tuple(out)


def build_history(directory, now=None):
    """Generated Odoo-shaped history ending at ``now`` and a tree trained on it."""
    now = now or datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    lines = plan_lines(now)
    rows, coverage = build_rows(lines, extracted_at=now)
    boundary = max(r.cutoff for r in rows) - timedelta(days=92)
    boundary = boundary.replace(day=1 if boundary.day < 16 else 16)
    split = split_rows(rows, boundary=boundary)
    model = train(split, database=DATABASE, data_origin="generated")
    save_model(model, directory)
    return {
        "now": now,
        "lines": lines,
        "rows": rows,
        "split": split,
        "model": model,
        "dir": directory,
    }


def export_response(lines, data):
    start = datetime.strptime(data["date_from"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    end = datetime.strptime(data["date_to"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    fmt = "%Y-%m-%d %H:%M:%S"
    chosen = [
        x
        for x in lines
        if x.product_id == f"odoo:product.product:{data['product_id']}"
        and start <= x.expected_at < end
    ]
    records = [
        {
            "purchase_order_line_id": int(x.line_id.rsplit(":", 1)[1]),
            "purchase_order_id": int(x.order_id.rsplit(":", 1)[1]),
            "commercial_partner_id": int(x.supplier_id.rsplit(":", 1)[1]),
            "product_uom_id": 1,
            "ordered_quantity": f"{x.ordered_quantity}.0",
            "expected_arrival_at": x.expected_at.strftime(fmt),
            "order_confirmed_at": x.confirmed_at.strftime(fmt),
            "receipts": [
                {"stock_move_id": int(r.event_id.rsplit(":", 1)[1]), "stock_picking_id": 1,
                 "processed_at": r.received_at.strftime(fmt), "quantity": f"{r.quantity}.0",
                 "backorder_of_picking_id": None}
                for r in x.receipts
            ],
            "returned_quantity": "0",
        }
        for x in chosen
    ]  # fmt: skip
    return {
        "schema_version": "pdss.product_history.v1",
        "company_id": data["company_id"],
        "product_id": data["product_id"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "result_count": len(records),
        "lines": records,
    }


def install_fake_odoo(history, monkeypatch):
    """Fake read-only Odoo (group 501, its history) plus the trained history model."""
    payloads, calls = quotation_payloads(), []
    for order, quote_line, partner, n in zip(
        payloads["orders"], payloads["lines"], payloads["partners"], QUOTED, strict=True
    ):
        order["partner_id"] = [300 + n, f"Supplier {n}"]
        order["date_order"] = "2026-10-15 08:00:00"
        partner.update(id=300 + n, commercial_partner_id=[300 + n, f"Supplier {n}"])
        quote_line["product_qty"] = 200.0

    def respond(request):
        data = json.loads(request.content)
        calls.append(request.url.path)
        assert request.headers["X-Odoo-Database"] == DATABASE
        if request.url.path.endswith("read_product_history"):
            assert request.headers["Authorization"] == "Bearer history-only"
            return httpx.Response(200, json=export_response(history["lines"], data))
        assert request.headers["Authorization"] == "Bearer rfq-only"
        path = request.url.path
        if path.endswith("purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if path.endswith("purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        if path.endswith("purchase.order.line/search_read"):
            return httpx.Response(200, json=payloads["lines"])
        if path.endswith("res.partner/search_read"):
            return httpx.Response(200, json=payloads["partners"])
        if path.endswith("res.currency/search_read"):
            return httpx.Response(200, json=[{"id": 2, "name": "USD"}])
        raise AssertionError(path)

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(
        "backend.app.dependencies.get_comparison_case_reader",
        lambda: OdooComparisonCaseReader(
            base_url="http://odoo.test", database=DATABASE, api_key="rfq-only", transport=transport
        ),
    )
    monkeypatch.setattr(
        "backend.app.dependencies.get_purchase_history_reader",
        lambda: OdooProductHistoryReader(
            base_url="http://odoo.test",
            database=DATABASE,
            api_key="history-only",
            transport=transport,
        ),
    )
    monkeypatch.setattr(settings, "odoo_database", DATABASE)
    monkeypatch.setattr(settings, "odoo_history_data_origin", "generated")
    monkeypatch.setattr(settings, "supplier_history_model_directory", history["dir"])
    monkeypatch.setattr(settings, "api_service_token", SecretStr("history-test-token"))
    return calls
