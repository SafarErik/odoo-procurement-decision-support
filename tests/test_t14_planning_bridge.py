"""Score direction/provenance and complete positive-allocation validity coverage."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from decision_core.planning.models import InvalidPlanningInput
from supplier_evaluation.contracts import QuantityValidity
from supplier_evaluation.dataset import BOUNDARY, EXTRACTED_AT, generate_dataset, prepare_dataset
from supplier_evaluation.model import train
from supplier_evaluation.planning_bridge import risk_inputs
from tests.t14_helpers import planning_fixture


@pytest.fixture(scope="module")
def fixture():
    split = prepare_dataset(generate_dataset(), boundary=BOUNDARY, extracted_at=EXTRACTED_AT)
    model = train(split)
    return planning_fixture(model, split)


def bridge(fixture, scores=None, **kwargs):
    request, assessments, company, cutoff = fixture
    return risk_inputs(
        kwargs.pop("request", request),
        assessments if scores is None else scores,
        company_id=kwargs.pop("company_id", company),
        as_of=kwargs.pop("as_of", cutoff),
    )


def test_valid_direction_range_and_provenance_are_preserved(fixture):
    coefficients, context = bridge(fixture)
    expected = {a.snapshot.context.supplier_id: a.score for a in fixture[1]}
    assert {c.supplier_id: c.value for c in coefficients} == expected
    assert all(0 <= c.value <= 1 for c in coefficients)
    assert all(
        c.valid_quantities.minimum == 1 and c.valid_quantities.maximum == 100 for c in coefficients
    )
    assert context.controlled_fixture is True
    assert "t14-leaf-exposure-v1" in context.definition_reference
    assert "t14-assessments:" in context.assessment_reference
    assert "quantity-independent" in context.validity_reference
    assert bridge(fixture, tuple(reversed(fixture[1]))) == (coefficients, context)


@pytest.mark.parametrize("scores", ((), (None,)))
def test_absent_or_invalid_scores_have_no_zero_fallback(fixture, scores):
    with pytest.raises(ValueError, match="no zero-risk fallback"):
        bridge(fixture, scores)


def test_missing_duplicate_and_foreign_supplier_join_rejected(fixture):
    scores = fixture[1]
    foreign = replace(
        scores[0],
        snapshot=replace(
            scores[0].snapshot, context=replace(scores[0].snapshot.context, supplier_id="foreign")
        ),
    )
    for invalid in (scores[:-1], (scores[0], scores[0], scores[2]), (foreign,) + scores[1:]):
        with pytest.raises(ValueError, match="join"):
            bridge(fixture, invalid)


@pytest.mark.parametrize(
    "value", (None, Decimal("NaN"), Decimal("Infinity"), Decimal("-0.1"), Decimal("1.1"))
)
def test_invalid_risk_coefficient_never_becomes_zero(fixture, value):
    with pytest.raises(ValueError, match="score"):
        replace(fixture[1][0], score=value)


def test_quantity_validity_covers_entire_business_range_without_narrowing(fixture):
    scores = fixture[1]
    for quantities in (
        QuantityValidity(1, 7, "too-small"),
        QuantityValidity(2, 100, "too-high-lower"),
    ):
        invalid = (replace(scores[0], quantities=quantities),) + scores[1:]
        with pytest.raises(InvalidPlanningInput, match="every feasible positive quantity"):
            bridge(fixture, invalid)
    assert fixture[0].risk_coefficients is None


def test_changed_quantity_within_validity_reuses_quantity_independent_score(fixture):
    request = replace(fixture[0], requirement=replace(fixture[0].requirement, approved_quantity=20))
    assert bridge(fixture, request=request)[0] == bridge(fixture)[0]


def test_stale_future_wrong_company_and_outside_outcome_window_rejected(fixture):
    cutoff = fixture[3]
    for kwargs in (
        {"as_of": cutoff - timedelta(seconds=1)},
        {"as_of": cutoff + timedelta(days=30)},
        {"company_id": "foreign"},
        {
            "request": replace(
                fixture[0],
                requirement=replace(
                    fixture[0].requirement, required_date=(cutoff + timedelta(days=31)).date()
                ),
            )
        },
    ):
        with pytest.raises(ValueError, match="validity"):
            bridge(fixture, **kwargs)


def test_mixed_model_mapping_and_source_provenance_rejected(fixture):
    scores = fixture[1]
    with pytest.raises(ValueError, match="Mixed"):
        bridge(fixture, (replace(scores[0], model_id="another-model"),) + scores[1:])
    for change in (
        {"mapping_version": "other"},
        {"dataset_version": "other"},
        {"label_version": "other"},
        {"snapshot": replace(scores[0].snapshot, source_type="odoo_json2")},
    ):
        with pytest.raises(ValueError, match="provenance"):
            replace(scores[0], **change)


def test_leaf_class_risk_direction_and_support_are_validated(fixture):
    a = fixture[1][0]
    with pytest.raises(ValueError, match="mapping"):
        replace(a, predicted_class=1 - a.predicted_class)
    with pytest.raises(ValueError, match="support"):
        replace(a, leaf_counts=(1, 1))
    high = replace(a, predicted_class=1, leaf_counts=(0, 10), score=Decimal(1))
    low = replace(a, predicted_class=0, leaf_counts=(10, 0), score=Decimal(0))
    assert high.score > low.score


def test_provenance_changes_affect_context_references(fixture):
    scores = fixture[1]
    changed = (
        replace(scores[0], quantities=QuantityValidity(1, 100, "different-authority")),
    ) + scores[1:]
    assert bridge(fixture, changed)[1].validity_reference != bridge(fixture)[1].validity_reference
