"""Immutable PDF bytes/reference in the existing helper database."""

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from application.errors import RepositoryError
from application.planning_documents import PlanningDocument
from persistence.schema import PlanningDocumentRecord


class SqlAlchemyPlanningDocumentRepository:
    def __init__(self, session):
        self._session = session

    def lock(self, case_id):
        try:
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "t21:pdf:" + case_id}
            )
        except SQLAlchemyError as error:
            raise RepositoryError(
                "repository_failure", "PDF storage could not be locked."
            ) from error

    def get(self, case_id, language, kind):
        try:
            row = self._session.execute(
                select(PlanningDocumentRecord).where(
                    PlanningDocumentRecord.case_id == case_id,
                    PlanningDocumentRecord.language == language,
                    PlanningDocumentRecord.kind == kind,
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            document = PlanningDocument(
                row.case_id,
                row.content_version,
                row.content_hash,
                row.reference,
                row.renderer_version,
                row.pdf,
                row.language,
                row.kind,
            )
            if document.pdf_hash != row.pdf_hash:
                raise RepositoryError("approved_pdf_unavailable", "PDF integrity failed.")
            return document
        except SQLAlchemyError as error:
            raise RepositoryError("repository_failure", "PDF storage could not be read.") from error

    def add(self, document):
        self._session.add(
            PlanningDocumentRecord(
                case_id=document.case_id,
                language=document.language,
                kind=document.kind,
                content_version=document.content_version,
                content_hash=document.content_hash,
                reference=document.reference,
                renderer_version=document.renderer_version,
                pdf_hash=document.pdf_hash,
                pdf=document.pdf,
            )
        )
        try:
            self._session.flush()
        except SQLAlchemyError as error:
            raise RepositoryError("repository_failure", "PDF could not be stored.") from error
