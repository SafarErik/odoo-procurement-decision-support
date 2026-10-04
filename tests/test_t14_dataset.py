"""Cutoff, target separation, group boundaries, source semantics and duplicate gates."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from application.historical_performance import (
    HistoricalMetric,
    HistoricalPerformanceAvailability,
    SourcedSupplierHistoricalPerformance,
    SupplierHistoricalPerformance,
)
from supplier_evaluation.contracts import FEATURES, feature_vector
from supplier_evaluation.dataset import (
    BOUNDARY,
    EXTRACTED_AT,
    future_label,
    generate_dataset,
    load_dataset,
    prepare_dataset,
    prepare_features,
    save_dataset,
)
from supplier_evaluation.history import from_sourced_history, prepare_history


@pytest.fixture(scope="module")
def rows():
    return generate_dataset()


def prepare(rows):
    return prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)


def test_deterministic_dataset_roundtrip_and_partition_separation(rows, tmp_path):
    assert rows == generate_dataset()
    split = prepare(rows)
    assert len(split.train) == 160 and len(split.test) == 80
    assert {e.snapshot.context.supplier_id for e in split.train}.isdisjoint(
        {e.snapshot.context.supplier_id for e in split.test}
    )
    assert max(e.label_available_at for e in split.train) < min(
        e.snapshot.cutoff for e in split.test
    )
    assert prepare(tuple(reversed(rows))) == split
    path = tmp_path / "dataset.json"
    save_dataset(path, rows)
    assert load_dataset(path) == split


def test_future_outcome_changes_never_change_training_or_test_features(rows):
    modified = tuple(
        replace(
            r,
            outcomes=tuple(
                replace(
                    line,
                    completed_at=line.expected_arrival + timedelta(hours=2),
                    available_at=line.expected_arrival + timedelta(hours=3),
                )
                for line in r.outcomes
            ),
        )
        for r in rows
    )
    assert [prepare_features(r) for r in rows] == [prepare_features(r) for r in modified]
    assert any(
        future_label(a, EXTRACTED_AT)[0] != future_label(b, EXTRACTED_AT)[0]
        for a, b in zip(rows, modified, strict=True)
    )


@pytest.mark.parametrize("field", ("completed_at", "available_at"))
def test_future_history_information_is_rejected(rows, field):
    row = rows[0]
    changes = {field: row.cutoff + timedelta(seconds=1)}
    if field == "completed_at":
        changes["available_at"] = row.cutoff + timedelta(seconds=2)
    line = replace(row.history[0], **changes)
    with pytest.raises(ValueError, match="cutoff"):
        prepare_features(replace(row, history=(line,) + row.history[1:]))


def test_exact_cutoff_completion_rejected_and_recording_at_cutoff_allowed(rows):
    row = rows[0]
    line = replace(row.history[0], completed_at=row.cutoff, available_at=row.cutoff)
    with pytest.raises(ValueError, match="cutoff"):
        prepare_features(replace(row, history=(line,) + row.history[1:]))
    line = replace(row.history[0], available_at=row.cutoff)
    assert prepare_features(replace(row, history=(line,) + row.history[1:])).values


@pytest.mark.parametrize("kind", ("id", "context", "history", "outcome", "group"))
def test_duplicate_and_cross_partition_group_leakage_rejected(rows, kind):
    items = list(rows)
    row = items[160]
    if kind == "id":
        items[160] = replace(row, observation_id=items[0].observation_id)
    elif kind == "context":
        items[161] = replace(row, observation_id="another-id")
    elif kind == "history":
        items[160] = replace(
            row,
            history=(replace(row.history[0], line_id=items[0].history[0].line_id),)
            + row.history[1:],
        )
    elif kind == "outcome":
        items[160] = replace(
            row,
            outcomes=(replace(row.outcomes[0], line_id=row.history[0].line_id),) + row.outcomes[1:],
        )
    else:
        context = replace(row.context, supplier_id=items[0].context.supplier_id)
        items[160] = replace(
            row,
            context=context,
            history=tuple(replace(line, context=context) for line in row.history),
            outcomes=tuple(replace(line, context=context) for line in row.outcomes),
        )
    with pytest.raises(ValueError, match="Duplicate|leakage"):
        prepare(tuple(items))


def test_context_mismatch_old_history_and_small_sample_rejected(rows):
    row = rows[0]
    with pytest.raises(ValueError, match="context"):
        prepare_features(replace(row, history=(rows[1].history[0],) + row.history[1:]))
    line = replace(row.history[0], completed_at=row.cutoff - timedelta(days=366))
    with pytest.raises(ValueError, match="cutoff"):
        prepare_features(replace(row, history=(line,) + row.history[1:]))
    with pytest.raises(ValueError, match="support"):
        prepare_features(replace(row, history=row.history[:2]))


def test_training_label_window_crossing_boundary_rejected(rows):
    with pytest.raises(ValueError, match="Temporal"):
        prepare_dataset(
            rows, boundary=rows[0].cutoff + timedelta(days=15), extracted_at=EXTRACTED_AT
        )


def test_incomplete_unavailable_future_and_wrong_context_labels_rejected(rows):
    row = rows[-1]
    for invalid in (
        replace(row, outcomes=row.outcomes[:4]),
        replace(
            row,
            outcomes=(replace(row.outcomes[0], available_at=EXTRACTED_AT + timedelta(days=1)),)
            + row.outcomes[1:],
        ),
        replace(row, outcomes=(rows[0].outcomes[0],) + row.outcomes[1:]),
    ):
        with pytest.raises(ValueError, match="outcomes"):
            future_label(invalid, EXTRACTED_AT)
    with pytest.raises(ValueError, match="observable"):
        future_label(row, row.cutoff + timedelta(days=25))


@pytest.mark.parametrize(
    "values",
    (
        (None, 10),
        (float("nan"), 10),
        (float("inf"), 10),
        (-1, 10),
        (101, 10),
        (50, 2),
        (50, 51),
        (50, 3.5),
        (True, 10),
    ),
)
def test_missing_invalid_features_fail_closed(values):
    with pytest.raises(ValueError):
        feature_vector(FEATURES, values)


@pytest.mark.parametrize("names", (tuple(reversed(FEATURES)), FEATURES + ("target",), ()))
def test_feature_order_extra_targets_and_missing_columns_rejected(names):
    with pytest.raises(ValueError, match="schema"):
        feature_vector(names, (50, 10))


def test_stale_future_naive_and_wrong_feature_version_rejected(rows):
    snapshot = prepare_features(rows[0])
    for change in (
        {"cutoff": snapshot.cutoff + timedelta(days=8)},
        {"evidence_available_at": snapshot.cutoff + timedelta(seconds=1)},
        {"cutoff": snapshot.cutoff.replace(tzinfo=None)},
        {"feature_version": "v999"},
    ):
        with pytest.raises(ValueError):
            replace(snapshot, **change)


def test_expected_arrival_equality_uses_existing_t8_policy_and_no_future_probability(rows):
    row = rows[0]
    history = tuple(
        replace(line, completed_at=line.expected_arrival, available_at=line.expected_arrival)
        for line in row.history
    )
    snapshot = prepare_features(replace(row, history=history))
    assert snapshot.values == (100.0, float(len(history)))
    assert snapshot.source_type == "t14_synthetic"
    assert snapshot.source_reference == row.source_reference


def test_sourced_t8_history_preserves_kpi_support_and_attribution_without_live_read(rows):
    snapshot = prepare_features(rows[0])
    performance = SupplierHistoricalPerformance(
        metric_id=HistoricalMetric.DELIVERY_SCHEDULE_ADHERENCE,
        value=Decimal(str(snapshot.values[0])),
        sample_size=int(snapshot.values[1]),
        observation_window_start=snapshot.history_start,
        observation_window_end=snapshot.history_end,
        observed_at=snapshot.cutoff,
        supplier_id=snapshot.context.supplier_id,
        availability=HistoricalPerformanceAvailability.USABLE,
        warnings=(),
    )
    sourced = SourcedSupplierHistoricalPerformance(
        performance, "odoo_json2", "bounded-test-reference"
    )
    converted = from_sourced_history(sourced, snapshot.context, snapshot.cutoff)
    assert converted.values == snapshot.values
    assert converted.source_type == "odoo_json2"
    assert converted.source_reference == "bounded-test-reference"
    # Synthetic unit receipts cannot masquerade as observed Odoo receipt evidence.
    with pytest.raises(ValueError, match="synthetic"):
        prepare_history(
            rows[0].context, rows[0].cutoff, rows[0].history, "odoo_json2", "unsupported-source"
        )
    with pytest.raises(ValueError, match="mismatched"):
        from_sourced_history(
            sourced, replace(snapshot.context, supplier_id="another"), snapshot.cutoff
        )
