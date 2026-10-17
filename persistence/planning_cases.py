"""PostgreSQL planning-case repositories and their per-use-case transaction."""

import json
from datetime import UTC

from sqlalchemy import func, select, text, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from application.errors import RepositoryError
from application.planning_cases import (
    DEMO_INPUT_KIND,
    SNAPSHOT_VERSION,
    PlanningCase,
    validate_snapshot,
)
from application.planning_serialization import snapshot_json
from persistence.planning_decisions import SqlAlchemyPlanningDecisionRepository, read_decision_row
from persistence.planning_documents import SqlAlchemyPlanningDocumentRepository
from persistence.schema import (
    PlanningCaseRecord,
    PlanningFinalDecisionRecord,
)


class SqlAlchemyPlanningRepository:
    def __init__(self, session):
        self._session = session

    def lock(self, key: str) -> None:
        try:
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "t15:" + key}
            )
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning key could not be locked."
            ) from error

    def _read(self, statement) -> PlanningCase | None:
        try:
            row = self._session.execute(statement).scalar_one_or_none()
            if row is None:
                return None
            return read_case_row(row)
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning case could not be read."
            ) from error

    def by_key(self, key: str) -> PlanningCase | None:
        return self._read(
            select(PlanningCaseRecord).where(PlanningCaseRecord.idempotency_key == key)
        )

    def get(self, case_id: str) -> PlanningCase | None:
        return self._read(select(PlanningCaseRecord).where(PlanningCaseRecord.case_id == case_id))

    def list_saved(self, query):
        try:
            rows = self._session.execute(library_statement(query)).all()
            return [
                (
                    read_case_row(case),
                    None if query.parent_id is not None else read_decision_row(decision),
                )
                for case, decision in rows
            ]
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The case library is unavailable."
            ) from error

    def add(self, case: PlanningCase) -> None:
        validate_snapshot(case)
        self._session.add(
            PlanningCaseRecord(
                case_id=case.case_id,
                parent_id=case.parent_id,
                created_at=case.created_at,
                idempotency_key=case.idempotency_key,
                fingerprint=case.fingerprint,
                snapshot_version=SNAPSHOT_VERSION,
                snapshot_hash=case.snapshot_hash,
                snapshot=json.loads(case.snapshot),
            )
        )
        try:
            self._session.flush()
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "The planning case could not be stored."
            ) from error


def read_case_row(row):
    case = PlanningCase(
        row.case_id,
        row.created_at.astimezone(UTC),
        row.parent_id,
        row.idempotency_key,
        row.fingerprint,
        snapshot_json(row.snapshot),
    )
    if row.snapshot_version != SNAPSHOT_VERSION or case.snapshot_hash != row.snapshot_hash:
        raise RepositoryError(
            "invalid_persisted_case", "The planning snapshot integrity check failed."
        )
    validate_snapshot(case)
    return case


def library_statement(query):
    case, decision = PlanningCaseRecord, PlanningFinalDecisionRecord
    original_id = func.coalesce(case.parent_id, case.case_id)
    statement = (
        select(case, decision)
        .outerjoin(decision, decision.case_id == original_id)
        .where(case.snapshot["facts"]["company_id"].astext == query.company)
        .where(
            case.parent_id.is_(None)
            if query.parent_id is None
            else case.parent_id == query.parent_id
        )
    )
    if query.origin != "all":
        input_kind = func.coalesce(case.snapshot["facts"]["input_kind"].astext, DEMO_INPUT_KIND)
        statement = statement.where(
            input_kind == DEMO_INPUT_KIND
            if query.origin == "demo"
            else input_kind != DEMO_INPUT_KIND
        )
    if query.status == "draft":
        statement = statement.where(decision.case_id.is_(None))
    elif query.status != "all":
        statement = statement.where(
            decision.record["audit"]["outcome"].astext
            == ("approve" if query.status == "approved" else "no_award")
        )
    if query.q:
        # Escape LIKE metacharacters: search is literal text, never SQL or a wildcard API.
        pattern = "%" + query.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        statement = statement.where(
            case.snapshot["request"]["requirement"]["product_id"].astext.ilike(pattern, escape="\\")
            | case.case_id.ilike(pattern, escape="\\")
        )
    if query.after is not None:
        statement = statement.where(tuple_(case.created_at, case.case_id) < query.after)
    return statement.order_by(case.created_at.desc(), case.case_id.desc()).limit(query.limit + 1)


class SqlAlchemyPlanningUnitOfWork:
    """One SQLAlchemy session and transaction per application use-case call."""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._session = None
        self._committed = False

    def __enter__(self):
        self._session = self._session_factory()
        self.cases = SqlAlchemyPlanningRepository(self._session)
        self.decisions = SqlAlchemyPlanningDecisionRepository(self._session)
        self.documents = SqlAlchemyPlanningDocumentRepository(self._session)
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._session is None:
            return
        if not self._committed:
            self._session.rollback()
        self._session.close()
        self._session = None

    def commit(self):
        if self._session is None:
            raise RepositoryError("invalid_repository_operation", "No transaction is active.")
        try:
            self._session.commit()
            self._committed = True
        except IntegrityError as error:
            self._session.rollback()
            raise RepositoryError(
                "repository_constraint_violation", "A database constraint was violated."
            ) from error
        except SQLAlchemyError as error:
            self._session.rollback()
            raise RepositoryError(
                "repository_failure", "The database transaction could not be committed."
            ) from error
