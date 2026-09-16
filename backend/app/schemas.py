"""Stable HTTP response schemas owned by the API boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
