"""Read the narrow T6 Odoo comparison-case fact contract through JSON-2."""

from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from application.decision_input_assembly import (
    OdooComparisonCaseFacts,
    OdooComparisonOfferFacts,
    OdooOrderLineFacts,
)
from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable

_MAX_GROUP_OFFERS = 20
_MAX_GROUP_LINES = 40
_ORDER_FIELDS = (
    "id",
    "name",
    "partner_id",
    "state",
    "currency_id",
    "company_id",
    "purchase_group_id",
    "order_line",
)
_LINE_FIELDS = (
    "id",
    "order_id",
    "product_id",
    "product_uom_id",
    "product_qty",
    "price_unit",
    "discount",
    "tax_ids",
    "currency_id",
    "company_id",
)


class OdooComparisonCaseReader:
    """Retrieve typed Odoo facts without supplying missing business semantics."""

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

    async def read_comparison_case(self, purchase_group_id: int) -> OdooComparisonCaseFacts:
        """Read all RFQs and lines in one explicit persisted alternative group."""

        if not self._base_url or not self._database or not self._api_key:
            raise ProcurementDataUnavailable("Odoo integration is not configured")
        if isinstance(purchase_group_id, bool) or not isinstance(purchase_group_id, int):
            raise ValueError("purchase_group_id must be an integer")
        if purchase_group_id <= 0:
            raise ValueError("purchase_group_id must be greater than zero")

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Odoo-Database": self._database,
                    "User-Agent": "odoo-procurement-decision-support/0.0.1",
                },
            ) as client:
                count = await self._post(
                    client,
                    "purchase.order",
                    "search_count",
                    {"domain": [["purchase_group_id", "=", purchase_group_id]]},
                )
                if isinstance(count, bool) or not isinstance(count, int):
                    raise TypeError("Expected an integer purchase.order count")
                if count > _MAX_GROUP_OFFERS:
                    raise ProcurementDataResponseError(
                        f"Odoo comparison case exceeds the {_MAX_GROUP_OFFERS}-offer safety bound"
                    )
                orders = await self._post(
                    client,
                    "purchase.order",
                    "search_read",
                    {
                        "domain": [["purchase_group_id", "=", purchase_group_id]],
                        "fields": list(_ORDER_FIELDS),
                        "limit": _MAX_GROUP_OFFERS,
                        "order": "id asc",
                    },
                )
                if not isinstance(orders, list):
                    raise TypeError("Expected a purchase.order list")
                if len(orders) != count:
                    raise TypeError("purchase.order count changed during the bounded read")
                line_ids = [
                    line_id for order in orders for line_id in _integer_list(order, "order_line")
                ]
                if len(line_ids) > _MAX_GROUP_LINES:
                    raise ProcurementDataResponseError(
                        f"Odoo comparison case exceeds the {_MAX_GROUP_LINES}-line safety bound"
                    )
                lines = await self._post(
                    client,
                    "purchase.order.line",
                    "search_read",
                    {
                        "domain": [["id", "in", line_ids]],
                        "fields": list(_LINE_FIELDS),
                        "limit": _MAX_GROUP_LINES,
                        "order": "id asc",
                    },
                )
                if not isinstance(lines, list):
                    raise TypeError("Expected a purchase.order.line list")
                if {_required_int(line, "id") for line in lines} != set(line_ids):
                    raise TypeError("Odoo did not return the complete grouped order-line set")
                partner_ids = [_many2one_id(order, "partner_id") for order in orders]
                partners = await self._post(
                    client,
                    "res.partner",
                    "search_read",
                    {
                        "domain": [["id", "in", partner_ids]],
                        "fields": ["id", "commercial_partner_id"],
                        "limit": len(partner_ids),
                        "order": "id asc",
                    },
                )
                if not isinstance(partners, list):
                    raise TypeError("Expected a res.partner list")
        except httpx.RequestError as error:
            raise ProcurementDataUnavailable("Odoo could not be reached") from error
        except httpx.HTTPStatusError as error:
            raise ProcurementDataResponseError(
                f"Odoo returned HTTP {error.response.status_code}"
            ) from error
        except ProcurementDataResponseError:
            raise
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProcurementDataResponseError(
                "Odoo returned an invalid comparison-case payload"
            ) from error

        try:
            observed_at = datetime.now(UTC)
            return _map_case(purchase_group_id, orders, lines, partners, observed_at)
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProcurementDataResponseError(
                "Odoo returned an invalid comparison-case payload"
            ) from error

    async def read_currency_code(self, currency_id: str) -> tuple[str, datetime]:
        """Resolve one already selected currency; no conversion or broad discovery."""
        from odoo_adapter.historical_performance_reader import _prefixed_id

        identifier = _prefixed_id(currency_id, "odoo:res.currency:")
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Odoo-Database": self._database,
                },
            ) as client:
                rows = await self._post(
                    client,
                    "res.currency",
                    "search_read",
                    {
                        "domain": [["id", "=", identifier]],
                        "fields": ["id", "name"],
                        "limit": 2,
                    },
                )
            if not isinstance(rows, list) or len(rows) != 1 or rows[0]["id"] != identifier:
                raise ValueError("Missing selected currency.")
            code = _required_string(rows[0], "name")
            if len(code) != 3 or not code.isascii() or not code.isalpha() or not code.isupper():
                raise ValueError("Unsupported currency code.")
            return code, datetime.now(UTC)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProcurementDataUnavailable("Selected Odoo currency is unavailable.") from error

    async def _post(
        self,
        client: httpx.AsyncClient,
        model: str,
        method: str,
        payload: dict[str, Any],
    ) -> Any:
        response = await client.post(
            f"{self._base_url}/json/2/{model}/{method}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def _map_case(
    purchase_group_id: int,
    orders: list[Any],
    lines: list[Any],
    partners: list[Any],
    observed_at: datetime,
) -> OdooComparisonCaseFacts:
    case_id = f"odoo:purchase.order.group:{purchase_group_id}"
    commercial_by_partner = {
        _required_int(partner, "id"): _many2one_id(partner, "commercial_partner_id")
        for partner in partners
    }
    lines_by_order: dict[int, list[OdooOrderLineFacts]] = defaultdict(list)
    for line in lines:
        order_id = _many2one_id(line, "order_id")
        line_id = _required_int(line, "id")
        lines_by_order[order_id].append(
            OdooOrderLineFacts(
                line_id=f"odoo:purchase.order.line:{line_id}",
                product_id=f"odoo:product.product:{_many2one_id(line, 'product_id')}",
                uom_id=f"odoo:uom.uom:{_many2one_id(line, 'product_uom_id')}",
                quantity=_decimal(line, "product_qty"),
                unit_price=_decimal(line, "price_unit"),
                discount=_decimal(line, "discount"),
                tax_ids=tuple(
                    f"odoo:account.tax:{tax_id}" for tax_id in _integer_list(line, "tax_ids")
                ),
                currency_id=f"odoo:res.currency:{_many2one_id(line, 'currency_id')}",
                company_id=f"odoo:res.company:{_many2one_id(line, 'company_id')}",
            )
        )

    mapped_offers = []
    for order in orders:
        order_id = _required_int(order, "id")
        partner_id = _many2one_id(order, "partner_id")
        group_id = _many2one_id(order, "purchase_group_id")
        commercial_partner_id = commercial_by_partner[partner_id]
        mapped_offers.append(
            OdooComparisonOfferFacts(
                offer_id=f"odoo:purchase.order:{order_id}",
                order_reference=_required_string(order, "name"),
                comparison_case_id=f"odoo:purchase.order.group:{group_id}",
                supplier_id=f"odoo:res.partner:{commercial_partner_id}",
                supplier_source_reference=(f"odoo:res.partner:{partner_id}#commercial_partner_id"),
                state=_required_string(order, "state"),
                currency_id=f"odoo:res.currency:{_many2one_id(order, 'currency_id')}",
                company_id=f"odoo:res.company:{_many2one_id(order, 'company_id')}",
                lines=tuple(lines_by_order[order_id]),
                observed_at=observed_at,
            )
        )

    return OdooComparisonCaseFacts(
        comparison_case_id=case_id,
        offers=tuple(mapped_offers),
        observed_at=observed_at,
    )


def _required_int(record: Any, field: str) -> int:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise TypeError(f"Expected a positive integer for {field}")
    return value


def _many2one_id(record: Any, field: str) -> int:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if (
        not isinstance(value, (list, tuple))
        or len(value) < 1
        or isinstance(value[0], bool)
        or not isinstance(value[0], int)
        or value[0] <= 0
    ):
        raise TypeError(f"Expected a many2one identity for {field}")
    return value[0]


def _required_string(record: Any, field: str) -> str:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return value


def _decimal(record: Any, field: str) -> Decimal:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = Decimal(str(record[field]))
    if not value.is_finite():
        raise InvalidOperation
    return value


def _integer_list(record: Any, field: str) -> tuple[int, ...]:
    if not isinstance(record, Mapping):
        raise TypeError("Expected an Odoo record object")
    value = record[field]
    if not isinstance(value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value
    ):
        raise TypeError(f"Expected positive integer identities for {field}")
    return tuple(value)
