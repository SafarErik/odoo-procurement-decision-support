"""Immutable capture of bounded Odoo purchase history and its as-of supplier features.

The capture stores the raw exported lines, so a stored case can re-derive and check
its feature values without Odoo, a model file, or any new read.
"""

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from application.errors import (
    PlanningCaseError,
    ProcurementDataResponseError,
    ProcurementDataUnavailable,
)
from application.odoo_quotations import ComparisonCaseReader
from application.planning_serialization import json_value
from application.purchase_history import (
    PurchaseHistoryPort,
    PurchaseHistoryQuery,
    PurchaseHistorySnapshot,
    PurchaseLineHistory,
    ReceiptEvent,
)
from supplier_evaluation.contracts import (
    HISTORY_DATA_ORIGINS,
    HISTORY_LOOKBACK,
    HISTORY_SETTLEMENT,
    HISTORY_SOURCE,
    Context,
    FeatureSnapshot,
    canonical,
    digest,
)
from supplier_evaluation.purchase_history import RECENCY_WINDOW, feature_snapshot

CAPTURE_VERSION = "odoo-purchase-history-capture-v2"
CAPTURE_WINDOW = RECENCY_WINDOW  # covers the feature window and the recency window
MAX_READ_TO_CUTOFF = timedelta(days=1)


class HistoryCaptureError(ValueError):
    """The captured history cannot support an assessment for every supplier."""


def history_query(company_id: str, product_id: str, read_end: datetime) -> PurchaseHistoryQuery:
    return PurchaseHistoryQuery(company_id, product_id, read_end - CAPTURE_WINDOW, read_end)


def build_capture(
    snapshot: PurchaseHistorySnapshot,
    contexts: tuple[Context, ...],
    database: str,
    data_origin: str,
) -> str:
    """Freeze raw lines, the cutoff and one feature snapshot per quoted supplier.

    ``data_origin`` is the operator's declaration of what the database holds
    (generated or observed history); it is frozen with the evidence.
    """
    if data_origin not in HISTORY_DATA_ORIGINS:
        raise ValueError(f"Unsupported history data origin: {data_origin!r}.")
    cutoff = snapshot.observed_at
    evidence = {
        "version": CAPTURE_VERSION,
        "database": database,
        "data_origin": data_origin,
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


def capture_origin(encoded: str) -> str:
    """Declared origin of a stored capture."""
    origin = json.loads(encoded)["evidence"]["data_origin"]
    if origin not in HISTORY_DATA_ORIGINS:
        raise ValueError("Unsupported history capture data origin.")
    return origin


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
    capture_origin(encoded)
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


async def capture_odoo_history(
    quotations: ComparisonCaseReader,
    history: PurchaseHistoryPort,
    group_id: int,
    *,
    database: str,
    data_origin: str,
):
    """Read one quotation group and its product's bounded history; never called on replay.

    Returns ``(case, currency_code, currency_observed_at, capture)``. Raises
    PlanningCaseError ``odoo_history_unavailable`` when Odoo cannot be read and
    ``odoo_history_insufficient`` when a supplier has too little history.
    """
    try:
        case = await quotations.read_comparison_case(group_id)
        if not case.offers or any(len(o.lines) != 1 for o in case.offers):
            raise ValueError("A one-line quotation group is required.")
        code, observed = await quotations.read_currency_code(case.offers[0].currency_id)
        line, company = case.offers[0].lines[0], case.offers[0].company_id
        # Odoo rejects an export end in its future; a lagging container clock (e.g. after the
        # host slept) must not turn every read into "unavailable", hence the small margin.
        read_end = datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=60)
        query = history_query(company, line.product_id, read_end)
        snapshot = await history.read_purchase_history(query)
        contexts = tuple(
            Context(o.supplier_id, company, line.product_id, line.uom_id) for o in case.offers
        )
        return case, code, observed, build_capture(snapshot, contexts, database, data_origin)
    except HistoryCaptureError as error:
        raise PlanningCaseError("odoo_history_insufficient", str(error)) from error
    except (ProcurementDataUnavailable, ProcurementDataResponseError) as error:
        raise PlanningCaseError(
            "odoo_history_unavailable", "The Odoo quotation group or its history is unavailable."
        ) from error


def odoo_history_preview(group_id: int, captured, *, database: str, model_company: str | None):
    """Read-only preview of a captured group with suggested buyer terms; nothing is stored.

    The terms are suggestions the buyer reviews and may edit before saving: a 7-day
    deadline, capacity 60 % of the demand per supplier, quantity ranges 1-1000 and a
    two-supplier policy. ``model_company`` is the company the loaded history model was
    trained for, or None when no compatible model loads; any other value reports
    ``model_unavailable``.
    """
    case, code, _, capture = captured
    features = capture_features(capture)
    company = case.offers[0].company_id
    readiness = "ready" if model_company == company else "model_unavailable"
    now = datetime.now(UTC)
    line = case.offers[0].lines[0]
    demand = int(line.quantity)
    deadline = (now + timedelta(days=7)).date().isoformat()
    source = {
        "source_type": "buyer_default_terms",
        "source_reference": "odoo-history-preview-defaults-v2",
        "observed_at": now.isoformat(),
    }
    suppliers = [
        {
            "supplier_id": offer.supplier_id,
            "offer_id": offer.offer_id,
            "unit_price": str(offer.lines[0].unit_price),
            "capacity": max(1, -(-demand * 6 // 10)),
            "available": True,
            "minimum_order_quantity": None,
            "price_quantities": {"minimum": 1, "maximum": 1000},
            "delivery_quantities": {"minimum": 1, "maximum": 1000},
            "promised_date": deadline,
            "source": source,
        }
        for offer in sorted(case.offers, key=lambda o: o.supplier_id)
    ]
    terms = {
        "company_id": company,
        "as_of": now.isoformat(),
        "approval_reference": f"odoo-history-demand-{demand}-v2",
        "requirement": {
            "product_id": line.product_id,
            "approved_quantity": demand,
            "quantity_unit": line.uom_id,
            "currency": code,
            "required_date": deadline,
        },
        "requirement_source": source,
        "policy_source": source,
        "policy": {
            "max_suppliers": 2,
            "concentration_limit": "0.8",
            "epsilons": ["0.05", "0.1", "0.2"],
            "diversification_epsilon": "0.2",
        },
        "suppliers": suppliers,
    }
    parsed = json.loads(capture)
    return {
        "purchase_group_id": group_id,
        "database": database,
        "data_origin": capture_origin(capture),
        "model_readiness": readiness,
        "captured_at": parsed["evidence"]["cutoff"],
        "capture_hash": parsed["capture_hash"],
        "features": json_value(features),
        "history": [
            {"supplier_id": f.context.supplier_id}
            | dict(zip(f.feature_names, f.values, strict=True))
            for f in features
        ],
        "terms": terms,
    }
