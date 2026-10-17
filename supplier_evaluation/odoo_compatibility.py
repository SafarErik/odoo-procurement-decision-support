"""One frozen offline compatibility evaluation; never fit or access Odoo."""

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from supplier_evaluation.artifacts import load_model
from supplier_evaluation.contracts import Context, LineEvidence, QuantityValidity, canonical, digest
from supplier_evaluation.dataset import (
    BOUNDARY,
    EXTRACTED_AT,
    Observation,
    future_label,
    generate_dataset,
    prepare_dataset,
    prepare_features,
)
from supplier_evaluation.evaluation import classification_metrics, evaluate

PROTOCOL = {
    "version": "odoo-controlled-compatibility-v1",
    "seed": 18,
    "cohort_size": 240,
    "support_range": [3, 30],
    "cutoff": "2026-05-01T00:00:00+00:00",
    "extracted_at": "2026-06-01T00:00:00+00:00",
    "origin": "controlled_synthetic",
    "minimum_class_support": 20,
    "accuracy_gate": "at_least_majority",
    "macro_f1_gate": "strictly_above_majority",
}


def validation_cohorts(domain):
    """Independent supplier/receipt identities; same declared controlled label mechanism."""
    rng = random.Random(PROTOCOL["seed"])
    cutoff = datetime.fromisoformat(PROTOCOL["cutoff"])
    cohorts = {}
    for cohort in ("n3", "support_3_to_30"):
        rows = []
        for i in range(PROTOCOL["cohort_size"]):
            context = Context(f"compat-{cohort}-{i:03}", *domain)
            count = 3 if cohort == "n3" else 3 + i % 28
            miss_rate = rng.uniform(0.05, 0.70)
            history = []
            for j in range(count):
                expected = cutoff - timedelta(days=2 + j * 5)
                completed = expected + timedelta(hours=12 if rng.random() < miss_rate else -12)
                history.append(
                    LineEvidence(
                        f"CH:{cohort}:{i}:{j}",
                        context,
                        expected,
                        completed,
                        completed + timedelta(hours=1),
                    )
                )
            adherence = (
                sum(line.completed_at <= line.expected_arrival for line in history) / count * 100
            )
            future_miss = 0.65 if adherence < 80 else 0.10
            outcomes = []
            for j in range(5):
                expected = cutoff + timedelta(days=3 + j * 5)
                completed = expected + timedelta(hours=12 if rng.random() < future_miss else -12)
                outcomes.append(
                    LineEvidence(
                        f"CY:{cohort}:{i}:{j}",
                        context,
                        expected,
                        completed,
                        completed + timedelta(hours=1),
                    )
                )
            rows.append(
                Observation(
                    f"compat:{cohort}:{i}",
                    context,
                    cutoff,
                    tuple(history),
                    tuple(outcomes),
                    f"{PROTOCOL['version']}:{cohort}:{i}",
                )
            )
        cohorts[cohort] = tuple(rows)
    return cohorts


def evaluate_candidate(directory: Path) -> dict:
    model = load_model(directory, trusted_local=True)
    domain = tuple(model.metadata["domain"])
    if domain != ("odoo:res.company:1", "odoo:product.product:54", "odoo:uom.uom:1"):
        raise ValueError("Candidate is not in the approved local Odoo domain.")
    original_rows = generate_dataset(domain=domain)
    original = prepare_dataset(original_rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    report = {
        "protocol": PROTOCOL,
        "protocol_hash": digest(PROTOCOL),
        "candidate_manifest": json.loads((directory / "manifest.json").read_text(encoding="utf-8")),
        "original_evaluation": evaluate(model, original),
        "cohorts": {},
    }
    groups = {row.context.supplier_id for row in original_rows}
    ids = {line.line_id for row in original_rows for line in row.history + row.outcomes}
    extracted = datetime.fromisoformat(PROTOCOL["extracted_at"])
    for name, rows in validation_cohorts(domain).items():
        labels, predictions = [], []
        for row in rows:
            if row.context.supplier_id in groups:
                raise ValueError("Supplier group leakage in compatibility evaluation.")
            groups.add(row.context.supplier_id)
            for line in row.history + row.outcomes:
                if line.line_id in ids:
                    raise ValueError("Receipt evidence reused across evaluation partitions.")
                ids.add(line.line_id)
            snapshot = prepare_features(row)
            label, _ = future_label(row, extracted)
            assessment = model.infer(snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
            labels.append(label)
            predictions.append(assessment.predicted_class)
        counts = Counter(labels)
        majority = max((0, 1), key=lambda k: (counts[k], -k))
        metrics = classification_metrics(labels, predictions)
        baseline = classification_metrics(labels, [majority] * len(labels))
        passed = (
            all(counts[k] >= PROTOCOL["minimum_class_support"] for k in (0, 1))
            and metrics["accuracy"] >= baseline["accuracy"]
            and metrics["macro"]["f1"] is not None
            and metrics["macro"]["f1"] > baseline["macro"]["f1"]
        )
        report["cohorts"][name] = {
            "metrics": metrics,
            "majority_baseline": baseline,
            "passed": passed,
            "evidence_hash": digest([asdict(row) for row in rows]),
            "prediction_hash": digest(predictions),
            "supplier_groups_disjoint": True,
            "receipt_ids_unique": True,
        }
    report["decision"] = "GO" if all(c["passed"] for c in report["cohorts"].values()) else "NO-GO"
    report["report_hash"] = digest(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; compatibility evidence is not overwritten.")
    report = evaluate_candidate(args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(canonical(report) + "\n")
    print(
        canonical(
            {
                "decision": report["decision"],
                "report_hash": report["report_hash"],
                "cohorts": {
                    k: {
                        "accuracy": v["metrics"]["accuracy"],
                        "macro_f1": v["metrics"]["macro"]["f1"],
                        "passed": v["passed"],
                    }
                    for k, v in report["cohorts"].items()
                },
            }
        )
    )


if __name__ == "__main__":
    main()
