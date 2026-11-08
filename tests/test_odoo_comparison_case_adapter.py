"""Read-only Odoo comparison-case (quotation group) reader with mocked transport."""

import asyncio
from decimal import Decimal

import httpx
import pytest

from application.errors import ProcurementDataResponseError, ProcurementDataUnavailable
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from tests.helpers.odoo_fakes import quotation_payloads


def test_reader_requests_explicit_group_and_maps_only_validated_facts() -> None:
    payloads = quotation_payloads()
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
    payloads = quotation_payloads()
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
    payloads = quotation_payloads()
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
    payloads = quotation_payloads()

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


@pytest.mark.parametrize("change", ["other_order", "listed_twice"])
def test_reader_rejects_a_line_that_does_not_belong_to_the_order_listing_it(change) -> None:
    payloads = quotation_payloads()
    if change == "other_order":  # line 201 is listed by order 101 but claims order 102
        payloads["lines"][0]["order_id"] = [102, "T6-RFQ-B"]  # type: ignore[index]
    else:  # order 102 also lists order 101's line 201
        payloads["orders"][1]["order_line"] = [202, 201]  # type: ignore[index]

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

    with pytest.raises(ProcurementDataResponseError, match="invalid comparison-case payload"):
        asyncio.run(reader.read_comparison_case(501))


def _down(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("refused", request=request)


@pytest.mark.parametrize(
    ("respond", "error", "message"),
    [
        (_down, ProcurementDataUnavailable, "could not be reached"),
        (lambda request: httpx.Response(500), ProcurementDataResponseError, "HTTP 500"),
    ],
)
def test_unreachable_odoo_and_http_errors_map_to_distinct_errors(respond, error, message) -> None:
    """Unreachable Odoo must become 'unavailable' (503), an HTTP error 'bad response' (502)."""
    reader = OdooComparisonCaseReader(
        base_url="http://odoo.example.test",
        database="db",
        api_key="key",
        transport=httpx.MockTransport(respond),
    )

    with pytest.raises(error, match=message):
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
