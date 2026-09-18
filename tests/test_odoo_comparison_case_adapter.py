"""Fast contract tests for the read-only T6 Odoo comparison-case reader."""

import asyncio
from decimal import Decimal

import httpx
import pytest

from application.rfqs import ProcurementDataResponseError
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader


def _payloads() -> dict[str, object]:
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


def test_reader_requests_explicit_group_and_maps_only_validated_facts() -> None:
    payloads = _payloads()
    calls: list[tuple[str, dict[str, object]]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        calls.append((request.url.path, body))
        if request.url.path.endswith("/purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if request.url.path.endswith("/purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        if request.url.path.endswith("/purchase.order.line/search_read"):
            return httpx.Response(200, json=payloads["lines"])
        if request.url.path.endswith("/res.partner/search_read"):
            return httpx.Response(200, json=payloads["partners"])
        raise AssertionError(request.url.path)

    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test/",
        database="procurement_poc",
        api_key="secret",
        transport=httpx.MockTransport(respond),
    )

    facts = asyncio.run(reader.read_comparison_case(501))

    assert facts.comparison_case_id == "odoo:purchase.order.group:501"
    assert [offer.order_reference for offer in facts.offers] == [
        "T6-RFQ-A",
        "T6-RFQ-B",
        "T6-RFQ-C",
    ]
    assert facts.offers[0].supplier_id == "odoo:res.partner:301"
    assert facts.offers[0].supplier_source_reference == "odoo:res.partner:301#commercial_partner_id"
    assert facts.offers[0].lines[0].quantity == Decimal("100.0")
    assert facts.offers[2].lines[0].unit_price == Decimal("9.0")
    assert all(offer.observed_at.tzinfo is not None for offer in facts.offers)
    assert calls[0][1] == {"domain": [["purchase_group_id", "=", 501]]}
    assert calls[1][1]["domain"] == [["purchase_group_id", "=", 501]]
    assert calls[2][1]["domain"] == [["id", "in", [201, 202, 203]]]
    assert "date_planned" not in calls[2][1]["fields"]
    assert "selected_seller_id" not in calls[2][1]["fields"]


def test_reader_preserves_unsupported_values_for_fail_closed_application_validation() -> None:
    payloads = _payloads()
    payloads["orders"][0]["state"] = "purchase"  # type: ignore[index]
    payloads["lines"][0]["discount"] = 5.0  # type: ignore[index]
    payloads["lines"][0]["tax_ids"] = [7]  # type: ignore[index]

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if request.url.path.endswith("/purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        if request.url.path.endswith("/purchase.order.line/search_read"):
            return httpx.Response(200, json=payloads["lines"])
        return httpx.Response(200, json=payloads["partners"])

    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
        transport=httpx.MockTransport(respond),
    )
    facts = asyncio.run(reader.read_comparison_case(501))

    assert facts.offers[0].state == "purchase"
    assert facts.offers[0].lines[0].discount == Decimal("5.0")
    assert facts.offers[0].lines[0].tax_ids == ("odoo:account.tax:7",)


def test_reader_rejects_unbounded_or_invalid_upstream_payloads() -> None:
    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=21)),
    )

    with pytest.raises(ProcurementDataResponseError, match="safety bound"):
        asyncio.run(reader.read_comparison_case(501))


def test_reader_rejects_unbounded_grouped_line_set() -> None:
    payloads = _payloads()
    payloads["orders"][0]["order_line"] = list(range(1, 42))  # type: ignore[index]

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/purchase.order/search_count"):
            return httpx.Response(200, json=3)
        return httpx.Response(200, json=payloads["orders"])

    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
        transport=httpx.MockTransport(respond),
    )

    with pytest.raises(ProcurementDataResponseError, match="line safety bound"):
        asyncio.run(reader.read_comparison_case(501))


def test_reader_rejects_incomplete_grouped_line_response() -> None:
    payloads = _payloads()

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if request.url.path.endswith("/purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        return httpx.Response(200, json=payloads["lines"][:-1])  # type: ignore[index]

    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
        transport=httpx.MockTransport(respond),
    )

    with pytest.raises(ProcurementDataResponseError, match="invalid comparison-case payload"):
        asyncio.run(reader.read_comparison_case(501))


@pytest.mark.parametrize("group_id", [0, -1, True, "501"])
def test_reader_rejects_invalid_group_identity(group_id: object) -> None:
    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
    )

    with pytest.raises(ValueError):
        asyncio.run(reader.read_comparison_case(group_id))  # type: ignore[arg-type]
