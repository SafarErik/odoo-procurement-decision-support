"""Approved documents resource: server-side PDF retrieval; the browser gets bytes only."""

import hashlib
import re
from dataclasses import dataclass

from frontend.api import http
from frontend.api.parsing import is_uuid
from frontend.config import settings
from frontend.i18n import tr

MAX_PDF_BYTES = 2 * 1024 * 1024
# Mirrors application/planning_documents.py ``FILENAMES`` (the frontend may not import it).
FILENAMES = {
    ("plan", "hu"): "jovahagyott-beszerzesi-terv",
    ("plan", "en"): "approved-procurement-plan",
    ("audit", "hu"): "audit-melleklet",
    ("audit", "en"): "audit-appendix",
}


@dataclass(frozen=True, slots=True)
class PlanningPDF:
    """Verified PDF bytes with the download filename and the PDF reference."""

    data: bytes
    filename: str
    reference: str


async def fetch_planning_pdf(case_id, content_hash, *, language="hu", kind="plan"):
    """The approved plan or audit appendix PDF, checked against the approved content hash."""
    try:
        if not is_uuid(case_id) or re.fullmatch(r"[0-9a-f]{64}", content_hash) is None:
            raise ValueError("Invalid document identity")
        if language not in ("hu", "en"):
            raise ValueError("Unsupported document language")
        if kind not in ("plan", "audit"):
            raise ValueError("Unsupported document kind")
        reference = f"t17-approved-pdf-v3:{case_id}:{language}:{kind}:{content_hash}"

        def check(headers):
            """Reject a response whose headers do not name this exact approved document."""
            if (
                headers.get("content-type") != "application/pdf"
                or headers.get("x-approved-content-hash") != content_hash
                or headers.get("x-content-version") != "t17-approved-planning-v1"
                or headers.get("x-pdf-reference") != reference
                or headers.get("content-language") != language
                or headers.get("x-document-kind") != kind
            ):
                raise ValueError("Unsupported PDF response")

        headers, data = await http.get_bytes(
            f"{settings.planning_cases_url}/{case_id}/approved-pdf/{content_hash}",
            params={"language": language, "kind": kind},
            limit=MAX_PDF_BYTES,
            check_headers=check,
        )
        if (
            not data.startswith(b"%PDF-")
            or not data.rstrip().endswith(b"%%EOF")
            or hashlib.sha256(data).hexdigest() != headers.get("x-pdf-sha256")
        ):
            raise ValueError("Invalid PDF integrity")
        return PlanningPDF(
            data,
            f"{FILENAMES[(kind, language)]}-{case_id}-{content_hash[:12]}-{language}.pdf",
            headers["x-pdf-reference"],
        ), ""
    except (http.TokenMissing, http.Unreachable, ValueError, TypeError, AttributeError):
        return None, tr("err_pdf", language if language in ("hu", "en") else "en")
