"""One bounded Decision Tree; feature engineering and allocation remain separate."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.tree import DecisionTreeClassifier, export_text

from tools.v2_ml_risk.dataset import FEATURES, SCHEMA_VERSION, Dataset, digest, feature_vector

PARAMETERS = {
    "criterion": "gini",
    "splitter": "best",
    "max_depth": 3,
    "min_samples_leaf": 12,
    "min_samples_split": 24,
    "random_state": 17,
    "class_weight": None,
}


@dataclass(frozen=True)
class SupplierRiskAssessment:
    supplier_id: str
    ml_risk_score: Decimal
    predicted_class: int
    model_version: str
    evaluation_context: str
    observation_timestamp: datetime
    explanation: dict


class RiskModel:
    def __init__(self, dataset: Dataset):
        if len(dataset.train) < 24 or {e.outcome.schedule_miss for e in dataset.train} != {0, 1}:
            raise ValueError("Training requires both classes and support for the bounded tree.")
        self.train_x = np.asarray([e.features for e in dataset.train], dtype=np.float32)
        self.train_y = np.asarray([e.outcome.schedule_miss for e in dataset.train])
        self.tree = DecisionTreeClassifier(**PARAMETERS).fit(self.train_x, self.train_y)
        tree = self.tree.tree_
        self.model_version = digest(
            {
                "dataset": dataset.dataset_hash,
                "schema": SCHEMA_VERSION,
                "features": FEATURES,
                "parameters": self.tree.get_params(),
                "children_left": tree.children_left.tolist(),
                "children_right": tree.children_right.tolist(),
                "feature": tree.feature.tolist(),
                "threshold_hex": [float(v).hex() for v in tree.threshold],
                "value_hex": [float(v).hex() for v in tree.value.ravel()],
            }
        )
        self.trained_at = datetime.now(UTC)
        self.training_cutoff = dataset.cutoff
        self.train_leaves = self.tree.apply(self.train_x)

    def assess(
        self,
        supplier_id: str,
        values: dict[str, float],
        decision_at: datetime,
        context: str = "synthetic-feasibility-only",
    ) -> SupplierRiskAssessment:
        if decision_at < self.training_cutoff:
            raise ValueError("Prediction cannot precede the model's training-data cutoff.")
        vector = feature_vector(values)
        x = np.asarray([vector], dtype=np.float32)
        predicted = int(self.tree.predict(x)[0])
        leaf = int(self.tree.apply(x)[0])
        labels = self.train_y[self.train_leaves == leaf]
        counts = [int(sum(labels == label)) for label in (0, 1)]
        raw_score = float(self.tree.predict_proba(x)[0, list(self.tree.classes_).index(1)])
        canonical_score = (Decimal(counts[1]) / sum(counts)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        path = []
        tree = self.tree.tree_
        for node in self.tree.decision_path(x).indices:
            if node == leaf:
                continue
            feature = int(tree.feature[node])
            threshold = float(tree.threshold[node])
            value = float(x[0, feature])
            path.append(
                {
                    "feature": FEATURES[feature],
                    "value_float32": value,
                    "operator": "<=" if value <= threshold else ">",
                    "threshold": threshold,
                }
            )
        return SupplierRiskAssessment(
            supplier_id,
            canonical_score,
            predicted,
            self.model_version,
            context,
            decision_at,
            {
                "features": dict(zip(FEATURES, vector, strict=True)),
                "rules_traversed": path,
                "leaf_id": leaf,
                "leaf_sample_count": int(len(labels)),
                "leaf_class_counts_0_1": counts,
                "raw_positive_class_score": raw_score,
                "canonical_score": str(canonical_score),
                "score_is_calibrated_probability": False,
            },
        )

    def global_explanation(self) -> dict:
        return {
            "depth": int(self.tree.get_depth()),
            "leaves": int(self.tree.get_n_leaves()),
            "feature_importances": dict(
                zip(FEATURES, self.tree.feature_importances_.tolist(), strict=True)
            ),
            "rules_display_rounded": export_text(self.tree, feature_names=list(FEATURES)),
            "leaf_support": [
                {
                    "leaf": int(leaf),
                    "count": int(sum(self.train_leaves == leaf)),
                    "class_counts_0_1": [
                        int(sum(self.train_y[self.train_leaves == leaf] == k)) for k in (0, 1)
                    ],
                }
                for leaf in sorted(set(self.train_leaves))
            ],
        }


def metrics(y: list[int], predicted: list[int]) -> dict:
    if set(y) != {0, 1}:
        raise ValueError("Both holdout classes are needed; no meaningful metrics fabricated.")
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, predicted, average="binary", pos_label=1, zero_division=0
    )
    return {
        "confusion_matrix_labels_0_1": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
        "positive_precision": float(precision),
        "positive_recall": float(recall),
        "positive_f1": float(f1),
        "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "accuracy": float(accuracy_score(y, predicted)),
        "support": len(y),
        "class_support_0_1": [y.count(0), y.count(1)],
    }
