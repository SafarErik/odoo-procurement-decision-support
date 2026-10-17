"""Decision Tree trained on Odoo purchase history: selection, baselines, artifact, inference."""

import hashlib
import io
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier, export_text

from supplier_evaluation.contracts import (
    HISTORY_DATASET_VERSION,
    HISTORY_FEATURE_VERSION,
    HISTORY_FEATURES,
    HISTORY_LABEL_VERSION,
    HISTORY_MAPPING_VERSION,
    HISTORY_SOURCE,
    Assessment,
    FeatureSnapshot,
    PathStep,
    QuantityValidity,
    canonical,
    digest,
    text_identity,
    utc,
)
from supplier_evaluation.evaluation import classification_metrics
from supplier_evaluation.model import runtime, tree_state
from supplier_evaluation.purchase_history import HistorySplit, Row, rows_id

ARTIFACT_VERSION = "odoo-history-tree-v2"
CLASSES = ("regular", "problematic")
SEED = 17
DEPTHS = (1, 2, 3, 4, 5)
CV_FOLDS = 4
BASE_CONFIG = {
    "criterion": "gini",
    "splitter": "best",
    "min_samples_leaf": 10,
    "min_samples_split": 20,
    "random_state": SEED,
    "class_weight": None,
    "ccp_alpha": 0.0,
}
EXPERT_RULE = {"feature": "on_time_rate", "operator": "<", "threshold": 0.8}
METADATA_FIELDS = {
    "artifact_version",
    "feature_version",
    "feature_names",
    "label_version",
    "class_names",
    "mapping_version",
    "dataset_version",
    "config",
    "runtime",
    "source_type",
    "data_origin",
    "database",
    "company_id",
    "training_id",
    "trained_through",
    "train_rows",
    "train_class_support",
    "depth_selection",
    "model_id",
}


def _xy(rows):
    x = np.asarray([r.values for r in rows], dtype=np.float32)
    y = np.asarray([r.label for r in rows], dtype=np.int64)
    return x, y


def time_series_folds(rows: tuple[Row, ...], folds: int = CV_FOLDS):
    """Expanding-window folds over train cutoffs; fit rows' labels end before validation."""
    cutoffs = sorted({r.cutoff for r in rows})
    blocks = np.array_split(np.array(cutoffs, dtype=object), folds + 1)
    for block in blocks[1:]:
        if not len(block):
            continue
        start = block[0]
        fit = tuple(r for r in rows if r.label_available_at <= start)
        validate = tuple(r for r in rows if r.cutoff in set(block))
        if fit and validate and len({r.label for r in fit}) == 2:
            yield fit, validate


def select_depth(rows: tuple[Row, ...]) -> dict:
    """Mean macro F1 per depth across time-series folds on train rows only."""
    scores = {}
    for depth in DEPTHS:
        fold_scores = []
        for fit, validate in time_series_folds(rows):
            x, y = _xy(fit)
            tree = DecisionTreeClassifier(max_depth=depth, **BASE_CONFIG).fit(x, y)
            vx, vy = _xy(validate)
            f1 = classification_metrics(vy.tolist(), tree.predict(vx).tolist())["macro"]["f1"]
            fold_scores.append(0.0 if f1 is None else f1)
        if not fold_scores:
            raise ValueError("Time-series cross-validation produced no usable fold.")
        scores[str(depth)] = round(float(np.mean(fold_scores)), 6)
    best = max(scores.values())
    chosen = min(int(d) for d, s in scores.items() if s >= best - 1e-9)
    return {"metric": "mean_macro_f1", "folds": CV_FOLDS, "scores": scores, "chosen": chosen}


@dataclass(frozen=True)
class HistoryTreeModel:
    tree: DecisionTreeClassifier
    metadata: dict
    leaf_counts: dict[int, tuple[int, int]]

    def validate(self) -> None:
        check_manifest_metadata(self.metadata)
        tree, depth = self.tree, self.metadata["depth_selection"]["chosen"]
        expected = DecisionTreeClassifier(max_depth=depth, **BASE_CONFIG).get_params()
        if (
            type(tree) is not DecisionTreeClassifier
            or tree.n_features_in_ != len(HISTORY_FEATURES)
            or tree.classes_.tolist() != [0, 1]
            or tree.get_params() != expected
            or tree.tree_.n_node_samples[0] != self.metadata["train_rows"]
        ):
            raise ValueError("Incompatible fitted classifier.")
        leaves = set(np.flatnonzero(tree.tree_.children_left == -1).tolist())
        if set(self.leaf_counts) != leaves or any(
            sum(c) != int(tree.tree_.n_node_samples[leaf]) for leaf, c in self.leaf_counts.items()
        ):
            raise ValueError("Artifact leaf-support mismatch.")
        identity = {k: v for k, v in self.metadata.items() if k != "model_id"}
        semantic = {"metadata": identity, "tree": tree_state(tree), "leaf_counts": self.leaf_counts}
        if digest(semantic) != self.metadata["model_id"]:
            raise ValueError("Artifact semantic identity mismatch.")

    def infer(self, snapshot: FeatureSnapshot, quantities: QuantityValidity) -> Assessment:
        self.validate()
        if (
            not isinstance(snapshot, FeatureSnapshot)
            or not isinstance(quantities, QuantityValidity)
            or snapshot.source_type != HISTORY_SOURCE
            or snapshot.feature_version != HISTORY_FEATURE_VERSION
            or snapshot.context.company_id != self.metadata["company_id"]
            or f"|database={self.metadata['database']}|" not in snapshot.source_reference + "|"
            or snapshot.cutoff < datetime.fromisoformat(self.metadata["trained_through"])
        ):
            raise ValueError("Snapshot source, company, database or cutoff is unsupported.")
        x = np.asarray([snapshot.values], dtype=np.float32)
        leaf = int(self.tree.apply(x)[0])
        counts = self.leaf_counts[leaf]
        with localcontext() as ctx:
            ctx.prec = 28
            score = (Decimal(counts[1]) / sum(counts)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        t, path = self.tree.tree_, []
        for node in self.tree.decision_path(x).indices:
            if node != leaf:
                index = int(t.feature[node])
                value, threshold = float(x[0, index]), float(t.threshold[node])
                path.append(
                    PathStep(
                        int(node),
                        HISTORY_FEATURES[index],
                        value,
                        "<=" if value <= threshold else ">",
                        threshold,
                    )
                )
        return Assessment(
            snapshot,
            quantities,
            snapshot.cutoff + timedelta(days=30),
            int(counts[1] > counts[0]),
            score,
            self.metadata["model_id"],
            self.metadata["training_id"],
            leaf,
            counts,
            tuple(path),
            HISTORY_MAPPING_VERSION,
            HISTORY_DATASET_VERSION,
            HISTORY_LABEL_VERSION,
        )

    def predict(self, rows) -> list[int]:
        x, _ = _xy(rows)
        counts = [self.leaf_counts[int(leaf)] for leaf in self.tree.apply(x)]
        return [int(c[1] > c[0]) for c in counts]

    def global_explanation(self) -> dict:
        return {
            "depth": int(self.tree.get_depth()),
            "leaves": int(self.tree.get_n_leaves()),
            "rules": export_text(self.tree, feature_names=list(HISTORY_FEATURES), decimals=3),
            "feature_importances": dict(
                zip(
                    HISTORY_FEATURES,
                    (round(v, 6) for v in self.tree.feature_importances_),
                    strict=True,
                )
            ),
            "leaf_counts": {str(k): list(v) for k, v in sorted(self.leaf_counts.items())},
        }


def check_manifest_metadata(metadata: dict) -> None:
    """Static compatibility check usable on stored snapshots without loading a file."""
    expected = {
        "artifact_version": ARTIFACT_VERSION,
        "feature_version": HISTORY_FEATURE_VERSION,
        "feature_names": list(HISTORY_FEATURES),
        "label_version": HISTORY_LABEL_VERSION,
        "class_names": list(CLASSES),
        "mapping_version": HISTORY_MAPPING_VERSION,
        "dataset_version": HISTORY_DATASET_VERSION,
        "source_type": HISTORY_SOURCE,
        "data_origin": "generated",
    }
    if set(metadata) != METADATA_FIELDS or any(metadata[k] != v for k, v in expected.items()):
        raise ValueError("Incompatible history model metadata.")
    depth = metadata["depth_selection"]["chosen"]
    if metadata["config"] != dict(BASE_CONFIG, max_depth=depth) or depth not in DEPTHS:
        raise ValueError("Incompatible history model configuration.")
    for key in ("training_id", "model_id", "database", "company_id"):
        text_identity(metadata[key])
    utc(datetime.fromisoformat(metadata["trained_through"]))
    support = metadata["train_class_support"]
    if (
        not isinstance(support, list)
        or len(support) != 2
        or any(type(n) is not int or n < 20 for n in support)
        or sum(support) != metadata["train_rows"]
    ):
        raise ValueError("Insufficient history model training support.")


def train(split: HistorySplit, *, database: str) -> HistoryTreeModel:
    rows = tuple(sorted(split.train, key=lambda r: r.row_id))
    support = Counter(r.label for r in rows)
    if any(support[k] < 20 for k in (0, 1)):
        raise ValueError("Insufficient training class support: at least 20 per class required.")
    selection = select_depth(rows)
    config = dict(BASE_CONFIG, max_depth=selection["chosen"])
    x, y = _xy(rows)
    tree = DecisionTreeClassifier(**config).fit(x, y)
    leaves = tree.apply(x)
    counts = {
        int(leaf): tuple(int(np.sum(y[leaves == leaf] == k)) for k in (0, 1))
        for leaf in sorted(set(leaves.tolist()))
    }
    metadata = {
        "artifact_version": ARTIFACT_VERSION,
        "feature_version": HISTORY_FEATURE_VERSION,
        "feature_names": list(HISTORY_FEATURES),
        "label_version": HISTORY_LABEL_VERSION,
        "class_names": list(CLASSES),
        "mapping_version": HISTORY_MAPPING_VERSION,
        "dataset_version": HISTORY_DATASET_VERSION,
        "config": config,
        "runtime": runtime(),
        "source_type": HISTORY_SOURCE,
        "data_origin": "generated",
        "database": database,
        "company_id": rows[0].context.company_id,
        "training_id": rows_id(rows),
        "trained_through": max(r.label_available_at for r in rows).isoformat(),
        "train_rows": len(rows),
        "train_class_support": [support[0], support[1]],
        "depth_selection": selection,
    }
    metadata["model_id"] = digest(
        {"metadata": metadata, "tree": tree_state(tree), "leaf_counts": counts}
    )
    model = HistoryTreeModel(tree, metadata, counts)
    model.validate()
    return model


def expert_rule(rows) -> list[int]:
    index = HISTORY_FEATURES.index(EXPERT_RULE["feature"])
    return [int(r.values[index] < EXPERT_RULE["threshold"]) for r in rows]


def evaluate(model: HistoryTreeModel, split: HistorySplit) -> dict:
    """Held-out metrics against majority, fixed expert rule and a learned one-split stump."""
    model.validate()
    majority = Counter(r.label for r in split.train).most_common(1)[0][0]
    x, y = _xy(split.train)
    stump = DecisionTreeClassifier(max_depth=1, **BASE_CONFIG).fit(x, y)
    stump_rule = export_text(stump, feature_names=list(HISTORY_FEATURES), decimals=3)

    def auc(labels, scores):
        return round(float(roc_auc_score(labels, scores)), 6) if len(set(labels)) == 2 else None

    def report(rows):
        labels = [r.label for r in rows]
        x_rows = _xy(rows)[0]
        tree_scores = [
            model.leaf_counts[int(leaf)][1] / sum(model.leaf_counts[int(leaf)])
            for leaf in model.tree.apply(x_rows)
        ]
        on_time = HISTORY_FEATURES.index("on_time_rate")
        return {
            "score_roc_auc": {
                "decision_tree_leaf_score": auc(labels, tree_scores),
                "one_minus_on_time_rate": auc(labels, [1 - r.values[on_time] for r in rows]),
            },
            "rows": len(rows),
            "suppliers": len({r.context.supplier_id for r in rows}),
            "class_support": {str(k): v for k, v in sorted(Counter(labels).items())},
            "decision_tree": classification_metrics(labels, model.predict(rows)),
            "baselines": {
                "majority_class": classification_metrics(labels, [majority] * len(rows)),
                "expert_rule_on_time_below_80pct": classification_metrics(
                    labels, expert_rule(rows)
                ),
                "learned_single_split": classification_metrics(
                    labels, stump.predict(_xy(rows)[0]).tolist()
                ),
            },
        }

    return {
        "primary_supplier_and_time_holdout": report(split.test),
        "supplementary_time_holdout_all_suppliers": report(split.temporal_test),
        "train_fit": report(split.train),
        "baseline_definitions": {
            "majority_class": f"always predict train majority class {majority}",
            "expert_rule_on_time_below_80pct": EXPERT_RULE,
            "learned_single_split": stump_rule,
        },
    }


def save_model(model: HistoryTreeModel, directory: Path) -> dict:
    model.validate()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "tree.joblib"
    joblib.dump({"tree": model.tree, "leaf_counts": model.leaf_counts}, path, compress=3)
    manifest = {
        "metadata": model.metadata,
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (directory / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
    return manifest


def load_model(directory: Path, *, trusted_local: bool = False) -> tuple[HistoryTreeModel, dict]:
    """Only for artifacts this pipeline wrote locally; joblib can execute code."""
    if trusted_local is not True:
        raise ValueError("Explicit trusted locally generated artifact required.")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if set(manifest) != {"metadata", "artifact_sha256"}:
        raise ValueError("Incompatible model manifest.")
    check_manifest_metadata(manifest["metadata"])
    data = (directory / "tree.joblib").read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest["artifact_sha256"]:
        raise ValueError("Model artifact checksum mismatch.")
    payload = joblib.load(io.BytesIO(data))
    if not isinstance(payload, dict) or set(payload) != {"tree", "leaf_counts"}:
        raise ValueError("Incompatible fitted model payload.")
    model = HistoryTreeModel(payload["tree"], manifest["metadata"], payload["leaf_counts"])
    model.validate()
    return model, manifest


FEATURE_TEXT = {
    "on_time_rate": ("on-time delivery rate", "{:.1%}"),
    "mean_lateness_days": ("average lateness", "{:.1f} days"),
    "lateness_spread_days": ("lateness spread", "{:.1f} days"),
    "fill_rate": ("fill rate", "{:.1%}"),
    "partial_share": ("share of partial deliveries", "{:.1%}"),
    "order_count": ("number of settled orders", "{:.0f}"),
    "days_since_last_receipt": ("days since last receipt", "{:.0f}"),
}


def path_text(assessment: Assessment) -> list[str]:
    """Readable decision path, one sentence per split, plus the leaf outcome."""
    lines = []
    for step in assessment.path:
        name, fmt = FEATURE_TEXT[step.feature]
        relation = "at most" if step.operator == "<=" else "above"
        lines.append(
            f"The {name} is {fmt.format(step.value_float32)}, {relation} "
            f"{fmt.format(step.threshold)}."
        )
    regular, problematic = assessment.leaf_counts
    lines.append(
        f"Similar past cases: {problematic} of {regular + problematic} were problematic "
        f"in the following 60 days; risk score {assessment.score}."
    )
    return lines
