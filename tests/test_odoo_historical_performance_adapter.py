"""Contract tests for the bounded Odoo historical-performance adapter."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from application.historical_performance import HistoricalPerformanceQuery
from application.rfqs import ProcurementDataResponseError
from odoo_adapter.historical_performance_reader import OdooHistoricalPerformanceReader

WINDOW_END = datetime(2026, 9, 20, tzinfo=UTC)
WINDOW_START = WINDOW_END - timedelta(days=365)


def _query() -> HistoricalPerformanceQuery:
    return HistoricalPerformanceQuery(
        supplier_id="odoo:res.partner:31",
        company_id="odoo:res.company:1",
        purchase_line_ids=("odoo:purchase.order.line:21",),
        observation_window_start=WINDOW_START,
        observation_window_end=WINDOW_END,
        result_limit=10,
    )


def _record(**changes: Any) -> dict[str, Any]:
    record = {
        "company_id": 1,
        "commercial_partner_id": 31,
        "purchase_order_id": 11,
        "purchase_order_line_id": 21,
        "product_id": 41,
        "product_uom_id": 1,
        "expected_arrival_at": "2026-01-02 00:00:00",
        "stock_move_id": 51,
        "stock_picking_id": 61,
        "move_processed_at": "2026-01-01 00:00:00",
        "ordered_quantity": "100",
        "completed_quantity": "100",
        "state": "done",
        "source_location_usage": "supplier",
        "destination_location_usage": "internal",
        "backorder_of_picking_id": None,
        "return_of_move_id": None,
        "return_of_picking_id": None,
    }
    record.update(changes)
    return record


def _response(records: list[dict[str, Any]] | None = None, **changes: Any) -> dict[str, Any]:
    records = records if records is not None else [_record()]
    response = {
        "schema_version": "t7s.inventory_history.v1",
        "company_id": 1,
        "date_from": "2025-09-20 00:00:00",
        "date_to": "2026-09-20 00:00:00",
        "result_count": len(records),
        "records": records,
    }
    response.update(changes)
    return response


def _reader(handler) -> OdooHistoricalPerformanceReader:
    return OdooHistoricalPerformanceReader(
        base_url="https://odoo.example.test",
        database="procurement_poc",
        api_key="dedicated-projection-key",
        transport=httpx.MockTransport(handler),
    )


def test_adapter_uses_only_the_accepted_projection_and_maps_neutral_evidence() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_response())

    snapshot = asyncio.run(_reader(handler).read_inventory_history(_query()))

    assert len(requests) == 1
    assert requests[0].url.path == (
        "/json/2/procurement.inventory.history.projection/read_bounded_history"
    )
    payload = json.loads(requests[0].content)
    assert payload == {
        "company_id": 1,
        "date_from": "2025-09-20 00:00:00",
        "date_to": "2026-09-20 00:00:00",
        "purchase_order_line_ids": [21],
        "limit": 10,
    }
    assert snapshot.observations[0].supplier_id == "odoo:res.partner:31"
    assert snapshot.observations[0].purchase_line_id == "odoo:purchase.order.line:21"
    assert snapshot.source_type == "odoo_projection"
    assert "procurement.inventory.history.projection.read_bounded_history" in (
        snapshot.source_reference
    )
    assert "dedicated-projection-key" not in snapshot.source_reference


@pytest.mark.parametrize(
    "response",
    [
        _response(company_id=2),
        _response(date_to="2026-09-19 00:00:00"),
        _response(result_count=2),
        _response(schema_version="unexpected"),
        {key: value for key, value in _response().items() if key != "records"},
        _response([{key: value for key, value in _record().items() if key != "product_id"}]),
        _response([_record(company_id=2)]),
        _response([_record(commercial_partner_id=32)]),
        _response([_record(purchase_order_line_id=22)]),
        _response([_record(state="cancel")]),
        _response([_record(move_processed_at="2026-09-20 00:00:00")]),
    ],
)
def test_incomplete_or_inconsistent_projection_responses_fail_closed(
    response: dict[str, Any],
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response)

    with pytest.raises(ProcurementDataResponseError):
        asyncio.run(_reader(handler).read_inventory_history(_query()))


def test_projection_http_errors_are_translated_without_fallback_reads() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(403, json={"error": "denied"})

    with pytest.raises(ProcurementDataResponseError):
        asyncio.run(_reader(handler).read_inventory_history(_query()))

    assert paths == ["/json/2/procurement.inventory.history.projection/read_bounded_history"]


def test_noncanonical_odoo_identities_are_rejected_before_transport() -> None:
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json=_response())

    with pytest.raises(ProcurementDataResponseError):
        asyncio.run(
            _reader(handler).read_inventory_history(replace(_query(), company_id="company:1"))
        )
    assert called is False
