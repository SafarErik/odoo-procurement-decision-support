"""ERP-neutral purchase-obligation history: confirmed lines and their receipts."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol

MAX_WINDOW = timedelta(days=366)
MAX_LINES = 500


def _utc(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be an explicit UTC timestamp.")


def _identity(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a canonical identity.")


@dataclass(frozen=True, slots=True)
class ReceiptEvent:
    event_id: str
    received_at: datetime
    quantity: Decimal
    backorder_of: str | None = None

    def __post_init__(self) -> None:
        _identity(self.event_id, "event_id")
        _utc(self.received_at, "received_at")
        if not isinstance(self.quantity, Decimal) or not self.quantity.is_finite():
            raise ValueError("Receipt quantity must be a finite decimal.")
        if self.quantity <= 0:
            raise ValueError("Receipt quantity must be positive.")


@dataclass(frozen=True, slots=True)
class PurchaseLineHistory:
    """One confirmed purchase obligation, as stored in the ERP at read time."""

    line_id: str
    order_id: str
    company_id: str
    supplier_id: str
    product_id: str
    uom_id: str
    ordered_quantity: Decimal
    expected_at: datetime
    confirmed_at: datetime
    receipts: tuple[ReceiptEvent, ...]
    returned_quantity: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        for label in ("line_id", "order_id", "company_id", "supplier_id", "product_id", "uom_id"):
            _identity(getattr(self, label), label)
        _utc(self.expected_at, "expected_at")
        _utc(self.confirmed_at, "confirmed_at")
        if not isinstance(self.ordered_quantity, Decimal) or not self.ordered_quantity > 0:
            raise ValueError("Ordered quantity must be a positive decimal.")
        if not isinstance(self.receipts, tuple) or any(
            not isinstance(r, ReceiptEvent) for r in self.receipts
        ):
            raise ValueError("Typed immutable receipts required.")
        if list(self.receipts) != sorted(self.receipts, key=lambda r: (r.received_at, r.event_id)):
            raise ValueError("Receipts must be chronological.")
        if not isinstance(self.returned_quantity, Decimal) or self.returned_quantity < 0:
            raise ValueError("Returned quantity must be a nonnegative decimal.")


@dataclass(frozen=True, slots=True)
class PurchaseHistoryQuery:
    """One company and product; lines whose Expected Arrival lies in [start, end)."""

    company_id: str
    product_id: str
    window_start: datetime
    window_end: datetime
    limit: int = MAX_LINES

    def __post_init__(self) -> None:
        _identity(self.company_id, "company_id")
        _identity(self.product_id, "product_id")
        _utc(self.window_start, "window_start")
        _utc(self.window_end, "window_end")
        if not timedelta(0) < self.window_end - self.window_start <= MAX_WINDOW:
            raise ValueError("History window must be positive and at most 366 days.")
        if type(self.limit) is not int or not 1 <= self.limit <= MAX_LINES:
            raise ValueError(f"History limit must be between 1 and {MAX_LINES}.")


@dataclass(frozen=True, slots=True)
class PurchaseHistorySnapshot:
    query: PurchaseHistoryQuery
    lines: tuple[PurchaseLineHistory, ...]
    observed_at: datetime
    source_type: str
    source_reference: str

    def __post_init__(self) -> None:
        _utc(self.observed_at, "observed_at")
        _identity(self.source_type, "source_type")
        _identity(self.source_reference, "source_reference")
        if self.observed_at < self.query.window_end:
            raise ValueError("A history snapshot cannot be observed before its window closes.")
        if len(self.lines) > self.query.limit or len({x.line_id for x in self.lines}) != len(
            self.lines
        ):
            raise ValueError("Bounded unique purchase lines required.")
        for line in self.lines:
            if (
                line.company_id != self.query.company_id
                or line.product_id != self.query.product_id
                or not self.query.window_start <= line.expected_at < self.query.window_end
            ):
                raise ValueError("History line outside the requested company/product/window.")


class PurchaseHistoryPort(Protocol):
    async def read_purchase_history(self, query: PurchaseHistoryQuery) -> PurchaseHistorySnapshot:
        """Read one bounded company/product purchase history window."""
