"""PostgreSQL implementation of the T11 decision-case persistence ports."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC
from typing import Self

from sqlalchemy import Engine, create_engine, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

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
from application.decision_cases import (
    DecisionCase,
    DecisionCaseState,
    HumanDecision,
    HumanDecisionOutcome,
    RepositoryError,
)
from application.decision_input_assembly import AssembledDecisionInput
from persistence.schema import DecisionCaseRecord

SessionFactory = Callable[[], Session]


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """Create an explicit engine/session factory without mutating the schema."""

    if not isinstance(database_url, str) or not database_url.strip():
        raise RepositoryError("invalid_database_configuration", "A database URL is required.")
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
    except SQLAlchemyError as error:
        raise RepositoryError(
            "invalid_database_configuration", "The database engine could not be configured."
        ) from error
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


class SqlAlchemyDecisionCaseRepository:
    """Repository bound to one caller-owned SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, decision_case: DecisionCase) -> None:
        decision = decision_case.human_decision
        record = DecisionCaseRecord(
            decision_case_id=decision_case.decision_case_id,
            snapshot_version=decision_case.snapshot_version,
            created_at=decision_case.created_at,
            state=decision_case.state.value,
            policy_name=decision_case.scoring_policy.name,
            recommended_offer_id=decision_case.recommended_offer_id,
            canonical_input_snapshot=serialize_canonical_input(
                decision_case.assembled_input.canonical
            ),
            scoring_policy_snapshot=serialize_scoring_policy(decision_case.scoring_policy),
            evaluation_result_snapshot=serialize_evaluation(decision_case.evaluation),
            provenance_snapshot=serialize_provenance(decision_case.assembled_input.provenance),
            human_outcome=decision.outcome.value if decision is not None else None,
            selected_offer_id=decision.selected_offer_id if decision is not None else None,
            rationale=decision.rationale if decision is not None else None,
            decided_at=decision.decided_at if decision is not None else None,
            actor_reference=decision.actor_reference if decision is not None else None,
            idempotency_key=decision.idempotency_key if decision is not None else None,
        )
        self._session.add(record)
        try:
            self._session.flush()
        except IntegrityError as error:
            raise _integrity_error(error) from error
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The decision case could not be stored."
            ) from error

    def get(self, decision_case_id: str, *, for_update: bool = False) -> DecisionCase | None:
        statement = select(DecisionCaseRecord).where(
            DecisionCaseRecord.decision_case_id == decision_case_id
        )
        if for_update:
            statement = statement.with_for_update()
        try:
            record = self._session.execute(statement).scalar_one_or_none()
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The decision case could not be retrieved."
            ) from error
        return _to_decision_case(record) if record is not None else None

    def finalize(self, decision_case: DecisionCase) -> None:
        decision = decision_case.human_decision
        if decision_case.state is not DecisionCaseState.FINALIZED or decision is None:
            raise RepositoryError(
                "invalid_repository_operation", "Only a finalized case may be persisted."
            )
        statement = (
            update(DecisionCaseRecord)
            .where(
                DecisionCaseRecord.decision_case_id == decision_case.decision_case_id,
                DecisionCaseRecord.state == DecisionCaseState.EVALUATED.value,
            )
            .values(
                state=decision_case.state.value,
                human_outcome=decision.outcome.value,
                selected_offer_id=decision.selected_offer_id,
                rationale=decision.rationale,
                decided_at=decision.decided_at,
                actor_reference=decision.actor_reference,
                idempotency_key=decision.idempotency_key,
            )
        )
        try:
            result = self._session.execute(statement)
            if result.rowcount != 1:
                raise RepositoryError(
                    "decision_case_already_finalized", "The case is no longer open."
                )
            self._session.flush()
        except RepositoryError:
            raise
        except IntegrityError as error:
            raise _integrity_error(error) from error
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The human decision could not be stored."
            ) from error


class SqlAlchemyUnitOfWork:
    """One SQLAlchemy session and transaction per application use-case call."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.cases: SqlAlchemyDecisionCaseRepository
        self._committed = False

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.cases = SqlAlchemyDecisionCaseRepository(self._session)
        self._committed = False
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._session is None:
            return
        if not self._committed:
            self._session.rollback()
        self._session.close()
        self._session = None

    def commit(self) -> None:
        if self._session is None:
            raise RepositoryError("invalid_repository_operation", "No transaction is active.")
        try:
            self._session.commit()
            self._committed = True
        except IntegrityError as error:
            self._session.rollback()
            raise _integrity_error(error) from error
        except SQLAlchemyError as error:
            self._session.rollback()
            raise RepositoryError(
                "repository_failure", "The database transaction could not be committed."
            ) from error


def _to_decision_case(record: DecisionCaseRecord) -> DecisionCase:
    decision = None
    if record.state == DecisionCaseState.FINALIZED.value:
        if (
            record.human_outcome is None
            or record.decided_at is None
            or record.actor_reference is None
            or record.idempotency_key is None
        ):
            raise RepositoryError("invalid_persisted_case", "Final decision fields are incomplete.")
        decision = HumanDecision(
            outcome=HumanDecisionOutcome(record.human_outcome),
            selected_offer_id=record.selected_offer_id,
            rationale=record.rationale,
            decided_at=record.decided_at.astimezone(UTC),
            actor_reference=record.actor_reference,
            idempotency_key=record.idempotency_key,
        )
    canonical = deserialize_canonical_input(record.canonical_input_snapshot)
    provenance = deserialize_provenance(record.provenance_snapshot)
    decision_case = DecisionCase(
        decision_case_id=record.decision_case_id,
        snapshot_version=record.snapshot_version,
        created_at=record.created_at.astimezone(UTC),
        assembled_input=AssembledDecisionInput(canonical=canonical, provenance=provenance),
        scoring_policy=deserialize_scoring_policy(record.scoring_policy_snapshot),
        evaluation=deserialize_evaluation(record.evaluation_result_snapshot),
        state=DecisionCaseState(record.state),
        human_decision=decision,
    )
    if decision_case.scoring_policy.name != record.policy_name:
        raise RepositoryError("invalid_persisted_case", "The policy identity is inconsistent.")
    if decision_case.recommended_offer_id != record.recommended_offer_id:
        raise RepositoryError(
            "invalid_persisted_case", "The recommended-offer identity is inconsistent."
        )
    return decision_case


def _integrity_error(error: IntegrityError) -> RepositoryError:
    constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    if constraint_name == "pk_decision_cases":
        return RepositoryError("duplicate_decision_case_id", "The decision-case ID is duplicate.")
    if constraint_name == "uq_decision_cases_idempotency_key":
        return RepositoryError("idempotency_key_conflict", "The idempotency key is already in use.")
    return RepositoryError("repository_constraint_violation", "A database constraint was violated.")
