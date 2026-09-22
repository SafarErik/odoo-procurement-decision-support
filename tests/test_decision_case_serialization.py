"""Versioned snapshot serialization tests for T11."""

from copy import deepcopy
from datetime import timedelta, timezone

import pytest

from application.decision_case_serialization import (
    deserialize_canonical_input,
    deserialize_evaluation,
    deserialize_provenance,
    deserialize_scoring_policy,
    serialize_canonical_input,
    serialize_evaluation,
    serialize_provenance,
    serialize_scoring_policy,
)
from application.decision_cases import DecisionCaseError
from tests.t11_helpers import NOW, variant


@pytest.mark.parametrize("name", ["legacy", "historical_active", "historical_fallback"])
def test_supported_snapshot_variants_round_trip_without_recalculation(name: str) -> None:
    assembled, policy, evaluation = variant(name)

    assert deserialize_canonical_input(serialize_canonical_input(assembled.canonical)) == (
        assembled.canonical
    )
    assert deserialize_scoring_policy(serialize_scoring_policy(policy)) == policy
    assert deserialize_evaluation(serialize_evaluation(evaluation)) == evaluation
    assert (
        deserialize_provenance(serialize_provenance(assembled.provenance)) == assembled.provenance
    )


def test_decimal_strings_and_contribution_order_are_preserved_exactly() -> None:
    assembled, _, evaluation = variant("historical_active")
    canonical = serialize_canonical_input(assembled.canonical)
    result = serialize_evaluation(evaluation)

    assert canonical["requirement"]["requested_quantity"] == "10.000"
    assert canonical["offers"][0]["unit_price"] == "10.1200"
    contributions = result["decision_result"]["ranked_offers"][0]["contributions"]
    assert [item["criterion"] for item in contributions] == [
        "unit_price",
        "lead_time_days",
        "delivery_schedule_adherence",
    ]
    assert serialize_evaluation(deserialize_evaluation(result)) == result


def test_timestamps_serialize_as_explicit_utc_and_non_utc_is_rejected() -> None:
    assembled, _, _ = variant("legacy")
    payload = serialize_provenance(assembled.provenance)
    assert payload["entries"][0]["observed_at"] == "2026-09-22T08:30:45.123456Z"

    invalid = deepcopy(payload)
    invalid["entries"][0]["observed_at"] = NOW.astimezone(timezone(timedelta(hours=2))).isoformat()
    with pytest.raises(DecisionCaseError, match="provenance snapshot is malformed"):
        deserialize_provenance(invalid)


def test_provenance_is_logically_separate_from_canonical_and_evaluation_snapshots() -> None:
    assembled, _, evaluation = variant("historical_active")
    canonical = serialize_canonical_input(assembled.canonical)
    result = serialize_evaluation(evaluation)
    provenance = serialize_provenance(assembled.provenance)

    assert "provenance" not in canonical
    assert "provenance" not in result
    assert provenance["entries"][0]["source_reference"] == "RFQ-A#line-1"


@pytest.mark.parametrize(
    "serializer,deserializer,value_getter",
    [
        (serialize_canonical_input, deserialize_canonical_input, lambda data: data[0].canonical),
        (serialize_scoring_policy, deserialize_scoring_policy, lambda data: data[1]),
        (serialize_evaluation, deserialize_evaluation, lambda data: data[2]),
        (serialize_provenance, deserialize_provenance, lambda data: data[0].provenance),
    ],
)
def test_unknown_snapshot_version_fails_clearly(serializer, deserializer, value_getter) -> None:
    data = variant("legacy")
    payload = serializer(value_getter(data))
    payload["snapshot_version"] = 999

    with pytest.raises(DecisionCaseError) as captured:
        deserializer(payload)

    assert captured.value.code == "unsupported_snapshot_version"
