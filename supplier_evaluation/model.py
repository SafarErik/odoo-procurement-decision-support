"""Fixed offline DecisionTreeClassifier training and validated explainable inference."""

import platform
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, localcontext

import joblib
import numpy as np
import scipy
import sklearn
import threadpoolctl
from sklearn.tree import DecisionTreeClassifier, export_text

from supplier_evaluation.contracts import (
    ARTIFACT_VERSION,
    CLASSES,
    DATASET_VERSION,
    FEATURE_VERSION,
    FEATURES,
    LABEL_VERSION,
    MAPPING_VERSION,
    SEED,
    SYNTHETIC,
    Assessment,
    FeatureSnapshot,
    PathStep,
    QuantityValidity,
    digest,
)
from supplier_evaluation.dataset import Split

CONFIG = {
    "criterion": "gini",
    "splitter": "best",
    "max_depth": 3,
    "min_samples_leaf": 10,
    "min_samples_split": 20,
    "random_state": SEED,
    "class_weight": None,
    "ccp_alpha": 0.0,
}


def runtime() -> dict[str, str]:
    return {
        "python": ".".join(platform.python_version_tuple()[:2]),
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "joblib": joblib.__version__,
        "threadpoolctl": threadpoolctl.__version__,
    }


def check_envelope(metadata: dict) -> None:
    expected = {
        "artifact_version": ARTIFACT_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": list(FEATURES),
        "label_version": LABEL_VERSION,
        "class_names": list(CLASSES),
        "mapping_version": MAPPING_VERSION,
        "dataset_version": DATASET_VERSION,
        "config": CONFIG,
        "runtime": runtime(),
        "source_type": SYNTHETIC,
    }
    if any(metadata.get(k) != v for k, v in expected.items()):
        raise ValueError("Incompatible artifact schema, classes, config or runtime.")
    if set(metadata) != set(expected) | {
        "training_id",
        "model_id",
        "trained_through",
        "domain",
        "train_rows",
        "train_class_support",
    }:
        raise ValueError("Incompatible artifact metadata fields.")
    from supplier_evaluation.contracts import text_identity, utc

    for key in ("training_id", "model_id"):
        text_identity(metadata[key])
    utc(datetime.fromisoformat(metadata["trained_through"]))
    if (
        not isinstance(metadata["domain"], list)
        or len(metadata["domain"]) != 3
        or any(not isinstance(x, str) or not x.strip() for x in metadata["domain"])
        or type(metadata["train_rows"]) is not int
        or not isinstance(metadata["train_class_support"], list)
        or len(metadata["train_class_support"]) != 2
        or any(type(x) is not int or x < 20 for x in metadata["train_class_support"])
        or sum(metadata["train_class_support"]) != metadata["train_rows"]
    ):
        raise ValueError("Invalid artifact training support/context.")


def tree_state(tree: DecisionTreeClassifier) -> dict:
    t = tree.tree_
    return {
        name: getattr(t, name).tolist()
        for name in (
            "children_left",
            "children_right",
            "feature",
            "threshold",
            "value",
            "n_node_samples",
        )
    }


@dataclass(frozen=True)
class TreeModel:
    tree: DecisionTreeClassifier
    metadata: dict
    leaf_counts: dict[int, tuple[int, int]]

    def validate(self) -> None:
        check_envelope(self.metadata)
        tree = self.tree
        if (
            type(tree) is not DecisionTreeClassifier
            or not hasattr(tree, "tree_")
            or tree.n_features_in_ != len(FEATURES)
            or tree.classes_.tolist() != [0, 1]
            or tree.get_params() != DecisionTreeClassifier(**CONFIG).get_params()
            or tree.get_depth() > 3
            or tree.get_n_leaves() > 8
            or tree.tree_.n_node_samples[0] != self.metadata["train_rows"]
        ):
            raise ValueError("Incompatible fitted classifier.")
        actual_leaves = set(np.flatnonzero(tree.tree_.children_left == -1).tolist())
        if set(self.leaf_counts) != actual_leaves:
            raise ValueError("Artifact leaf-support mismatch.")
        for leaf, counts in self.leaf_counts.items():
            if (
                not isinstance(counts, tuple)
                or len(counts) != 2
                or any(type(n) is not int or n < 0 for n in counts)
                or sum(counts) < 10
                or sum(counts) != int(tree.tree_.n_node_samples[leaf])
                or not np.allclose(
                    tree.tree_.value[leaf, 0], np.array(counts) / sum(counts), rtol=0, atol=1e-12
                )
            ):
                raise ValueError("Corrupt artifact leaf counts.")
        if [sum(c[i] for c in self.leaf_counts.values()) for i in (0, 1)] != self.metadata[
            "train_class_support"
        ]:
            raise ValueError("Corrupt artifact class support.")
        identity = {k: v for k, v in self.metadata.items() if k != "model_id"}
        if (
            digest(
                {"metadata": identity, "tree": tree_state(tree), "leaf_counts": self.leaf_counts}
            )
            != self.metadata["model_id"]
        ):
            raise ValueError("Artifact semantic identity mismatch.")

    def infer(self, snapshot: FeatureSnapshot, quantities: QuantityValidity) -> Assessment:
        self.validate()
        if not isinstance(snapshot, FeatureSnapshot) or not isinstance(
            quantities, QuantityValidity
        ):
            raise ValueError("Typed inference features/quantity validity required.")
        if (
            snapshot.source_type != SYNTHETIC
            or list(snapshot.context.domain) != self.metadata["domain"]
            or snapshot.cutoff < datetime.fromisoformat(self.metadata["trained_through"])
        ):
            raise ValueError("Unsupported observed context or inference before training cutoff.")
        x = np.asarray([snapshot.values], dtype=np.float32)
        leaf = int(self.tree.apply(x)[0])
        predicted = int(self.tree.predict(x)[0])
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
                        FEATURES[index],
                        value,
                        "<=" if value <= threshold else ">",
                        threshold,
                    )
                )
        return Assessment(
            snapshot,
            quantities,
            snapshot.cutoff + timedelta(days=30),
            predicted,
            score,
            self.metadata["model_id"],
            self.metadata["training_id"],
            leaf,
            counts,
            tuple(path),
        )

    def global_explanation(self) -> dict:
        self.validate()
        return {
            "depth": int(self.tree.get_depth()),
            "leaves": int(self.tree.get_n_leaves()),
            "display_rules_rounded": export_text(self.tree, feature_names=list(FEATURES)),
            "feature_importances": dict(
                zip(FEATURES, self.tree.feature_importances_.tolist(), strict=True)
            ),
            "leaf_counts": self.leaf_counts,
        }


def train(split: Split) -> TreeModel:
    """Only canonical training snapshots/labels enter fit; no held-out model selection."""
    if not isinstance(split, Split):
        raise ValueError("Validated split required.")
    rows = sorted(split.train, key=lambda e: e.observation_id)
    support = Counter(e.label for e in rows)
    if any(support[k] < 20 for k in (0, 1)):
        raise ValueError("Insufficient training class support: at least 20 per class required.")
    x = np.asarray([e.snapshot.values for e in rows], dtype=np.float32)
    y = np.asarray([e.label for e in rows], dtype=np.int64)
    tree = DecisionTreeClassifier(**CONFIG).fit(x, y)
    leaves = tree.apply(x)
    counts = {
        int(leaf): tuple(int(np.sum(y[leaves == leaf] == k)) for k in (0, 1))
        for leaf in sorted(set(leaves))
    }
    metadata = {
        "artifact_version": ARTIFACT_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": list(FEATURES),
        "label_version": LABEL_VERSION,
        "class_names": list(CLASSES),
        "mapping_version": MAPPING_VERSION,
        "dataset_version": DATASET_VERSION,
        "config": CONFIG,
        "runtime": runtime(),
        "source_type": SYNTHETIC,
        "training_id": digest([asdict(e) for e in rows]),
        "trained_through": max(e.label_available_at for e in rows).isoformat(),
        "domain": list(rows[0].snapshot.context.domain),
        "train_rows": len(rows),
        "train_class_support": [support[0], support[1]],
    }
    metadata["model_id"] = digest(
        {"metadata": metadata, "tree": tree_state(tree), "leaf_counts": counts}
    )
    model = TreeModel(tree, metadata, counts)
    model.validate()
    return model
