"""Immutable capture of bounded Odoo purchase history and its as-of supplier features.

The capture stores the raw exported lines, so a stored case can re-derive and check
its feature values without Odoo, a model file, or any new read.
"""

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal

from application.purchase_history import (
    PurchaseHistoryQuery,
    PurchaseHistorySnapshot,
    PurchaseLineHistory,
    ReceiptEvent,
)
from supplier_evaluation.contracts import (
    HISTORY_LOOKBACK,
    HISTORY_SETTLEMENT,
    HISTORY_SOURCE,
    Context,
    FeatureSnapshot,
    canonical,
    digest,
)
from supplier_evaluation.purchase_history import RECENCY_WINDOW, feature_snapshot

HISTORY_INPUT_KIND = "odoo_quotations_odoo_history"
CAPTURE_VERSION = "odoo-purchase-history-capture-v2"
CAPTURE_WINDOW = RECENCY_WINDOW  # covers the feature window and the recency window
MAX_READ_TO_CUTOFF = timedelta(days=1)


class HistoryCaptureError(ValueError):
    """The captured history cannot support an assessment for every supplier."""


def history_query(company_id: str, product_id: str, read_end: datetime) -> PurchaseHistoryQuery:
    return PurchaseHistoryQuery(company_id, product_id, read_end - CAPTURE_WINDOW, read_end)


def build_capture(
    snapshot: PurchaseHistorySnapshot, contexts: tuple[Context, ...], database: str
) -> str:
    """Freeze raw lines, the cutoff and one feature snapshot per quoted supplier."""
    cutoff = snapshot.observed_at
    evidence = {
        "version": CAPTURE_VERSION,
        "database": database,
        "cutoff": cutoff,
        "contexts": [asdict(c) for c in sorted(contexts, key=lambda c: c.supplier_id)],
        "snapshot": asdict(snapshot),
    }
    capture_hash = digest(evidence)
    features = []
    for context in sorted(contexts, key=lambda c: c.supplier_id):
        feature = feature_snapshot(
            snapshot.lines,
            context,
            cutoff,
            snapshot.observed_at,
            f"{snapshot.source_reference}|capture={capture_hash}",
        )
        if feature is None:
            raise HistoryCaptureError(
                f"Supplier {context.supplier_id} has fewer than three settled purchase lines "
                "in the feature window; no score fallback."
            )
        features.append(asdict(feature))
    payload = {"evidence": evidence, "capture_hash": capture_hash, "features": features}
    payload["payload_hash"] = digest(payload)
    encoded = canonical(payload)
    capture_features(encoded)
    return encoded


def _snapshot(raw: dict) -> PurchaseHistorySnapshot:
    query = raw["query"]
    lines = []
    for line in raw["lines"]:
        item = dict(line)
        item["receipts"] = tuple(
            ReceiptEvent(
                r["event_id"],
                datetime.fromisoformat(r["received_at"]),
                Decimal(r["quantity"]),
                r["backorder_of"],
            )
            for r in item["receipts"]
        )
        for key in ("expected_at", "confirmed_at"):
            item[key] = datetime.fromisoformat(item[key])
        for key in ("ordered_quantity", "returned_quantity"):
            item[key] = Decimal(item[key])
        lines.append(PurchaseLineHistory(**item))
    return PurchaseHistorySnapshot(
        PurchaseHistoryQuery(
            query["company_id"],
            query["product_id"],
            datetime.fromisoformat(query["window_start"]),
            datetime.fromisoformat(query["window_end"]),
            query["limit"],
        ),
        tuple(lines),
        datetime.fromisoformat(raw["observed_at"]),
        raw["source_type"],
        raw["source_reference"],
    )


def capture_features(encoded: str) -> tuple[FeatureSnapshot, ...]:
    """Validate a stored capture and re-derive its features from the raw lines only."""
    payload = json.loads(encoded)
    if set(payload) != {"evidence", "capture_hash", "features", "payload_hash"}:
        raise ValueError("Unsupported history capture envelope.")
    if payload["payload_hash"] != digest({k: v for k, v in payload.items() if k != "payload_hash"}):
        raise ValueError("History capture payload integrity mismatch.")
    evidence = payload["evidence"]
    if digest(evidence) != payload["capture_hash"] or evidence["version"] != CAPTURE_VERSION:
        raise ValueError("History capture evidence integrity mismatch.")
    snapshot = _snapshot(evidence["snapshot"])
    cutoff = datetime.fromisoformat(evidence["cutoff"])
    window = snapshot.query
    if (
        snapshot.source_type != HISTORY_SOURCE
        or f"|database={evidence['database']}|" not in snapshot.source_reference
        or cutoff != snapshot.observed_at
        or not timedelta(0) <= cutoff - window.window_end <= MAX_READ_TO_CUTOFF
        or window.window_start > cutoff - max(RECENCY_WINDOW, HISTORY_SETTLEMENT + HISTORY_LOOKBACK)
    ):
        raise ValueError("History capture source or temporal validity mismatch.")
    contexts = tuple(Context(**c) for c in evidence["contexts"])
    if (
        not contexts
        or len({c.supplier_id for c in contexts}) != len(contexts)
        or any(
            (c.company_id, c.product_id) != (window.company_id, window.product_id) for c in contexts
        )
    ):
        raise ValueError("History capture context mismatch.")
    reference = f"{snapshot.source_reference}|capture={payload['capture_hash']}"
    features = []
    for context, stored in zip(contexts, payload["features"], strict=True):
        feature = feature_snapshot(snapshot.lines, context, cutoff, snapshot.observed_at, reference)
        if feature is None or canonical(asdict(feature)) != canonical(stored):
            raise ValueError("Captured feature provenance/value mismatch.")
        features.append(feature)
    return tuple(features)
