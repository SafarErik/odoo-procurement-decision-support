"""Explicit controlled-Odoo qualification around unchanged synthetic-trained tree bytes."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from supplier_evaluation.artifacts import load_model
from supplier_evaluation.contracts import (
    ODOO_HISTORY,
    ODOO_MAPPING_VERSION,
    SYNTHETIC,
    FeatureSnapshot,
    QuantityValidity,
    canonical,
    digest,
)
from supplier_evaluation.model import TreeModel
from supplier_evaluation.odoo_compatibility import PROTOCOL

PACKAGE_VERSION = "t14-qualified-odoo-controlled-v1"
CAPABILITIES = {
    "source_type": ODOO_HISTORY,
    "evidence_origin": "controlled_synthetic",
    "domain": ["odoo:res.company:1", "odoo:product.product:54", "odoo:uom.uom:1"],
    "support_range": [3, 30],
    "quantity_range": [1, 1000],
    "profile_id": "local-v1",
    "database": "procurement_v2_history_test_v1",
}


def qualification_metadata(candidate, report):
    if (
        report.get("decision") != "GO"
        or report.get("protocol") != PROTOCOL
        or report.get("protocol_hash") != digest(PROTOCOL)
        or report.get("report_hash")
        != digest({k: v for k, v in report.items() if k != "report_hash"})
        or report.get("candidate_manifest") != candidate
        or set(report.get("cohorts", {})) != {"n3", "support_3_to_30"}
    ):
        raise ValueError("No matching frozen GO evaluation for this candidate.")
    for cohort in report["cohorts"].values():
        m, baseline = cohort["metrics"], cohort["majority_baseline"]
        if (
            cohort["passed"] is not True
            or min(c["support"] for c in m["per_class"]) < 20
            or m["accuracy"] < baseline["accuracy"]
            or m["macro"]["f1"] <= baseline["macro"]["f1"]
            or cohort["supplier_groups_disjoint"] is not True
            or cohort["receipt_ids_unique"] is not True
        ):
            raise ValueError("Compatibility acceptance gate failed.")
    old = candidate["metadata"]
    if old["source_type"] != SYNTHETIC or old["domain"] != CAPABILITIES["domain"]:
        raise ValueError("Unsupported candidate domain or training source.")
    metadata = dict(
        old,
        artifact_version=PACKAGE_VERSION,
        source_type=ODOO_HISTORY,
        training_source_type=SYNTHETIC,
        mapping_version=ODOO_MAPPING_VERSION,
        compatibility=CAPABILITIES,
        compatibility_report_hash=report["report_hash"],
        candidate_model_id=old["model_id"],
    )
    metadata["model_id"] = digest({k: v for k, v in metadata.items() if k != "model_id"})
    return metadata


def qualify(candidate_directory: Path, report_path: Path, output: Path):
    """Publish only after GO; never train or overwrite an existing package."""
    candidate = json.loads((candidate_directory / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metadata = qualification_metadata(candidate, report)
    load_model(candidate_directory, trusted_local=True)
    output.mkdir(parents=True, exist_ok=False)
    original = output / "candidate"
    original.mkdir()
    for name in ("manifest.json", "tree.joblib"):
        (original / name).write_bytes((candidate_directory / name).read_bytes())
    manifest = {
        "metadata": metadata,
        "artifact_sha256": candidate["artifact_sha256"],
        "candidate_manifest": candidate,
        "compatibility_report": report,
    }
    (output / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
    return manifest


@dataclass(frozen=True)
class QualifiedOdooModel:
    candidate: TreeModel
    metadata: dict

    def infer(self, snapshot: FeatureSnapshot, quantities: QuantityValidity):
        self.candidate.validate()
        caps = self.metadata["compatibility"]
        if (
            caps != CAPABILITIES
            or self.metadata["candidate_model_id"] != self.candidate.metadata["model_id"]
            or self.metadata["model_id"]
            != digest({k: v for k, v in self.metadata.items() if k != "model_id"})
        ):
            raise ValueError("Qualified model metadata changed.")
        suffix = (
            f"|database={caps['database']}|origin={caps['evidence_origin']}"
            f"|profile={caps['profile_id']}|capture="
        )
        if (
            not isinstance(snapshot, FeatureSnapshot)
            or not isinstance(quantities, QuantityValidity)
            or snapshot.source_type != ODOO_HISTORY
            or list(snapshot.context.domain) != caps["domain"]
            or not caps["support_range"][0] <= snapshot.values[1] <= caps["support_range"][1]
            or not caps["quantity_range"][0]
            <= quantities.minimum
            <= quantities.maximum
            <= caps["quantity_range"][1]
            or snapshot.cutoff < datetime.fromisoformat(self.metadata["trained_through"])
            or re.search(re.escape(suffix) + r"[0-9a-f]{64}$", snapshot.source_reference) is None
        ):
            raise ValueError("Odoo history source/model compatibility or validity mismatch.")
        return self.candidate._assess(
            snapshot,
            quantities,
            mapping_version=ODOO_MAPPING_VERSION,
            model_id=self.metadata["model_id"],
        )


def load_qualified_model(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if set(manifest) != {
        "metadata",
        "artifact_sha256",
        "candidate_manifest",
        "compatibility_report",
    }:
        raise ValueError("Invalid qualified artifact envelope.")
    expected = qualification_metadata(
        manifest["candidate_manifest"], manifest["compatibility_report"]
    )
    if (
        manifest["metadata"] != expected
        or manifest["artifact_sha256"] != manifest["candidate_manifest"]["artifact_sha256"]
    ):
        raise ValueError("Qualified artifact identity mismatch.")
    original = json.loads((directory / "candidate/manifest.json").read_text(encoding="utf-8"))
    if original != manifest["candidate_manifest"]:
        raise ValueError("Candidate changed after qualification.")
    model = load_model(directory / "candidate", trusted_local=True)
    return QualifiedOdooModel(model, expected), manifest
