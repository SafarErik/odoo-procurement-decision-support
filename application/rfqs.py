"""Application contract for listing open requests for quotation."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

RfqStatus = Literal["draft", "sent", "awaiting_approval", "unknown"]


class ProcurementDataUnavailable(RuntimeError):
    """The procurement source is not configured or cannot be reached."""


class ProcurementDataResponseError(RuntimeError):
    """The procurement source rejected a request or returned invalid data."""


@dataclass(frozen=True, slots=True)
class Money:
    """Currency-aware amount without binary floating-point loss."""

    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class RfqSummary:
    """ERP-neutral summary used by the application and API boundary."""

    source_id: str
    reference: str
    vendor_name: str
    order_date: datetime
    status: RfqStatus
    total: Money


class RfqReader(Protocol):
    """Port implemented by an external procurement-data adapter."""

    async def list_open_rfqs(self, limit: int) -> list[RfqSummary]:
        """Return the newest open RFQs, bounded by ``limit``."""


async def list_open_rfqs(reader: RfqReader, limit: int) -> list[RfqSummary]:
    """Execute the bounded, read-only RFQ listing use case."""

    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    return await reader.list_open_rfqs(limit)
