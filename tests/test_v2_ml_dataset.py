"""Leakage gates run without either optional ML or MILP dependency."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tools.v2_ml_risk.dataset import (
    FEATURES,
    Observation,
    Outcome,
    Receipt,
    build_dataset,
    feature_values,
    feature_vector,
    outcome,
    synthetic_dataset,
    synthetic_rows,
)

START = datetime(2025, 1, 1, tzinfo=UTC)


def observation(identity="line", decision=START):
    return Observation(
        identity,
        "supplier",
        "product",
        decision,
        decision + timedelta(days=10),
        100,
        (Receipt(decision + timedelta(days=8), 40), Receipt(decision + timedelta(days=12), 60)),
        decision + timedelta(days=13),
    )


def test_partial_receipt_does_not_mark_line_complete_or_on_time():
    row = observation()
    result, reason = outcome(row, START + timedelta(days=20))
    assert reason is None
    assert result.completed_at == START + timedelta(days=12)
    assert result.schedule_miss == 1
    partial, reason = outcome(replace(row, receipts=row.receipts[:1]), START + timedelta(days=20))
    assert partial is None and reason == "incomplete_receipt"


def test_exact_expected_arrival_is_on_time_and_late_recording_is_censored():
    row = observation()
    row = replace(row, receipts=(Receipt(row.expected_arrival_at_decision, 100),))
    result, _ = outcome(row, START + timedelta(days=20))
    assert result.schedule_miss == 0
    assert result.available_at == row.outcome_recorded_at
    assert outcome(row, START + timedelta(days=12))[1] == "outcome_not_available"


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"cancelled": True}, "cancelled"),
        ({"return_affected": True}, "return_affected"),
        ({"quantity_changed": True}, "quantity_changed"),
        ({"expected_arrival_at_decision": None}, "missing_expected_arrival"),
        ({"reference_snapshot_proven": False}, "unproven_decision_snapshot"),
        ({"receipts": (Receipt(START - timedelta(days=1), 100),)}, "ambiguous_timestamps"),
    ],
)
def test_unsupported_outcomes_are_excluded(changes, reason):
    assert outcome(replace(observation(), **changes), START + timedelta(days=20)) == (None, reason)


def test_prior_history_requires_completion_and_availability_strictly_before_decision():
    current = observation("current", START + timedelta(days=30))
    history = []
    for index in range(3):
        row = observation(f"prior-{index}")
        item, _ = outcome(row, START + timedelta(days=20))
        history.append(item)
    # Equal-boundary outcome, delayed-recorded outcome, future outcome, own row and other supplier.
    adversarial = (
        Outcome(observation("equal"), current.decision_at, current.decision_at, 0),
        replace(history[0], observation=observation("delayed"), available_at=current.decision_at),
        Outcome(
            observation("future"),
            current.decision_at + timedelta(days=1),
            current.decision_at + timedelta(days=2),
            0,
        ),
        replace(history[0], observation=replace(current, decision_at=START)),
        replace(history[0], observation=replace(observation("other"), supplier_id="other")),
        replace(history[0], observation=replace(observation("other-product"), product_id="other")),
    )
    clean = feature_values(current, tuple(history))
    assert clean[FEATURES[1]] == 3 and clean[FEATURES[0]] == 0
    assert feature_values(current, tuple(history) + adversarial) == clean
    with pytest.raises(ValueError, match="Insufficient"):
        feature_values(current, tuple(history[:2]) + adversarial)


@pytest.mark.parametrize(
    "field",
    [
        "schedule_miss",
        "completed_at",
        "actual_delay",
        "final_received_quantity",
        "outcome_recorded_at",
        "receipt_status",
        "supplier_id",
    ],
)
def test_outcome_and_identity_columns_cannot_enter_feature_vector(field):
    values = dict(zip(FEATURES, (0.5, 12, 100, 1), strict=True))
    with pytest.raises(ValueError, match="exact decision-time"):
        feature_vector({**values, field: 1})


def test_feature_order_is_stable_and_missing_nonfinite_data_is_rejected():
    values = dict(zip(reversed(FEATURES), (1, 100, 12, 0.5), strict=True))
    assert feature_vector(values) == (0.5, 12, 100, 1)
    with pytest.raises(ValueError):
        feature_vector({**values, FEATURES[0]: float("nan")})
    with pytest.raises(ValueError):
        feature_vector({k: v for k, v in values.items() if k != FEATURES[0]})


def test_chronological_split_purges_labels_and_freezes_test_history():
    data = synthetic_dataset()
    by_id = {item.observation.observation_id: item for item in data.outcomes}
    test_ids = {e.outcome.observation.observation_id for e in data.test}
    assert data.exclusions["purged_training_outcome_after_cutoff"] > 0
    for example in data.train:
        assert example.outcome.observation.decision_at < data.cutoff
        assert example.outcome.available_at < data.cutoff
    for example in (*data.train, *data.test):
        assert not test_ids.intersection(example.history_ids)
        for identity in example.history_ids:
            assert by_id[identity].completed_at < example.outcome.observation.decision_at
            assert by_id[identity].available_at < example.outcome.observation.decision_at
    assert all(e.outcome.observation.decision_at >= data.cutoff for e in data.test)


def test_changing_test_outcomes_does_not_change_train_or_test_feature_values():
    data = synthetic_dataset()
    rows = tuple(
        replace(
            row,
            receipts=(Receipt(row.expected_arrival_at_decision, 10000),),
            outcome_recorded_at=row.expected_arrival_at_decision,
        )
        if row.decision_at >= data.cutoff
        else row
        for row in synthetic_rows()
    )
    changed = build_dataset(rows, data.cutoff, data.as_of)
    for name in ("train", "test"):
        before = {e.outcome.observation.observation_id: e.features for e in getattr(data, name)}
        after = {e.outcome.observation.observation_id: e.features for e in getattr(changed, name)}
        assert before == after
    assert any(e.outcome.schedule_miss == 1 for e in data.test)
    assert all(e.outcome.schedule_miss == 0 for e in changed.test)


def test_input_reordering_preserves_dataset_hash_and_examples():
    data = synthetic_dataset()
    reversed_data = build_dataset(tuple(reversed(synthetic_rows())), data.cutoff, data.as_of)
    assert reversed_data == data
    with pytest.raises(ValueError, match="unique"):
        build_dataset((observation(), observation()), data.cutoff, data.as_of)
