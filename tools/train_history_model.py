"""Offline supplier-model training from the bounded Odoo purchase-history export.

    python -m tools.train_history_model extract [--products 1,2,3] [--company 1]
    python -m tools.train_history_model train
    python -m tools.train_history_model all
    python -m tools.train_history_model report   re-evaluate the saved model, no training

``extract`` reads Odoo through the restricted history user (ODOO_T7S_API_KEY) and
writes the raw export; ``train`` never touches Odoo. Output: .artifacts/ml/.
The backend only loads the resulting model (SUPPLIER_HISTORY_MODEL_DIRECTORY).
"""

import argparse
import asyncio
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from application.purchase_history import PurchaseHistoryQuery, PurchaseLineHistory, ReceiptEvent
from odoo_adapter.product_history_reader import OdooProductHistoryReader
from supplier_evaluation.contracts import HISTORY_FEATURES, canonical, digest
from supplier_evaluation.history_model import evaluate, load_model, save_model, train
from supplier_evaluation.purchase_history import (
    GRACE,
    HORIZON,
    build_rows,
    rows_id,
    semi_monthly_cutoffs,
    split_rows,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts" / "ml"
HISTORY_DAYS = 548
WINDOW = timedelta(days=180)  # stays below the export's 500-line bound per product
BOUNDARY_BEFORE_LAST_CUTOFF = timedelta(days=92)


def _settings() -> dict[str, str]:
    values = {}
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.lstrip().startswith("#"):
                values[key.strip()] = value.strip()
    return values


def _default_products() -> list[int]:
    manifest = ROOT / ".artifacts" / "seed" / "manifest.json"
    if not manifest.exists():
        raise SystemExit("Pass --products (Odoo product.product ids).")
    return sorted(json.loads(manifest.read_text(encoding="utf-8"))["manifest"]["products"].values())


async def extract(products: list[int], company: int) -> dict:
    settings = _settings()
    database = settings.get("ODOO_DATABASE", "")
    reader = OdooProductHistoryReader(
        base_url=settings.get("ODOO_BASE_URL", "http://127.0.0.1:8069"),
        database=database,
        api_key=settings.get("ODOO_T7S_API_KEY", ""),
    )
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=HISTORY_DAYS)
    snapshots = []
    for product in products:
        window_start = start
        while window_start < end:
            window_end = min(end, window_start + WINDOW)
            query = PurchaseHistoryQuery(
                f"odoo:res.company:{company}",
                f"odoo:product.product:{product}",
                window_start,
                window_end,
            )
            snapshots.append(await reader.read_purchase_history(query))
            window_start = window_end
    lines = [line for s in snapshots for line in s.lines]
    if len({line.line_id for line in lines}) != len(lines):
        raise ValueError("Overlapping export windows returned a line twice.")
    return {
        "database": database,
        "company_id": f"odoo:res.company:{company}",
        "products": [f"odoo:product.product:{p}" for p in products],
        "window": [start.isoformat(), end.isoformat()],
        "extracted_at": max(s.observed_at for s in snapshots).isoformat(),
        "data_origin": "generated",
        "source_references": [s.source_reference for s in snapshots],
        "lines": [asdict(line) for line in lines],
    }


def load_lines(export: dict) -> tuple[PurchaseLineHistory, ...]:
    def line(raw):
        raw = dict(raw)
        raw["receipts"] = tuple(
            ReceiptEvent(
                r["event_id"],
                datetime.fromisoformat(r["received_at"]),
                Decimal(r["quantity"]),
                r["backorder_of"],
            )
            for r in raw["receipts"]
        )
        for key in ("expected_at", "confirmed_at"):
            raw[key] = datetime.fromisoformat(raw[key])
        for key in ("ordered_quantity", "returned_quantity"):
            raw[key] = Decimal(raw[key])
        return PurchaseLineHistory(**raw)

    return tuple(line(raw) for raw in export["lines"])


def _split(export: dict):
    lines = load_lines(export)
    extracted_at = datetime.fromisoformat(export["extracted_at"])
    rows, coverage = build_rows(lines, extracted_at=extracted_at)
    last = max(r.cutoff for r in rows)
    candidates = semi_monthly_cutoffs(
        min(r.cutoff for r in rows), last - BOUNDARY_BEFORE_LAST_CUTOFF
    )
    return lines, rows, coverage, split_rows(rows, boundary=max(candidates))


def report_check(export: dict, model_directory: Path, reference: dict) -> dict:
    """Evaluate the saved model on the stored export again; compare with the reference."""
    _, _, _, split = _split(export)
    model, manifest = load_model(model_directory, trusted_local=True)
    evaluation = evaluate(model, split)
    same = {
        "artifact_sha256": manifest["artifact_sha256"] == reference["artifact_sha256"],
        "export_hash": digest(export["lines"]) == reference["dataset_card"]["export_hash"],
        "train_id": rows_id(split.train) == reference["dataset_card"]["split"]["train_id"],
        "evaluation": canonical(evaluation) == canonical(reference["evaluation"]),
    }
    primary = evaluation["primary_supplier_and_time_holdout"]
    return {
        "report": "P4 ML evaluation check: saved model re-evaluated, not retrained",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_id": model.metadata["model_id"],
        "artifact_sha256": manifest["artifact_sha256"],
        "export_hash": digest(export["lines"]),
        "identical_to_reference": same,
        "unchanged": all(same.values()),
        "primary_macro_f1": {
            "decision_tree": primary["decision_tree"]["macro"]["f1"],
            **{k: v["macro"]["f1"] for k, v in primary["baselines"].items()},
        },
        "evaluation": evaluation,
    }


def train_from_export(export: dict) -> dict:
    lines, rows, coverage, split = _split(export)
    model = train(split, database=export["database"])
    manifest = save_model(model, OUT / "model")
    report = {
        "dataset_card": dataset_card(export, lines, rows, coverage, split),
        "model": model.metadata,
        "artifact_sha256": manifest["artifact_sha256"],
        "evaluation": evaluate(model, split),
        "tree": model.global_explanation(),
        "limitations": [
            "All purchase history in the test database is generated by tools/seed_odoo_history.py;"
            " the pipeline is Odoo-native, the data is not observed.",
            "Generated timestamps follow a simulated clock (back-dated records).",
            "Expected Arrival is read as stored at extraction time, not as originally promised.",
            "Scores are leaf frequencies, not calibrated probabilities.",
            "Small held-out set: few suppliers; overlapping semi-monthly windows"
            " make rows correlated.",
        ],
    }
    (OUT / "report.json").write_text(canonical(report) + "\n", encoding="utf-8")
    rows_payload = [
        {"row_id": r.row_id, "supplier_id": r.context.supplier_id,
         "product_id": r.context.product_id, "cutoff": r.cutoff,
         "values": list(r.values), "label": r.label,
         "label_available_at": r.label_available_at,
         "partition": "train" if r in split.train else ("test" if r in split.test else "unused")}
        for r in rows
    ]  # fmt: skip
    (OUT / "dataset.json").write_text(canonical({"rows": rows_payload}) + "\n", encoding="utf-8")
    return report


def dataset_card(export, lines, rows, coverage, split) -> dict:
    return {
        "name": "Odoo purchase-history supplier dataset",
        "dataset_version": "odoo-purchase-history-dataset-v2",
        "source": "procurement.product.history.export.read_product_history (JSON-2, read-only)",
        "database": export["database"],
        "data_origin": "generated (tools/seed_odoo_history.py, simulated clock)",
        "extracted_at": export["extracted_at"],
        "export_window": export["window"],
        "export_hash": digest(export["lines"]),
        "purchase_lines": len(lines),
        "receipts": sum(len(x.receipts) for x in lines),
        "suppliers": len({x.supplier_id for x in lines}),
        "products": len({x.product_id for x in lines}),
        "unit_of_observation": "supplier x product x semi-monthly cutoff",
        "features": list(HISTORY_FEATURES),
        "feature_window": "Expected Arrival in [cutoff-134d, cutoff-14d);"
        " confirmed and received before cutoff",
        "label": "problematic = mean delay > 3 days or fill rate < 85%"
        " over lines due in [cutoff, cutoff+60d)",
        "delay_definition": "first receipt minus Expected Arrival in days; early = 0;"
        " nothing within 14 days = 14",
        "on_time_definition": f"first receipt by Expected Arrival + {GRACE.days} day",
        "label_horizon_days": HORIZON.days,
        "coverage": coverage,
        "class_support_all_rows": dict(sorted(Counter(str(r.label) for r in rows).items())),
        "split": {
            "boundary": split.boundary.isoformat(),
            "held_out_suppliers": list(split.test_suppliers),
            "train_rows": len(split.train),
            "test_rows": len(split.test),
            "temporal_test_rows": len(split.temporal_test),
            "train_id": rows_id(split.train),
            "rule": "train = other suppliers with labels observable by boundary; "
            "test = held-out suppliers with cutoff >= boundary",
        },
    }  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("command", choices=("extract", "train", "all", "report"))
    parser.add_argument("--products", type=lambda v: [int(x) for x in v.split(",")])
    parser.add_argument("--company", type=int, default=1)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    export_path = OUT / "history_export.json"
    if args.command in ("extract", "all"):
        export = asyncio.run(extract(args.products or _default_products(), args.company))
        export_path.write_text(canonical(export) + "\n", encoding="utf-8")
        print(f"Extracted {len(export['lines'])} purchase lines from {export['database']}")
    if args.command == "report":
        reference = ROOT / "docs" / "evidence" / "P1_ML_REPORT.json"
        check = report_check(
            json.loads(export_path.read_text(encoding="utf-8")),
            OUT / "model",
            json.loads(reference.read_text(encoding="utf-8")),
        )
        target = ROOT / "docs" / "evidence" / "P4_ML_REPORT_CHECK.json"
        target.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
        print(canonical({k: check[k] for k in ("unchanged", "identical_to_reference")}))
    if args.command in ("train", "all"):
        report = train_from_export(json.loads(export_path.read_text(encoding="utf-8")))
        primary = report["evaluation"]["primary_supplier_and_time_holdout"]
        print(canonical({
            "model_id": report["model"]["model_id"],
            "depth": report["model"]["depth_selection"],
            "test_rows": primary["rows"],
            "tree_macro_f1": primary["decision_tree"]["macro"]["f1"],
            "baselines_macro_f1": {k: v["macro"]["f1"] for k, v in primary["baselines"].items()},
        }))  # fmt: skip


if __name__ == "__main__":
    main()
