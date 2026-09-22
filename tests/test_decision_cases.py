"""Application-level T11 persistence and final-decision rules."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from application.decision_cases import (
    DecisionCase,
    DecisionCaseError,
    DecisionCaseState,
    HumanDecisionCommand,
    HumanDecisionOutcome,
    RepositoryError,
    get_decision_case,
    record_human_decision,
    store_evaluated_decision_case,
)
from tests.t11_helpers import CASE_ID, NOW, variant


class MemoryRepository:
    def __init__(self) -> None:
        self.records: dict[str, DecisionCase] = {}
        self.fail_code: str | None = None

    def add(self, decision_case: DecisionCase) -> None:
        if self.fail_code:
            raise RepositoryError(self.fail_code, "simulated")
        if decision_case.decision_case_id in self.records:
            raise RepositoryError("duplicate_decision_case_id", "duplicate")
        self.records[decision_case.decision_case_id] = decision_case

    def get(self, decision_case_id: str, *, for_update: bool = False) -> DecisionCase | None:
        del for_update
        if self.fail_code:
            raise RepositoryError(self.fail_code, "simulated")
        return self.records.get(decision_case_id)

    def finalize(self, decision_case: DecisionCase) -> None:
        if self.fail_code:
            raise RepositoryError(self.fail_code, "simulated")
        self.records[decision_case.decision_case_id] = decision_case


class MemoryUnitOfWork:
    def __init__(self, repository: MemoryRepository | None = None) -> None:
        self.cases = repository or MemoryRepository()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


def stored_case(name: str = "legacy") -> tuple[MemoryUnitOfWork, DecisionCase]:
    assembled, policy, evaluation = variant(name)
    unit_of_work = MemoryUnitOfWork()
    decision_case = store_evaluated_decision_case(
        unit_of_work,
        decision_case_id=CASE_ID,
        created_at=NOW,
        assembled_input=assembled,
        scoring_policy=policy,
        evaluation=evaluation,
    )
    return unit_of_work, decision_case


def command(
    outcome: HumanDecisionOutcome,
    selected_offer_id: str | None,
    rationale: str | None = None,
    *,
    key: str | None = None,
) -> HumanDecisionCommand:
    return HumanDecisionCommand(
        outcome=outcome,
        selected_offer_id=selected_offer_id,
        rationale=rationale,
        decided_at=NOW,
        actor_reference="buyer-reference-7",
        idempotency_key=key or str(uuid4()),
    )


def test_duplicate_case_id_and_missing_case_have_stable_errors() -> None:
    unit_of_work, decision_case = stored_case()
    with pytest.raises(DecisionCaseError) as duplicate:
        store_evaluated_decision_case(
            unit_of_work,
            decision_case_id=CASE_ID,
            created_at=NOW,
            assembled_input=decision_case.assembled_input,
            scoring_policy=decision_case.scoring_policy,
            evaluation=decision_case.evaluation,
        )
    assert duplicate.value.code == "duplicate_decision_case_id"

    with pytest.raises(DecisionCaseError) as missing:
        get_decision_case(unit_of_work, "22222222-2222-4222-8222-222222222222")
    assert missing.value.code == "decision_case_not_found"


def test_accept_recommendation_records_explicit_outcome() -> None:
    unit_of_work, _ = stored_case()
    result = record_human_decision(
        unit_of_work,
        CASE_ID,
        command(HumanDecisionOutcome.ACCEPT_RECOMMENDATION, "offer-A"),
    )

    assert result.state is DecisionCaseState.FINALIZED
    assert result.human_decision is not None
    assert result.human_decision.outcome is HumanDecisionOutcome.ACCEPT_RECOMMENDATION
    assert result.human_decision.selected_offer_id == result.recommended_offer_id


def test_override_requires_eligible_nonrecommended_offer_and_rationale() -> None:
    unit_of_work, _ = stored_case()
    result = record_human_decision(
        unit_of_work,
        CASE_ID,
        command(
            HumanDecisionOutcome.OVERRIDE_RECOMMENDATION,
            "offer-B",
            "The buyer has a documented operational constraint.",
        ),
    )
    assert result.human_decision is not None
    assert result.human_decision.outcome is HumanDecisionOutcome.OVERRIDE_RECOMMENDATION

    for selected, rationale, code in (
        ("offer-B", None, "rationale_required"),
        ("offer-A", "Reason", "invalid_recommendation_override"),
        (None, "Reason", "selected_offer_required"),
        ("unknown", "Reason", "selected_offer_not_eligible"),
    ):
        fresh, _ = stored_case()
        with pytest.raises(DecisionCaseError) as captured:
            record_human_decision(
                fresh,
                CASE_ID,
                command(HumanDecisionOutcome.OVERRIDE_RECOMMENDATION, selected, rationale),
            )
        assert captured.value.code == code


@pytest.mark.parametrize("case_name", ["legacy", "all_excluded"])
def test_no_award_works_with_or_without_recommendation(case_name: str) -> None:
    unit_of_work, _ = stored_case(case_name)
    result = record_human_decision(
        unit_of_work,
        CASE_ID,
        command(HumanDecisionOutcome.NO_AWARD, None, "No supplier will be awarded."),
    )
    assert result.human_decision is not None
    assert result.human_decision.selected_offer_id is None


def test_no_award_rejects_selected_offer_or_empty_rationale() -> None:
    for selected, rationale, code in (
        ("offer-A", "Reason", "invalid_no_award"),
        (None, "  ", "rationale_required"),
    ):
        unit_of_work, _ = stored_case()
        with pytest.raises(DecisionCaseError) as captured:
            record_human_decision(
                unit_of_work,
                CASE_ID,
                command(HumanDecisionOutcome.NO_AWARD, selected, rationale),
            )
        assert captured.value.code == code


def test_accept_rejects_different_offer_and_missing_recommendation() -> None:
    unit_of_work, _ = stored_case()
    with pytest.raises(DecisionCaseError) as different:
        record_human_decision(
            unit_of_work,
            CASE_ID,
            command(HumanDecisionOutcome.ACCEPT_RECOMMENDATION, "offer-B"),
        )
    assert different.value.code == "invalid_recommendation_acceptance"

    all_excluded, _ = stored_case("all_excluded")
    with pytest.raises(DecisionCaseError) as unavailable:
        record_human_decision(
            all_excluded,
            CASE_ID,
            command(HumanDecisionOutcome.ACCEPT_RECOMMENDATION, None),
        )
    assert unavailable.value.code == "recommendation_unavailable"


def test_excluded_offer_cannot_be_selected() -> None:
    all_excluded, _ = stored_case("all_excluded")
    with pytest.raises(DecisionCaseError) as captured:
        record_human_decision(
            all_excluded,
            CASE_ID,
            command(
                HumanDecisionOutcome.OVERRIDE_RECOMMENDATION,
                "offer-A",
                "Attempting an excluded offer.",
            ),
        )
    assert captured.value.code == "selected_offer_not_eligible"


def test_finalization_is_immutable_and_identical_retry_is_idempotent() -> None:
    unit_of_work, _ = stored_case()
    idempotency_key = str(uuid4())
    original = command(
        HumanDecisionOutcome.ACCEPT_RECOMMENDATION,
        "offer-A",
        key=idempotency_key,
    )
    finalized = record_human_decision(unit_of_work, CASE_ID, original)
    commits_after_first = unit_of_work.commits

    assert record_human_decision(unit_of_work, CASE_ID, original) == finalized
    assert unit_of_work.commits == commits_after_first

    with pytest.raises(DecisionCaseError) as conflict:
        record_human_decision(
            unit_of_work,
            CASE_ID,
            replace(original, rationale="different payload"),
        )
    assert conflict.value.code == "idempotency_key_conflict"

    with pytest.raises(DecisionCaseError) as immutable:
        record_human_decision(
            unit_of_work,
            CASE_ID,
            command(HumanDecisionOutcome.NO_AWARD, None, "Changed decision."),
        )
    assert immutable.value.code == "decision_case_already_finalized"


def test_malformed_actor_timestamp_and_identifiers_fail_closed() -> None:
    with pytest.raises(DecisionCaseError):
        command(HumanDecisionOutcome.NO_AWARD, None, "Reason", key="not-a-uuid")
    with pytest.raises(DecisionCaseError):
        HumanDecisionCommand(
            outcome=HumanDecisionOutcome.NO_AWARD,
            selected_offer_id=None,
            rationale="Reason",
            decided_at=NOW.replace(tzinfo=None),
            actor_reference="buyer",
            idempotency_key=str(uuid4()),
        )
    with pytest.raises(DecisionCaseError):
        HumanDecisionCommand(
            outcome=HumanDecisionOutcome.NO_AWARD,
            selected_offer_id=None,
            rationale="Reason",
            decided_at=NOW,
            actor_reference=" ",
            idempotency_key=str(uuid4()),
        )


def test_repository_failures_are_translated_at_application_boundary() -> None:
    repository = MemoryRepository()
    repository.fail_code = "repository_failure"
    unit_of_work = MemoryUnitOfWork(repository)
    assembled, policy, evaluation = variant("legacy")

    with pytest.raises(DecisionCaseError) as captured:
        store_evaluated_decision_case(
            unit_of_work,
            decision_case_id=CASE_ID,
            created_at=NOW,
            assembled_input=assembled,
            scoring_policy=policy,
            evaluation=evaluation,
        )
    assert captured.value.code == "decision_case_persistence_failed"
    assert isinstance(captured.value.__cause__, RepositoryError)


def test_retrieval_returns_recorded_snapshot_without_recalculation() -> None:
    unit_of_work, stored = stored_case("historical_fallback")
    retrieved = get_decision_case(unit_of_work, CASE_ID)

    assert retrieved == stored
    assert retrieved.evaluation == stored.evaluation
