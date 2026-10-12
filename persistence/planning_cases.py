"""T15 uses the existing PostgreSQL session/transaction and advisory-lock patterns."""

import json
from datetime import UTC

from sqlalchemy import func, select, text, tuple_
from sqlalchemy.exc import SQLAlchemyError

from application.decision_cases import RepositoryError
from application.planning_cases import SNAPSHOT_VERSION, PlanningCase, validate_snapshot
from application.planning_serialization import snapshot_json
from persistence.planning_decisions import SqlAlchemyPlanningDecisionRepository, read_decision_row
from persistence.planning_documents import SqlAlchemyPlanningDocumentRepository
from persistence.postgres import SqlAlchemyUnitOfWork
from persistence.schema import (
    PlanningCaseCatalogRecord,
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
                    workspace or "unclassified",
                    example,
                    None if query.parent_id is not None else read_decision_row(decision),
                )
                for case, workspace, example, decision in rows
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
    case, catalog, decision = (
        PlanningCaseRecord,
        PlanningCaseCatalogRecord,
        PlanningFinalDecisionRecord,
    )
    original_id = func.coalesce(case.parent_id, case.case_id)
    statement = (
        select(case, catalog.workspace, catalog.example_id, decision)
        .outerjoin(catalog, catalog.case_id == original_id)
        .outerjoin(decision, decision.case_id == original_id)
        .where(case.snapshot["facts"]["company_id"].astext == query.company)
        .where(
            case.parent_id.is_(None)
            if query.parent_id is None
            else case.parent_id == query.parent_id
        )
        .where(
            catalog.case_id.is_(None)
            if query.workspace == "unclassified"
            else catalog.workspace == query.workspace
        )
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


class SqlAlchemyPlanningUnitOfWork(SqlAlchemyUnitOfWork):
    def __enter__(self):
        super().__enter__()
        self.cases = SqlAlchemyPlanningRepository(self._session)
        self.decisions = SqlAlchemyPlanningDecisionRepository(self._session)
        self.documents = SqlAlchemyPlanningDocumentRepository(self._session)
        return self
