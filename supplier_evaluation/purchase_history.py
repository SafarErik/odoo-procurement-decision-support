"""As-of supplier features, next-window labels and a leakage-safe dataset from purchase history.

Windows for one supplier/product context and cutoff ``c`` (see docs/MODEL_ML.md):

    features  lines with Expected Arrival in [c - 134d, c - 14d), confirmed before c,
              using only receipts processed before c
    gap       [c - 14d, c) is used for nothing (settlement time for recent lines)
    label     lines with Expected Arrival in [c, c + 60d): mean delay > 3 days or fill
              rate < 85%, judged 14 days after each Expected Arrival; observable from c + 74d
"""

import hashlib
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from application.purchase_history import PurchaseLineHistory
from supplier_evaluation.contracts import (
    HISTORY_FEATURE_VERSION,
    HISTORY_FEATURES,
    HISTORY_LOOKBACK,
    HISTORY_SETTLEMENT,
    HISTORY_SOURCE,
    Context,
    FeatureSnapshot,
    digest,
    utc,
)

GRACE = timedelta(days=1)
HORIZON = timedelta(days=60)
MIN_FEATURE_LINES = 3
MIN_LABEL_LINES = 2
LATE_DAYS_LIMIT = 3.0
FILL_RATE_LIMIT = 0.85
# Recency looks at receipts of lines due in the last 180 days (same window offline and live).
RECENCY_WINDOW = timedelta(days=180)
DAY = 86400.0


def _days(delta: timedelta) -> float:
    return delta.total_seconds() / DAY


def context_lines(lines, context: Context) -> tuple[PurchaseLineHistory, ...]:
    """Lines of exactly one company/supplier/product/unit context."""
    return tuple(
        line
        for line in lines
        if (line.company_id, line.supplier_id, line.product_id, line.uom_id)
        == (context.company_id, context.supplier_id, context.product_id, context.quantity_unit)
    )


def feature_values(lines, cutoff: datetime) -> tuple[float, ...] | None:
    """Seven as-of features, or None when fewer than three settled lines exist."""
    utc(cutoff)
    start, end = cutoff - HISTORY_SETTLEMENT - HISTORY_LOOKBACK, cutoff - HISTORY_SETTLEMENT
    window = [
        line for line in lines if start <= line.expected_at < end and line.confirmed_at < cutoff
    ]
    if len(window) < MIN_FEATURE_LINES:
        return None
    on_time, lateness, partial = [], [], []
    received_total, ordered_total = Decimal(0), Decimal(0)
    for line in window:
        known = [r for r in line.receipts if r.received_at < cutoff]
        first = known[0].received_at if known else None
        received = sum((r.quantity for r in known), Decimal(0))
        on_time.append(first is not None and first <= line.expected_at + GRACE)
        lateness.append(_days((first or cutoff) - line.expected_at))
        partial.append(len(known) > 1 or received < line.ordered_quantity)
        received_total += min(received, line.ordered_quantity)
        ordered_total += line.ordered_quantity
    cap = _days(RECENCY_WINDOW)
    seen = [
        r.received_at
        for line in lines
        if cutoff - RECENCY_WINDOW <= line.expected_at < cutoff and line.confirmed_at < cutoff
        for r in line.receipts
        if r.received_at < cutoff
    ]
    recency = min(cap, _days(cutoff - max(seen))) if seen else cap
    values = (
        sum(on_time) / len(window),
        statistics.fmean(lateness),
        statistics.pstdev(lateness),
        float(received_total / ordered_total),
        sum(partial) / len(window),
        float(len(window)),
        recency,
    )
    return tuple(round(v, 6) for v in values)


def feature_snapshot(
    lines, context: Context, cutoff: datetime, observed_at: datetime, source_reference: str
) -> FeatureSnapshot | None:
    values = feature_values(context_lines(lines, context), cutoff)
    if values is None:
        return None
    end = cutoff - HISTORY_SETTLEMENT
    return FeatureSnapshot(
        context,
        cutoff,
        end - HISTORY_LOOKBACK,
        end,
        min(observed_at, cutoff),
        values,
        HISTORY_SOURCE,
        source_reference,
        HISTORY_FEATURE_VERSION,
        HISTORY_FEATURES,
    )


def problematic_label(lines, cutoff: datetime) -> tuple[int, datetime] | None:
    """1 when the next 60 days are problematic for this supplier/product.

    Problematic: the average delay of the lines due in [cutoff, cutoff + 60d) exceeds
    3 days, or their fill rate is below 85%. A line's delay is first receipt minus
    Expected Arrival in days, early counts as 0, nothing within 14 days counts as 14.
    Fill counts what arrived within 14 days of Expected Arrival. At least two due
    lines are required. (An earlier share-of-late-lines label was dominated by single
    lines; see docs/MODEL_ML.md.)
    """
    utc(cutoff)
    due = [line for line in lines if cutoff <= line.expected_at < cutoff + HORIZON]
    if len(due) < MIN_LABEL_LINES:
        return None
    cap = _days(HISTORY_SETTLEMENT)
    delays, received_total, ordered_total = [], Decimal(0), Decimal(0)
    for line in due:
        first = line.receipts[0].received_at if line.receipts else None
        delay = cap if first is None else _days(first - line.expected_at)
        delays.append(min(cap, max(0.0, delay)))
        settled = [
            r for r in line.receipts if r.received_at <= line.expected_at + HISTORY_SETTLEMENT
        ]
        received = sum((r.quantity for r in settled), Decimal(0))
        received_total += min(received, line.ordered_quantity)
        ordered_total += line.ordered_quantity
    label = statistics.fmean(delays) > LATE_DAYS_LIMIT or received_total / ordered_total < Decimal(
        str(FILL_RATE_LIMIT)
    )
    return int(label), cutoff + HORIZON + HISTORY_SETTLEMENT


@dataclass(frozen=True, slots=True)
class Row:
    row_id: str
    context: Context
    cutoff: datetime
    values: tuple[float, ...]
    label: int
    label_available_at: datetime


def semi_monthly_cutoffs(start: datetime, end: datetime) -> tuple[datetime, ...]:
    """1st and 16th of each month at 00:00 UTC in [start, end]."""
    out, year, month = [], start.year, start.month
    while True:
        for day in (1, 16):
            value = start.replace(year=year, month=month, day=day, hour=0, minute=0, second=0)
            if value > end:
                return tuple(out)
            if value >= start:
                out.append(value)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def build_rows(lines, *, extracted_at: datetime) -> tuple[tuple[Row, ...], dict]:
    """Every context/cutoff whose features and label are both supported."""
    utc(extracted_at)
    if not lines:
        raise ValueError("No purchase history lines.")
    contexts = sorted(
        {Context(x.supplier_id, x.company_id, x.product_id, x.uom_id) for x in lines},
        key=lambda c: (c.supplier_id, c.product_id),
    )
    if len({c.company_id for c in contexts}) != 1:
        raise ValueError("A dataset covers exactly one company.")
    first = min(x.expected_at for x in lines) + HISTORY_LOOKBACK + HISTORY_SETTLEMENT
    last = extracted_at - HORIZON - HISTORY_SETTLEMENT
    cutoffs = semi_monthly_cutoffs(first, last)
    rows, skipped = [], Counter()
    for context in contexts:
        own = context_lines(lines, context)
        for cutoff in cutoffs:
            values = feature_values(own, cutoff)
            label = problematic_label(own, cutoff)
            if values is None or label is None:
                skipped["insufficient_features" if values is None else "insufficient_label"] += 1
                continue
            rows.append(
                Row(
                    f"{context.supplier_id}|{context.product_id}|{cutoff.date().isoformat()}",
                    context,
                    cutoff,
                    values,
                    *label,
                )
            )
    coverage = {
        "contexts": len(contexts),
        "cutoffs": [c.isoformat() for c in cutoffs],
        "rows": len(rows),
        "skipped": dict(skipped),
    }
    return tuple(rows), coverage


@dataclass(frozen=True, slots=True)
class HistorySplit:
    train: tuple[Row, ...]
    test: tuple[Row, ...]
    temporal_test: tuple[Row, ...]
    boundary: datetime
    test_suppliers: tuple[str, ...]


def test_suppliers(rows, share: float, seed: int) -> tuple[str, ...]:
    """Deterministic supplier groups held out entirely (hash order, no outcome look)."""
    suppliers = sorted({r.context.supplier_id for r in rows})
    order = sorted(suppliers, key=lambda s: hashlib.sha256(f"{seed}:{s}".encode()).hexdigest())
    return tuple(sorted(order[: max(1, round(len(suppliers) * share))]))


def split_rows(rows, *, boundary: datetime, share: float = 0.25, seed: int = 17) -> HistorySplit:
    """Train: other suppliers, labels observable before the boundary.

    Test: held-out suppliers, cutoffs at/after the boundary (primary).
    Temporal test: all suppliers, cutoffs at/after the boundary (supplementary).
    """
    utc(boundary)
    held = test_suppliers(rows, share, seed)
    train = tuple(
        r for r in rows if r.context.supplier_id not in held and r.label_available_at <= boundary
    )
    test = tuple(r for r in rows if r.context.supplier_id in held and r.cutoff >= boundary)
    temporal = tuple(r for r in rows if r.cutoff >= boundary)
    if not train or not test:
        raise ValueError("Nonempty train and held-out partitions required.")
    if {r.context.supplier_id for r in train} & {r.context.supplier_id for r in test}:
        raise ValueError("Supplier group leakage across train/test.")
    if max(r.label_available_at for r in train) > min(r.cutoff for r in test + temporal):
        raise ValueError("Temporal label-window leakage across split.")
    return HistorySplit(train, test, temporal, boundary, held)


def rows_id(rows) -> str:
    return digest([[r.row_id, list(r.values), r.label, r.label_available_at] for r in rows])
