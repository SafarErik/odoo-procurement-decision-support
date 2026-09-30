"""Run from repo root: python -m tools.v2_ml_risk.experiments."""

import json
import platform
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

from tools.v2_ml_risk.dataset import (
    DATASET_VERSION,
    FEATURES,
    SCHEMA_VERSION,
    TARGET_VERSION,
    Observation,
    digest,
    feature_values,
    synthetic_dataset,
    synthetic_rows,
)
from tools.v2_ml_risk.integration import allocation_proof
from tools.v2_ml_risk.model import PARAMETERS, RiskModel, metrics


def run() -> dict:
    data = synthetic_dataset()
    models = [RiskModel(data) for _ in range(3)]  # Repetition, not model selection.
    test_x = [e.features for e in data.test]
    predictions = [model.tree.predict(test_x).tolist() for model in models]
    score_hashes = [digest(model.tree.predict_proba(test_x).tolist()) for model in models]
    model = models[0]
    target = [e.outcome.schedule_miss for e in data.test]
    baseline = [int(1 - e.features[0] >= 0.5) for e in data.test]
    # Three fixed supplier contexts, same decision/quantity/product; no target-based selection.
    assessments = []
    history = tuple(
        item
        for item in data.outcomes
        if item.observation.decision_at < data.cutoff and item.available_at < data.cutoff
    )
    for supplier in ("S11", "S06", "S00"):
        context = Observation(
            f"quote-{supplier}",
            supplier,
            "P1",
            data.cutoff,
            None,
            100,
            (),
            data.cutoff,
        )
        assessments.append(model.assess(supplier, feature_values(context, history), data.cutoff))
    local = data.test[0]
    example = model.assess(
        local.outcome.observation.supplier_id,
        dict(zip(FEATURES, local.features, strict=True)),
        local.outcome.observation.decision_at,
    )
    return {
        "recommendation": "GO WITH CONDITIONS",
        "evidence_kind": "synthetic_pipeline_only",
        "dataset_version": DATASET_VERSION,
        "dataset_hash": data.dataset_hash,
        "feature_schema_version": SCHEMA_VERSION,
        "feature_schema_hash": digest({"version": SCHEMA_VERSION, "features": FEATURES}),
        "feature_order": FEATURES,
        "target_version": TARGET_VERSION,
        "target_definition": "full receipt completion > immutable decision-time Expected Arrival",
        "target_hash": digest({"version": TARGET_VERSION, "positive": "completion > expected"}),
        "model_version": model.model_version,
        "parameter_hash": digest(model.tree.get_params()),
        "configured_parameters": PARAMETERS,
        "all_effective_parameters": model.tree.get_params(),
        "training_timestamp": model.trained_at,
        "python": platform.python_version(),
        "libraries": {
            name: version(name)
            for name in (
                "scikit-learn",
                "numpy",
                "scipy",
                "joblib",
                "threadpoolctl",
                "cloudpickle",
                "pulp",
            )
        },
        "split": {
            "cutoff": data.cutoff,
            "export_as_of": data.as_of,
            "train": len(data.train),
            "test": len(data.test),
            "test_history": "frozen training outcome pool; no test outcomes",
            "train_class_counts_0_1": [
                sum(e.outcome.schedule_miss == k for e in data.train) for k in (0, 1)
            ],
        },
        "inventory": {
            "raw_lines": len(synthetic_rows()),
            "labelled_completed_lines": len(data.outcomes),
            "usable_feature_rows": len(data.train) + len(data.test),
            "suppliers": 12,
            "products": 1,
            "class_counts": dict(Counter(o.schedule_miss for o in data.outcomes)),
            "first_decision": min(o.observation.decision_at for o in data.outcomes),
            "last_decision": max(o.observation.decision_at for o in data.outcomes),
            "last_completion": max(o.completed_at for o in data.outcomes),
            "per_supplier": dict(Counter(o.observation.supplier_id for o in data.outcomes)),
            "missing_expected_arrival": 1,
            "unproven_reference_snapshot": 1,
            "exclusions_and_purges": data.exclusions,
        },
        "decision_tree": metrics(target, predictions[0]),
        "non_ml_baseline": {"rule": "1 - prior adherence >= 0.5", **metrics(target, baseline)},
        "global_explanation": model.global_explanation(),
        "local_holdout_example": {
            "id": local.outcome.observation.observation_id,
            "actual_class_for_evaluation_only": local.outcome.schedule_miss,
            **asdict(example),
        },
        "determinism": {
            "training_repetitions": 3,
            "model_hashes": [m.model_version for m in models],
            "score_hashes": score_hashes,
            "equal_models": len({m.model_version for m in models}) == 1,
            "equal_predictions": predictions[0] == predictions[1] == predictions[2],
            "equal_scores": len(set(score_hashes)) == 1,
        },
        "integration_assessments": [asdict(a) for a in assessments],
        "ml_to_milp": allocation_proof(tuple(assessments)),
        "real_data": {
            "live_availability_checked_at": "2026-09-30",
            "unauthenticated_login_probe": "ConnectError",
            "podman_machine_running": False,
            "live_history_read_performed": False,
            "established_leakage_safe_training_rows": 0,
            "actual_database_total": "unknown; no available live environment/export",
            "documented_controlled_fixture_lines": 4,
            "eligible_outcomes": 3,
            "class_counts_0_1": [1, 2],
            "suppliers": 1,
            "products": 1,
        },
    }


def encode(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


if __name__ == "__main__":
    result = run()
    output = Path("docs/spikes/v2-ml-supplier-risk-results.json")
    output.write_text(json.dumps(result, indent=2, default=encode) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "written": str(output),
                "train": result["split"]["train"],
                "test": result["split"]["test"],
                "tree": result["decision_tree"],
                "baseline": result["non_ml_baseline"],
                "determinism": result["determinism"],
                "integration": result["ml_to_milp"],
            },
            indent=2,
            default=encode,
        )
    )
