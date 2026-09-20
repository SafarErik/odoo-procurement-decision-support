"""Read the accepted bounded inventory-history projection through Odoo JSON-2."""

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from application.historical_performance import (
    HistoricalPerformanceQuery,
    InventoryHistoryObservation,
    InventoryHistorySnapshot,
    ReceiptDirection,
    ReceiptEventState,
)
from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable

_MODEL = "procurement.inventory.history.projection"
_METHOD = "read_bounded_history"
_SCHEMA_VERSION = "t7s.inventory_history.v1"
_ENVELOPE_FIELDS = {
    "schema_version",
    "company_id",
    "date_from",
    "date_to",
    "result_count",
    "records",
}
_RECORD_FIELDS = {
    "company_id",
    "commercial_partner_id",
    "purchase_order_id",
    "purchase_order_line_id",
    "product_id",
    "product_uom_id",
    "expected_arrival_at",
    "stock_move_id",
    "stock_picking_id",
    "move_processed_at",
    "ordered_quantity",
    "completed_quantity",
    "state",
    "source_location_usage",
    "destination_location_usage",
    "backorder_of_picking_id",
    "return_of_move_id",
    "return_of_picking_id",
}
_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class OdooHistoricalPerformanceReader:
    """Adapter exposing only the approved T7-S projection as a neutral port."""

    def __init__(
        self,
        *,
        base_url: str,
        database: str,
        api_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._database = database
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def read_inventory_history(
        self, query: HistoricalPerformanceQuery
    ) -> InventoryHistorySnapshot:
        """Read and fail-closed map one exact bounded projection response."""

        if not self._base_url or not self._database or not self._api_key:
            raise ProcurementDataUnavailable("Odoo historical projection is not configured")
        try:
            company_id = _prefixed_id(query.company_id, "odoo:res.company:")
            line_ids = [
                _prefixed_id(line_id, "odoo:purchase.order.line:")
                for line_id in query.purchase_line_ids
            ]
            payload = {
                "company_id": company_id,
                "date_from": _odoo_datetime(query.observation_window_start),
                "date_to": _odoo_datetime(query.observation_window_end),
                "purchase_order_line_ids": line_ids,
                "limit": query.result_limit,
            }
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Odoo-Database": self._database,
                    "User-Agent": "odoo-procurement-decision-support/0.0.1",
                },
            ) as client:
                response = await client.post(
                    f"{self._base_url}/json/2/{_MODEL}/{_METHOD}", json=payload
                )
                response.raise_for_status()
                result = response.json()
            observations = _map_response(result, query, payload)
        except httpx.RequestError as error:
            raise ProcurementDataUnavailable(
                "Odoo historical projection could not be reached"
            ) from error
        except httpx.HTTPStatusError as error:
            raise ProcurementDataResponseError(
                f"Odoo historical projection returned HTTP {error.response.status_code}"
            ) from error
        except ProcurementDataResponseError:
            raise
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProcurementDataResponseError(
                "Odoo historical projection returned an invalid response"
            ) from error

        observed_at = datetime.now(UTC)
        source_reference = (
            f"{_MODEL}.{_METHOD}|company={query.company_id}|"
            f"window=[{query.observation_window_start.isoformat()},"
            f"{query.observation_window_end.isoformat()})|"
            f"lines={','.join(sorted(query.purchase_line_ids))}"
        )
        return InventoryHistorySnapshot(
            query=query,
            observations=observations,
            observed_at=observed_at,
            source_type="odoo_projection",
            source_reference=source_reference,
        )


def _map_response(
    result: Any,
    query: HistoricalPerformanceQuery,
    payload: dict[str, Any],
) -> tuple[InventoryHistoryObservation, ...]:
    if not isinstance(result, Mapping) or set(result) != _ENVELOPE_FIELDS:
        raise TypeError("Unexpected projection envelope")
    if result["schema_version"] != _SCHEMA_VERSION:
        raise TypeError("Unexpected projection schema version")
    if result["company_id"] != payload["company_id"]:
        raise TypeError("Projection company does not match the request")
    if result["date_from"] != payload["date_from"] or result["date_to"] != payload["date_to"]:
        raise TypeError("Projection window does not match the request")
    records = result["records"]
    if not isinstance(records, list):
        raise TypeError("Projection records must be a list")
    result_count = result["result_count"]
    if (
        isinstance(result_count, bool)
        or not isinstance(result_count, int)
        or result_count != len(records)
        or result_count > query.result_limit
    ):
        raise TypeError("Projection result count is inconsistent")

    mapped = tuple(_map_record(record) for record in records)
    if len({item.receipt_event_id for item in mapped}) != len(mapped):
        raise TypeError("Projection contains duplicate stock-move identities")
    requested_lines = set(query.purchase_line_ids)
    if any(item.purchase_line_id not in requested_lines for item in mapped):
        raise TypeError("Projection returned an unrequested purchase line")
    if any(item.company_id != query.company_id for item in mapped):
        raise TypeError("Projection returned another company")
    if any(item.supplier_id != query.supplier_id for item in mapped):
        raise TypeError("Projection returned another supplier")
    if any(
        not query.observation_window_start <= item.completed_at < query.observation_window_end
        for item in mapped
    ):
        raise TypeError("Projection returned an event outside the requested window")
    return tuple(sorted(mapped, key=lambda item: (item.completed_at, item.receipt_event_id)))


def _map_record(record: Any) -> InventoryHistoryObservation:
    if not isinstance(record, Mapping) or set(record) != _RECORD_FIELDS:
        raise TypeError("Unexpected projection record schema")
    if record["state"] != "done":
        raise TypeError("Projection returned an unsupported stock-move state")
    direction_value = (
        _required_string(record, "source_location_usage"),
        _required_string(record, "destination_location_usage"),
    )
    directions = {
        ("supplier", "internal"): ReceiptDirection.SUPPLIER_TO_INTERNAL,
        ("internal", "supplier"): ReceiptDirection.INTERNAL_TO_SUPPLIER,
    }
    if direction_value not in directions:
        raise TypeError("Projection returned an unsupported stock-move direction")
    return InventoryHistoryObservation(
        company_id=f"odoo:res.company:{_required_int(record, 'company_id')}",
        supplier_id=f"odoo:res.partner:{_required_int(record, 'commercial_partner_id')}",
        purchase_document_id=f"odoo:purchase.order:{_required_int(record, 'purchase_order_id')}",
        purchase_line_id=(
            f"odoo:purchase.order.line:{_required_int(record, 'purchase_order_line_id')}"
        ),
        product_id=f"odoo:product.product:{_required_int(record, 'product_id')}",
        uom_id=f"odoo:uom.uom:{_required_int(record, 'product_uom_id')}",
        scheduled_arrival_at=_parse_datetime(record["expected_arrival_at"]),
        receipt_event_id=f"odoo:stock.move:{_required_int(record, 'stock_move_id')}",
        transfer_id=f"odoo:stock.picking:{_required_int(record, 'stock_picking_id')}",
        completed_at=_parse_datetime(record["move_processed_at"]),
        ordered_quantity=_positive_decimal(record, "ordered_quantity"),
        completed_quantity=_positive_decimal(record, "completed_quantity"),
        state=ReceiptEventState.COMPLETED,
        direction=directions[direction_value],
        backorder_of_transfer_id=_optional_id(
            record, "backorder_of_picking_id", "odoo:stock.picking:"
        ),
        return_of_event_id=_optional_id(record, "return_of_move_id", "odoo:stock.move:"),
        return_of_transfer_id=_optional_id(record, "return_of_picking_id", "odoo:stock.picking:"),
    )


def _odoo_datetime(value: datetime) -> str:
    return value.astimezone(UTC).replace(tzinfo=None).strftime(_DATETIME_FORMAT)


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError("Projection datetime must be a string")
    parsed = datetime.strptime(value, _DATETIME_FORMAT)
    if parsed.strftime(_DATETIME_FORMAT) != value:
        raise ValueError("Projection datetime is not canonical")
    return parsed.replace(tzinfo=UTC)


def _prefixed_id(value: str, prefix: str) -> int:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError("Identity has an unsupported source prefix")
    suffix = value.removeprefix(prefix)
    if not suffix.isdigit() or int(suffix) <= 0 or str(int(suffix)) != suffix:
        raise ValueError("Identity does not contain a canonical positive integer")
    return int(suffix)


def _required_int(record: Mapping[str, Any], field: str) -> int:
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError(f"Expected a positive integer for {field}")
    return value


def _required_string(record: Mapping[str, Any], field: str) -> str:
    value = record[field]
    if not isinstance(value, str) or not value:
        raise TypeError(f"Expected a non-empty string for {field}")
    return value


def _positive_decimal(record: Mapping[str, Any], field: str) -> Decimal:
    value = Decimal(str(record[field]))
    if not value.is_finite() or value <= 0:
        raise InvalidOperation
    return value


def _optional_id(record: Mapping[str, Any], field: str, prefix: str) -> str | None:
    value = record[field]
    if value is None or value is False:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError(f"Expected an optional positive integer for {field}")
    return f"{prefix}{value}"
