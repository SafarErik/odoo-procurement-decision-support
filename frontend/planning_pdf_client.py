"""Authenticated server-side PDF retrieval; browser receives bytes, never credentials."""

import hashlib
import re
from dataclasses import dataclass
from uuid import UUID

import httpx

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
    data: bytes
    filename: str
    reference: str


async def fetch_planning_pdf(
    cases_url, case_id, content_hash, token, *, language="hu", kind="plan", transport=None
):
    try:
        if str(UUID(case_id)) != case_id or re.fullmatch(r"[0-9a-f]{64}", content_hash) is None:
            raise ValueError("Invalid document identity")
        if language not in ("hu", "en"):
            raise ValueError("Unsupported document language")
        if kind not in ("plan", "audit"):
            raise ValueError("Unsupported document kind")
        if not token or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError("Service access not configured")
        references = {f"t17-approved-pdf-v3:{case_id}:{language}:{kind}:{content_hash}"}
        if kind == "plan":  # combined plan + appendix PDFs stored before the split
            references.add(f"t17-approved-pdf-v2:{case_id}:{language}:{content_hash}")
            if language == "en":  # English PDFs stored before P2 keep their v1 reference
                references.add(f"t17-approved-pdf-v1:{case_id}:{content_hash}")
        async with httpx.AsyncClient(
            timeout=45, transport=transport, follow_redirects=False
        ) as client:
            async with client.stream(
                "GET",
                f"{cases_url.rstrip('/')}/{case_id}/approved-pdf/{content_hash}",
                params={"language": language, "kind": kind},
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                response.raise_for_status()
                if (
                    response.status_code != 200
                    or response.headers.get("content-type") != "application/pdf"
                    or response.headers.get("x-approved-content-hash") != content_hash
                    or response.headers.get("x-content-version") != "t17-approved-planning-v1"
                    or response.headers.get("x-pdf-reference") not in references
                    or response.headers.get("content-language") != language
                    or response.headers.get("x-document-kind") != kind
                ):
                    raise ValueError("Unsupported PDF response")
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(data) + len(chunk) > MAX_PDF_BYTES:
                        raise ValueError("PDF response exceeds limit")
                    data.extend(chunk)
                data = bytes(data)
                if (
                    not data.startswith(b"%PDF-")
                    or not data.rstrip().endswith(b"%%EOF")
                    or hashlib.sha256(data).hexdigest() != response.headers.get("x-pdf-sha256")
                ):
                    raise ValueError("Invalid PDF integrity")
                return PlanningPDF(
                    data,
                    f"{FILENAMES[(kind, language)]}-{case_id}-{content_hash[:12]}-{language}.pdf",
                    response.headers["x-pdf-reference"],
                ), ""
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return None, tr("err_pdf", language if language in ("hu", "en") else "en")
