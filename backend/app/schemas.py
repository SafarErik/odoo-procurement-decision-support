"""Stable HTTP response schemas owned by the API boundary."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

_DECIMAL_STRING_PATTERN = r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$"
DecimalString = Annotated[
    str,
    StringConstraints(strict=True, pattern=_DECIMAL_STRING_PATTERN),
]


class HealthResponse(BaseModel):
    """Status response for service discovery and lightweight integration checks."""

    status: Literal["ok"]
    service: str
    api_version: str


class MoneyResponse(BaseModel):
    """Currency-aware amount represented without floating-point ambiguity."""

    amount: str
    currency: str


class RfqSummaryResponse(BaseModel):
    """ERP-neutral read model for an open request for quotation."""

    source_id: str
    reference: str
    vendor_name: str
    order_date: datetime
    status: Literal["draft", "sent", "awaiting_approval", "unknown"]
    total: MoneyResponse


class RfqListResponse(BaseModel):
    """Bounded collection returned by the procurement API."""

    items: list[RfqSummaryResponse]
    count: int
    retrieved_at: datetime


class QuotationLineResponse(BaseModel):
    product_id: str
    product_name: str
    uom_id: str
    uom_name: str
    quantity: DecimalString
    unit_price: DecimalString


class QuotationResponse(BaseModel):
    offer_id: str
    reference: str
    supplier_id: str
    supplier_name: str
    state: str
    order_date: datetime
    lines: list[QuotationLineResponse]


class QuotationGroupResponse(BaseModel):
    """One Odoo quotation group the buyer may analyse (`selectable`) or not (`issue`)."""

    purchase_group_id: int
    name: str
    product_id: str | None
    product_name: str | None
    quantity: DecimalString | None
    uom_name: str | None
    currency: str | None
    supplier_count: int
    latest_order_date: datetime
    selectable: bool
    issue: str | None
    quotations: list[QuotationResponse]


class QuotationGroupListResponse(BaseModel):
    company_id: str
    items: list[QuotationGroupResponse]
    count: int
    truncated: bool
    retrieved_at: datetime
