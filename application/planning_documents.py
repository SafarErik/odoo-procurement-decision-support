"""Approved-content PDF retrieval and atomic artifact storage, without acquisition.

One immutable artifact per (case, language, kind): the approved procurement plan
(``plan``) and its audit appendix (``audit``), both rendered from the same approved content
(ADR-036). Combined plan + appendix documents stored before the split (v1 English, v2)
are served unchanged as ``plan``.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from application.errors import RepositoryError
from application.planning_cases import PlanningCaseError, canonical_uuid
from application.planning_decisions import CONTENT_VERSION, validate_final_decision

DOCUMENT_VERSION = "t17-approved-pdf-v3"
COMBINED_DOCUMENT_VERSION = "t17-approved-pdf-v2"  # plan + audit appendix in one PDF
LEGACY_DOCUMENT_VERSION = "t17-approved-pdf-v1"  # English only, no language in reference
DOCUMENT_LANGUAGES = ("hu", "en")
DOCUMENT_KINDS = ("plan", "audit")
FILENAMES = {
    ("plan", "hu"): "jovahagyott-beszerzesi-terv",
    ("plan", "en"): "approved-procurement-plan",
    ("audit", "hu"): "audit-melleklet",
    ("audit", "en"): "audit-appendix",
}
MAX_PDF_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class PlanningDocument:
    case_id: str
    content_version: str
    content_hash: str
    reference: str
    renderer_version: str
    pdf: bytes
    language: str = "en"
    kind: str = "plan"

    @property
    def pdf_hash(self):
        return hashlib.sha256(self.pdf).hexdigest()

    @property
    def filename(self):
        name = FILENAMES[(self.kind, self.language)]
        return f"{name}-{self.case_id}-{self.content_hash[:12]}-{self.language}.pdf"


class PlanningDocumentRepository(Protocol):
    def lock(self, case_id: str) -> None: ...
    def get(self, case_id: str, language: str, kind: str) -> PlanningDocument | None: ...
    def add(self, document: PlanningDocument) -> None: ...


def legacy_references(case_id, language, content_hash):
    """Combined documents stored before the split; valid only as ``plan``."""
    references = {f"{COMBINED_DOCUMENT_VERSION}:{case_id}:{language}:{content_hash}"}
    if language == "en":  # pre-P2 English artifact
        references.add(f"{LEGACY_DOCUMENT_VERSION}:{case_id}:{content_hash}")
    return references


def approved_document(uow, case_id, content_hash, render, language="hu", kind="plan"):
    canonical_uuid(case_id)
    if language not in DOCUMENT_LANGUAGES:
        raise PlanningCaseError("invalid_document_language", "Use hu or en.")
    if kind not in DOCUMENT_KINDS:
        raise PlanningCaseError("invalid_document_kind", "Use plan or audit.")
    if not isinstance(content_hash, str) or re.fullmatch(r"[0-9a-f]{64}", content_hash) is None:
        raise PlanningCaseError("invalid_document_identity", "Use the saved approved content hash.")
    with uow:
        uow.documents.lock(case_id)
        case = uow.cases.get(case_id)
        if case is None:
            raise PlanningCaseError("planning_case_not_found", "The planning case does not exist.")
        decision = uow.decisions.get(case_id)
        if case.parent_id is not None or decision is None:
            raise PlanningCaseError(
                "approved_pdf_ineligible", "Only an approved original base has a PDF."
            )
        value = validate_final_decision(case, decision)
        content = value["approved_content"]
        if content is None:
            raise PlanningCaseError("approved_pdf_ineligible", "No-award has no approved PDF.")
        if value["approved_content_hash"] != content_hash:
            raise PlanningCaseError("approved_content_hash_mismatch", "Reload the saved approval.")
        reference = f"{DOCUMENT_VERSION}:{case_id}:{language}:{kind}:{content_hash}"
        document = uow.documents.get(case_id, language, kind)
        stored = document is not None
        if document is None:
            try:
                pdf, renderer_version = render(content, language, kind)
            except Exception as error:
                raise RepositoryError(
                    "approved_pdf_unavailable", "The approved PDF could not be rendered."
                ) from error
            document = PlanningDocument(
                case_id,
                content["content_version"],
                content_hash,
                reference,
                renderer_version,
                pdf,
                language,
                kind,
            )
        elif kind == "plan" and document.reference in legacy_references(
            case_id, language, content_hash
        ):
            reference = document.reference  # immutable combined document stored before v3
        if (
            document.case_id != case_id
            or document.language != language
            or document.kind != kind
            or document.content_version != CONTENT_VERSION
            or document.content_hash != content_hash
            or document.reference != reference
            or not isinstance(document.renderer_version, str)
            or not document.renderer_version.strip()
            or not isinstance(document.pdf, bytes)
            or not 1 <= len(document.pdf) <= MAX_PDF_BYTES
            or not document.pdf.startswith(b"%PDF-")
            or not document.pdf.rstrip().endswith(b"%%EOF")
        ):
            raise RepositoryError(
                "approved_pdf_unavailable", "The approved PDF artifact is invalid."
            )
        if not stored:
            uow.documents.add(document)
            uow.commit()
        return document
