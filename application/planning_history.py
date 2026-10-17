"""Immutable source-attributed history capture and stored-contract validation."""

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from application.historical_performance import (
    SourcedSupplierHistoricalPerformance,
    calculate_delivery_schedule_adherence,
)
from supplier_evaluation.contracts import ODOO_HISTORY, Context, FeatureSnapshot, canonical, digest
from supplier_evaluation.history import from_sourced_history

HISTORY_INPUT_KIND = "odoo_quotations_odoo_history"
CAPTURE_VERSION = "bounded-odoo-history-capture-v1"


def build_capture(profile, snapshots, identity_evidence):
    cutoff = datetime.now(UTC)
    evidence = {
        "version": CAPTURE_VERSION,
        "profile": profile,
        "profile_revision": digest(profile),
        "database": profile["database"],
        "origin": profile["origin"],
        "cutoff": cutoff,
        "identity_evidence": identity_evidence,
        "snapshots": [asdict(s) for s in snapshots],
    }
    _validate_raw_history(json.loads(canonical(evidence)))
    capture_hash = digest(evidence)
    features, performance = [], []
    for snapshot in snapshots:
        p = calculate_delivery_schedule_adherence(snapshot)
        if p.warnings:
            raise ValueError("History has exclusions or warnings; no score fallback.")
        reference = (
            snapshot.source_reference
            + f"|database={profile['database']}"
            + f"|origin={profile['origin']}|profile={profile['id']}|capture={capture_hash}"
        )
        sourced = SourcedSupplierHistoricalPerformance(p, ODOO_HISTORY, reference)
        feature = from_sourced_history(
            sourced,
            Context(
                snapshot.query.supplier_id,
                snapshot.query.company_id,
                f"odoo:product.product:{profile['product_id']}",
                f"odoo:uom.uom:{profile['unit_id']}",
            ),
            cutoff,
        )
        features.append(asdict(feature))
        performance.append(asdict(p))
    payload = {
        "evidence": evidence,
        "capture_hash": capture_hash,
        "features": features,
        "performance": performance,
    }
    payload["payload_hash"] = digest(payload)
    encoded = canonical(payload)
    capture_features(encoded)
    return encoded


def capture_features(encoded: str):
    """Validate stored evidence without Odoo, inference, KPI recalculation or a model file."""
    payload = json.loads(encoded)
    if set(payload) != {"evidence", "capture_hash", "features", "performance", "payload_hash"}:
        raise ValueError("Unsupported history capture envelope.")
    if payload["payload_hash"] != digest({k: v for k, v in payload.items() if k != "payload_hash"}):
        raise ValueError("History capture provenance/payload integrity mismatch.")
    evidence, capture_hash = payload["evidence"], payload["capture_hash"]
    if digest(evidence) != capture_hash:
        raise ValueError("History capture evidence integrity mismatch.")
    domain, by_supplier, suppliers = _validate_raw_history(evidence)
    profile = evidence["profile"]
    features = []
    results = {p["supplier_id"]: p for p in payload["performance"]}
    for raw in payload["features"]:
        item = dict(raw)
        item["context"] = Context(**item["context"])
        for field in ("cutoff", "history_start", "history_end", "evidence_available_at"):
            item[field] = datetime.fromisoformat(item[field])
        item["feature_names"], item["values"] = tuple(item["feature_names"]), tuple(item["values"])
        feature = FeatureSnapshot(**item)
        p = results[feature.context.supplier_id]
        suffix = (
            f"|database={profile['database']}|origin={profile['origin']}"
            f"|profile={profile['id']}|capture={capture_hash}"
        )
        snapshot = by_supplier[feature.context.supplier_id]
        if (
            feature.source_type != ODOO_HISTORY
            or feature.context.domain != domain
            or not feature.source_reference.endswith(suffix)
            or feature.cutoff != datetime.fromisoformat(evidence["cutoff"])
            or feature.values != (float(p["value"]), float(p["sample_size"]))
            or p["availability"] != "usable"
            or p["warnings"]
            or feature.history_end
            != datetime.fromisoformat(snapshot["query"]["observation_window_end"])
            or feature.evidence_available_at != datetime.fromisoformat(snapshot["observed_at"])
        ):
            raise ValueError("Captured feature provenance/value mismatch.")
        features.append(feature)
    if len(features) != 3 or {f.context.supplier_id for f in features} != suppliers:
        raise ValueError("Incomplete supplier features.")
    return tuple(features)


def _validate_raw_history(evidence):
    """Check exact raw receipt context/backorders before any KPI aggregation."""
    profile = evidence["profile"]
    if (
        evidence["version"] != CAPTURE_VERSION
        or digest(profile) != evidence["profile_revision"]
        or evidence["database"] != profile["database"]
        or evidence["origin"] != "controlled_synthetic"
        or profile["origin"] != evidence["origin"]
        or profile["id"] != "local-v1"
        or profile["database"] != "procurement_v2_history_test_v1"
    ):
        raise ValueError("History capture provenance mismatch.")
    domain = (
        f"odoo:res.company:{profile['company_id']}",
        f"odoo:product.product:{profile['product_id']}",
        f"odoo:uom.uom:{profile['unit_id']}",
    )
    expected = {f"odoo:purchase.order.line:{r['line']}": r for r in profile["records"]}
    if len(expected) != 9 or len({r["order"] for r in expected.values()}) != 9:
        raise ValueError("Duplicate or incomplete history membership.")
    events, seen_lines, suppliers, ends = set(), set(), set(), set()
    by_supplier = {}
    for snapshot in evidence["snapshots"]:
        query = snapshot["query"]
        by_supplier[query["supplier_id"]] = snapshot
        if query["company_id"] != domain[0]:
            raise ValueError("History query company mismatch.")
        suppliers.add(query["supplier_id"])
        start, end = (
            datetime.fromisoformat(query[k])
            for k in ("observation_window_start", "observation_window_end")
        )
        observed, cutoff = (
            datetime.fromisoformat(snapshot["observed_at"]),
            datetime.fromisoformat(evidence["cutoff"]),
        )
        if (
            end - start != timedelta(days=365)
            or not end <= observed <= cutoff
            or cutoff - end > timedelta(days=7)
        ):
            raise ValueError("History temporal validity mismatch.")
        ends.add(end)
        wanted_lines = {
            key
            for key, r in expected.items()
            if query["supplier_id"] == f"odoo:res.partner:{r['supplier']}"
        }
        if (
            set(query["purchase_line_ids"]) != wanted_lines
            or snapshot["source_type"] != ODOO_HISTORY
        ):
            raise ValueError("Supplier history membership mismatch.")
        for item in snapshot["observations"]:
            line = expected.get(item["purchase_line_id"])
            if (
                line is None
                or (item["company_id"], item["product_id"], item["uom_id"]) != domain
                or item["supplier_id"] != query["supplier_id"]
            ):
                raise ValueError("Unexpected receipt context.")
            known = {
                (
                    f"odoo:stock.move:{e[0]}",
                    f"odoo:stock.picking:{e[1]}",
                    Decimal(e[2]),
                    None if e[3] is None else f"odoo:stock.picking:{e[3]}",
                )
                for e in line["events"]
            }
            event = (
                item["receipt_event_id"],
                item["transfer_id"],
                Decimal(item["completed_quantity"]),
                item["backorder_of_transfer_id"],
            )
            completed = datetime.fromisoformat(item["completed_at"])
            if (
                event not in known
                or event[0] in events
                or not start <= completed < end
                or item["state"] != "completed"
                or item["direction"] != "supplier_to_internal"
                or item["return_of_event_id"] is not None
                or item["return_of_transfer_id"] is not None
                or item["purchase_document_id"] != f"odoo:purchase.order:{line['order']}"
                or datetime.fromisoformat(item["scheduled_arrival_at"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                != line["deadline"]
            ):
                raise ValueError("Unexpected receipt, schedule or backorder evidence.")
            events.add(event[0])
            seen_lines.add(item["purchase_line_id"])
    if len(events) != 10 or seen_lines != set(expected) or len(suppliers) != 3 or len(ends) != 1:
        raise ValueError("Incomplete captured history.")
    return domain, by_supplier, suppliers
