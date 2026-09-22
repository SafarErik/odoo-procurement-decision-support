"""Application contracts and use cases for auditable decision-case persistence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol, Self
from uuid import UUID

from application.decision_input_assembly import AssembledDecisionInput, ProvenanceManifest
from decision_core import DecisionResult, HistoricalScoringProfile, HistoricalScoringResult
from decision_core.models import StrategicProfile

SNAPSHOT_VERSION = 1


class DecisionCaseError(ValueError):
    """Stable application error that does not expose database exceptions."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class RepositoryError(RuntimeError):
    """Stable failure contract implemented by persistence adapters."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class DecisionCaseState(StrEnum):
    """Lifecycle states for a persisted decision case."""

    EVALUATED = "evaluated"
    FINALIZED = "finalized"


class HumanDecisionOutcome(StrEnum):
    """Explicit buyer outcomes supported by T11."""

    ACCEPT_RECOMMENDATION = "accept_recommendation"
    OVERRIDE_RECOMMENDATION = "override_recommendation"
    NO_AWARD = "no_award"


ScoringPolicy = StrategicProfile | HistoricalScoringProfile
EvaluationSnapshot = DecisionResult | HistoricalScoringResult


@dataclass(frozen=True, slots=True)
class HumanDecisionCommand:
    """Caller-supplied command for the single allowed case transition."""

    outcome: HumanDecisionOutcome
    selected_offer_id: str | None
    rationale: str | None
    decided_at: datetime
    actor_reference: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, HumanDecisionOutcome):
            _fail("invalid_human_decision", "The human-decision outcome is unsupported.")
        if self.selected_offer_id is not None:
            _identifier(self.selected_offer_id, "selected offer")
        if self.rationale is not None and not isinstance(self.rationale, str):
            _fail("invalid_human_decision", "The rationale must be text when supplied.")
        _utc_time(self.decided_at, "decided_at")
        _identifier(self.actor_reference, "actor reference")
        if len(self.actor_reference) > 255:
            _fail("invalid_actor_reference", "The actor reference must not exceed 255 characters.")
        _uuid(self.idempotency_key, "idempotency key")


@dataclass(frozen=True, slots=True)
class HumanDecision:
    """Immutable recorded form of a validated human decision."""

    outcome: HumanDecisionOutcome
    selected_offer_id: str | None
    rationale: str | None
    decided_at: datetime
    actor_reference: str
    idempotency_key: str

    def __post_init__(self) -> None:
        HumanDecisionCommand(
            outcome=self.outcome,
            selected_offer_id=self.selected_offer_id,
            rationale=self.rationale,
            decided_at=self.decided_at,
            actor_reference=self.actor_reference,
            idempotency_key=self.idempotency_key,
        )

    @classmethod
    def from_command(cls, command: HumanDecisionCommand) -> HumanDecision:
        return cls(
            outcome=command.outcome,
            selected_offer_id=command.selected_offer_id,
            rationale=command.rationale,
            decided_at=command.decided_at,
            actor_reference=command.actor_reference,
            idempotency_key=command.idempotency_key,
        )

    def matches(self, command: HumanDecisionCommand) -> bool:
        """Return whether a retry carries the exact previously accepted payload."""

        return self == HumanDecision.from_command(command)


@dataclass(frozen=True, slots=True)
class DecisionCase:
    """Immutable evaluation snapshots plus an optional one-time human decision."""

    decision_case_id: str
    snapshot_version: int
    created_at: datetime
    assembled_input: AssembledDecisionInput
    scoring_policy: ScoringPolicy
    evaluation: EvaluationSnapshot
    state: DecisionCaseState = DecisionCaseState.EVALUATED
    human_decision: HumanDecision | None = None

    def __post_init__(self) -> None:
        _uuid(self.decision_case_id, "decision case ID")
        if self.snapshot_version != SNAPSHOT_VERSION:
            _fail(
                "unsupported_snapshot_version",
                f"Unsupported decision-case snapshot version: {self.snapshot_version!r}.",
            )
        _utc_time(self.created_at, "created_at")
        if not isinstance(self.assembled_input, AssembledDecisionInput):
            _fail("invalid_decision_case", "The assembled decision input must be typed.")
        if not isinstance(self.assembled_input.provenance, ProvenanceManifest):
            _fail("invalid_decision_case", "The provenance manifest must remain separate.")
        if not isinstance(self.scoring_policy, (StrategicProfile, HistoricalScoringProfile)):
            _fail("invalid_decision_case", "The scoring policy is unsupported.")
        if not isinstance(self.evaluation, (DecisionResult, HistoricalScoringResult)):
            _fail("invalid_decision_case", "The evaluation result is unsupported.")
        if not isinstance(self.state, DecisionCaseState):
            _fail("invalid_decision_case", "The decision-case state is unsupported.")
        if self.state is DecisionCaseState.EVALUATED and self.human_decision is not None:
            _fail("invalid_decision_case", "An evaluated case cannot contain a final decision.")
        if self.state is DecisionCaseState.FINALIZED and not isinstance(
            self.human_decision, HumanDecision
        ):
            _fail("invalid_decision_case", "A finalized case requires a human decision.")

    @property
    def decision_result(self) -> DecisionResult:
        if isinstance(self.evaluation, HistoricalScoringResult):
            return self.evaluation.decision_result
        return self.evaluation

    @property
    def recommended_offer_id(self) -> str | None:
        recommended = self.decision_result.recommended_offer
        return recommended.offer.offer_id if recommended is not None else None


class DecisionCaseRepository(Protocol):
    """Narrow persistence port used only inside an explicit unit of work."""

    def add(self, decision_case: DecisionCase) -> None: ...

    def get(self, decision_case_id: str, *, for_update: bool = False) -> DecisionCase | None: ...

    def finalize(self, decision_case: DecisionCase) -> None: ...


class UnitOfWork(Protocol):
    """Transaction boundary supplied by a persistence adapter."""

    cases: DecisionCaseRepository

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


def store_evaluated_decision_case(
    unit_of_work: UnitOfWork,
    *,
    decision_case_id: str,
    created_at: datetime,
    assembled_input: AssembledDecisionInput,
    scoring_policy: ScoringPolicy,
    evaluation: EvaluationSnapshot,
) -> DecisionCase:
    """Atomically store a new immutable evaluated decision case."""

    decision_case = DecisionCase(
        decision_case_id=decision_case_id,
        snapshot_version=SNAPSHOT_VERSION,
        created_at=created_at,
        assembled_input=assembled_input,
        scoring_policy=scoring_policy,
        evaluation=evaluation,
    )
    _validate_evaluation_consistency(decision_case)
    try:
        with unit_of_work:
            unit_of_work.cases.add(decision_case)
            unit_of_work.commit()
    except RepositoryError as error:
        if error.code == "duplicate_decision_case_id":
            raise DecisionCaseError(error.code, "The decision case already exists.") from error
        raise DecisionCaseError(
            "decision_case_persistence_failed", "The decision case could not be stored."
        ) from error
    return decision_case


def get_decision_case(unit_of_work: UnitOfWork, decision_case_id: str) -> DecisionCase:
    """Retrieve the recorded snapshots without recalculating the evaluation."""

    _uuid(decision_case_id, "decision case ID")
    try:
        with unit_of_work:
            decision_case = unit_of_work.cases.get(decision_case_id)
    except RepositoryError as error:
        raise DecisionCaseError(
            "decision_case_persistence_failed", "The decision case could not be retrieved."
        ) from error
    if decision_case is None:
        _fail("decision_case_not_found", "The decision case does not exist.")
    return decision_case


def record_human_decision(
    unit_of_work: UnitOfWork,
    decision_case_id: str,
    command: HumanDecisionCommand,
) -> DecisionCase:
    """Validate and atomically persist the only permitted lifecycle transition."""

    _uuid(decision_case_id, "decision case ID")
    if not isinstance(command, HumanDecisionCommand):
        _fail("invalid_human_decision", "The final-decision command must be typed.")
    try:
        with unit_of_work:
            decision_case = unit_of_work.cases.get(decision_case_id, for_update=True)
            if decision_case is None:
                _fail("decision_case_not_found", "The decision case does not exist.")
            if decision_case.state is DecisionCaseState.FINALIZED:
                recorded = decision_case.human_decision
                if recorded is not None and recorded.idempotency_key == command.idempotency_key:
                    if recorded.matches(command):
                        return decision_case
                    _fail(
                        "idempotency_key_conflict",
                        "The idempotency key was already used with a different payload.",
                    )
                _fail("decision_case_already_finalized", "The decision case is already finalized.")

            _validate_human_decision(decision_case, command)
            finalized = replace(
                decision_case,
                state=DecisionCaseState.FINALIZED,
                human_decision=HumanDecision.from_command(command),
            )
            unit_of_work.cases.finalize(finalized)
            unit_of_work.commit()
            return finalized
    except DecisionCaseError:
        raise
    except RepositoryError as error:
        if error.code == "idempotency_key_conflict":
            raise DecisionCaseError(
                error.code, "The idempotency key is already assigned to another decision."
            ) from error
        if error.code == "decision_case_already_finalized":
            raise DecisionCaseError(
                error.code, "The decision case is already finalized."
            ) from error
        raise DecisionCaseError(
            "decision_case_persistence_failed", "The human decision could not be recorded."
        ) from error


def _validate_evaluation_consistency(decision_case: DecisionCase) -> None:
    canonical = decision_case.assembled_input.canonical
    result = decision_case.decision_result
    if result.requirement != canonical.requirement:
        _fail("inconsistent_decision_snapshot", "The result requirement differs from the input.")
    result_offers = tuple(
        sorted(
            (
                *(item.offer for item in result.ranked_offers),
                *(item.offer for item in result.excluded_offers),
            ),
            key=lambda item: item.offer_id,
        )
    )
    if result_offers != tuple(sorted(canonical.offers, key=lambda item: item.offer_id)):
        _fail("inconsistent_decision_snapshot", "The result offers differ from the input.")

    if isinstance(decision_case.evaluation, HistoricalScoringResult):
        if not isinstance(decision_case.scoring_policy, HistoricalScoringProfile):
            _fail(
                "inconsistent_decision_snapshot",
                "A historical evaluation requires its selected historical policy.",
            )
        if decision_case.scoring_policy.fallback_profile != canonical.profile:
            _fail(
                "inconsistent_decision_snapshot",
                "The historical policy fallback differs from the canonical profile.",
            )
        expected_result_profile: ScoringPolicy = (
            decision_case.scoring_policy
            if decision_case.evaluation.historical_criterion_active
            else decision_case.scoring_policy.fallback_profile
        )
        if result.profile != expected_result_profile:
            _fail(
                "inconsistent_decision_snapshot",
                "The recorded result profile does not match historical activation.",
            )
    elif decision_case.scoring_policy != canonical.profile or result.profile != canonical.profile:
        _fail(
            "inconsistent_decision_snapshot",
            "The legacy scoring policy differs from the canonical input or result.",
        )


def _validate_human_decision(decision_case: DecisionCase, command: HumanDecisionCommand) -> None:
    eligible_ids = {item.offer.offer_id for item in decision_case.decision_result.ranked_offers}
    recommended_id = decision_case.recommended_offer_id
    selected_id = command.selected_offer_id
    rationale_present = command.rationale is not None and bool(command.rationale.strip())

    if selected_id is not None and selected_id not in eligible_ids:
        _fail(
            "selected_offer_not_eligible",
            "The selected offer is unknown or excluded from the stored evaluation.",
        )
    if command.outcome is HumanDecisionOutcome.ACCEPT_RECOMMENDATION:
        if recommended_id is None:
            _fail("recommendation_unavailable", "A missing recommendation cannot be accepted.")
        if selected_id != recommended_id:
            _fail(
                "invalid_recommendation_acceptance",
                "Acceptance must select the stored recommended offer.",
            )
    elif command.outcome is HumanDecisionOutcome.OVERRIDE_RECOMMENDATION:
        if recommended_id is None:
            _fail("recommendation_unavailable", "A missing recommendation cannot be overridden.")
        if selected_id is None:
            _fail("selected_offer_required", "An override requires an eligible selected offer.")
        if selected_id == recommended_id:
            _fail(
                "invalid_recommendation_override",
                "An override must differ from the stored recommended offer.",
            )
        if not rationale_present:
            _fail("rationale_required", "An override requires a non-empty rationale.")
    elif command.outcome is HumanDecisionOutcome.NO_AWARD:
        if selected_id is not None:
            _fail("invalid_no_award", "A no-award decision cannot select an offer.")
        if not rationale_present:
            _fail("rationale_required", "A no-award decision requires a non-empty rationale.")


def _identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        _fail("invalid_identifier", f"The {label} must be a non-empty string.")


def _uuid(value: str, label: str) -> None:
    _identifier(value, label)
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError, TypeError) as error:
        raise DecisionCaseError("invalid_identifier", f"The {label} must be a UUID.") from error
    if str(parsed) != value.lower():
        _fail("invalid_identifier", f"The {label} must use canonical UUID text.")


def _utc_time(value: datetime, label: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        _fail("invalid_timestamp", f"The {label} must be an explicit UTC datetime.")


def _fail(code: str, message: str) -> None:
    raise DecisionCaseError(code, message)
