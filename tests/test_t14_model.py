"""Training-only fit, reproducibility, artifact gates and exact sklearn path explanations."""

import json
from dataclasses import replace

import numpy as np
import pytest
from sklearn.tree import DecisionTreeClassifier

from supplier_evaluation.artifacts import load_model, save_model
from supplier_evaluation.contracts import QuantityValidity
from supplier_evaluation.dataset import BOUNDARY, EXTRACTED_AT, generate_dataset, prepare_dataset
from supplier_evaluation.evaluation import classification_metrics, evaluate
from supplier_evaluation.model import train, tree_state


@pytest.fixture(scope="module")
def split():
    return prepare_dataset(generate_dataset(), boundary=BOUNDARY, extracted_at=EXTRACTED_AT)


@pytest.fixture(scope="module")
def model(split):
    return train(split)


def test_only_training_vectors_and_labels_enter_fit(split, monkeypatch):
    original, fitted = DecisionTreeClassifier.fit, []

    def capture(self, x, y, *args, **kwargs):
        fitted.append((x.copy(), y.copy()))
        return original(self, x, y, *args, **kwargs)

    monkeypatch.setattr(DecisionTreeClassifier, "fit", capture)
    train(split)
    assert len(fitted) == 1
    assert np.array_equal(
        fitted[0][0], np.array([e.snapshot.values for e in split.train], dtype=np.float32)
    )
    assert fitted[0][1].tolist() == [e.label for e in split.train]


def test_heldout_features_and_labels_do_not_change_fitted_model(split, model):
    changed = replace(
        split,
        test=tuple(
            replace(e, label=1 - e.label, snapshot=replace(e.snapshot, values=(0.0, 50.0)))
            for e in split.test
        ),
    )
    other = train(changed)
    assert other.metadata == model.metadata
    assert tree_state(other.tree) == tree_state(model.tree)


@pytest.mark.parametrize("support", (0, 19))
def test_single_or_insufficient_class_support_fails(split, support):
    changed = replace(
        split, train=tuple(replace(e, label=int(i < support)) for i, e in enumerate(split.train))
    )
    with pytest.raises(ValueError, match="class support"):
        train(changed)


def test_reproducible_training_permutation_reload_and_inference(
    split, model, tmp_path, monkeypatch
):
    repeated = train(replace(split, train=tuple(reversed(split.train))))
    assert repeated.metadata == model.metadata
    save_model(model, tmp_path)
    loaded = load_model(tmp_path, trusted_local=True)
    assert loaded.metadata == model.metadata
    assert tree_state(loaded.tree) == tree_state(model.tree)
    monkeypatch.setattr(
        DecisionTreeClassifier, "fit", lambda *a, **k: pytest.fail("Inference retrained")
    )
    validity = QuantityValidity(1, 1000, "controlled-proxy-v1")
    assert tuple(loaded.infer(e.snapshot, validity) for e in split.test) == tuple(
        model.infer(e.snapshot, validity) for e in split.test
    )


def test_actual_float32_path_leaf_class_and_counts_match_sklearn(split, model):
    for e in split.test:
        assessment = model.infer(e.snapshot, QuantityValidity(1, 1000, "controlled-proxy-v1"))
        x = np.array([e.snapshot.values], dtype=np.float32)
        assert assessment.leaf_id == model.tree.apply(x)[0]
        assert assessment.predicted_class == model.tree.predict(x)[0]
        assert [step.node_id for step in assessment.path] + [assessment.leaf_id] == list(
            model.tree.decision_path(x).indices
        )
        node = 0
        for step in assessment.path:
            assert node == step.node_id
            index = int(model.tree.tree_.feature[node])
            assert step.value_float32 == float(x[0, index])
            assert step.threshold == float(model.tree.tree_.threshold[node])
            node = int(
                model.tree.tree_.children_left[node]
                if step.operator == "<="
                else model.tree.tree_.children_right[node]
            )
            assert (step.value_float32 <= step.threshold) == (step.operator == "<=")
        assert node == assessment.leaf_id
        assert sum(assessment.leaf_counts) == model.tree.tree_.n_node_samples[node]
        assert abs(float(assessment.score) - model.tree.predict_proba(x)[0, 1]) <= 0.00005


@pytest.mark.parametrize(
    "field,value",
    (
        ("artifact_version", "unknown"),
        ("feature_version", "unknown"),
        ("feature_names", ["historical_completed_count", "delivery_schedule_adherence"]),
        ("class_names", ["watch", "regular"]),
        ("mapping_version", "unknown"),
        ("dataset_version", "unknown"),
        ("label_version", "unknown"),
        ("runtime", {}),
    ),
)
def test_incompatible_manifest_rejected_before_deserialization(
    model, tmp_path, monkeypatch, field, value
):
    save_model(model, tmp_path)
    path = tmp_path / "manifest.json"
    raw = json.loads(path.read_text())
    raw["metadata"][field] = value
    path.write_text(json.dumps(raw))
    monkeypatch.setattr(
        "supplier_evaluation.artifacts.joblib.load",
        lambda *a, **k: pytest.fail("Incompatible artifact was deserialized"),
    )
    with pytest.raises(ValueError, match="Incompatible"):
        load_model(tmp_path, trusted_local=True)


def test_checksum_and_trust_rejected_before_deserialization(model, tmp_path, monkeypatch):
    save_model(model, tmp_path)
    monkeypatch.setattr(
        "supplier_evaluation.artifacts.joblib.load",
        lambda *a, **k: pytest.fail("Invalid artifact was deserialized"),
    )
    with pytest.raises(ValueError, match="trusted"):
        load_model(tmp_path)
    artifact = tmp_path / "tree.joblib"
    artifact.write_bytes(artifact.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="checksum"):
        load_model(tmp_path, trusted_local=True)


def test_corrupt_leaf_counts_configuration_and_semantic_state_rejected(model):
    import copy

    for corruption in ("counts", "config", "threshold"):
        changed = copy.deepcopy(model)
        if corruption == "counts":
            leaf = next(iter(changed.leaf_counts))
            changed.leaf_counts[leaf] = (1, 1)
        elif corruption == "config":
            changed.tree.max_features = 1
        else:
            changed.tree.tree_.threshold[0] += 1
        with pytest.raises(ValueError):
            changed.validate()


def test_unsupported_observed_context_and_backdated_inference_rejected(model, split):
    snapshot = split.test[0].snapshot
    for invalid in (
        replace(snapshot, source_type="odoo_json2", source_reference="read-only-history"),
        replace(snapshot, context=replace(snapshot.context, company_id="another-company")),
        split.train[0].snapshot,
    ):
        with pytest.raises(ValueError, match="context|cutoff"):
            model.infer(invalid, QuantityValidity(1, 100, "controlled-proxy-v1"))


def test_metrics_are_reproducible_and_explain_undefined_classes(model, split):
    report = evaluate(model, split)
    assert report == evaluate(model, split)
    assert sum(sum(row) for row in report["metrics"]["confusion_matrix_labels_0_1"]) == 80
    absent = classification_metrics([0, 0], [0, 0])
    assert absent["per_class"][1]["recall"] is None
    assert absent["per_class"][1]["precision"] is None
    assert absent["per_class"][1]["f1"] is None
    assert absent["macro"]["f1"] is None
    assert len(absent["undefined_metrics"]) == 3
    no_predicted = classification_metrics([0, 1], [0, 0])
    assert no_predicted["per_class"][1]["recall"] == 0
    assert no_predicted["per_class"][1]["f1"] == 0
    assert no_predicted["per_class"][1]["precision"] is None


def test_evaluation_rejects_different_training_set(model, split):
    changed = replace(split, train=tuple(replace(e, label=1 - e.label) for e in split.train))
    with pytest.raises(ValueError, match="training data"):
        evaluate(model, changed)
