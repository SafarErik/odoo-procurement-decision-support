"""Synthetic model and explanation checks, optional dependency only."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

pytest.importorskip("sklearn")

from tools.v2_ml_risk.dataset import FEATURES, synthetic_dataset  # noqa: E402
from tools.v2_ml_risk.model import RiskModel, metrics  # noqa: E402


def test_repeated_training_and_predictions_are_identical():
    data = synthetic_dataset()
    first, second = RiskModel(data), RiskModel(data)
    assert first.model_version == second.model_version
    x = [e.features for e in data.test]
    assert (first.tree.predict_proba(x) == second.tree.predict_proba(x)).all()
    assert first.global_explanation()["depth"] <= 3
    assert all(leaf["count"] >= 12 for leaf in first.global_explanation()["leaf_support"])


def test_local_rules_leaf_counts_and_canonical_score_agree():
    data = synthetic_dataset()
    model = RiskModel(data)
    for example in data.test:
        row = example.outcome.observation
        result = model.assess(
            row.supplier_id, dict(zip(FEATURES, example.features, strict=True)), row.decision_at
        )
        explanation = result.explanation
        counts = explanation["leaf_class_counts_0_1"]
        assert sum(counts) == explanation["leaf_sample_count"]
        assert explanation["raw_positive_class_score"] == pytest.approx(counts[1] / sum(counts))
        assert abs(result.ml_risk_score - Decimal(counts[1]) / sum(counts)) <= Decimal("0.00005")
        assert result.predicted_class == (1 if counts[1] > counts[0] else 0)
        for rule in explanation["rules_traversed"]:
            assert (rule["value_float32"] <= rule["threshold"]) == (rule["operator"] == "<=")
        assert explanation["score_is_calibrated_probability"] is False


def test_single_class_evaluation_and_training_fail_closed():
    data = synthetic_dataset()
    with pytest.raises(ValueError, match="Both holdout classes"):
        metrics([0] * 20, [0] * 20)
    single_class = replace(data, train=tuple(e for e in data.train if e.outcome.schedule_miss == 0))
    with pytest.raises(ValueError, match="both classes"):
        RiskModel(single_class)
    with pytest.raises(ValueError, match="cannot precede"):
        RiskModel(data).assess(
            "supplier",
            dict(zip(FEATURES, data.test[0].features, strict=True)),
            data.cutoff - timedelta(seconds=1),
        )
