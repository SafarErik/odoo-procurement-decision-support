"""Authenticated server-side PDF retrieval; browser receives bytes, never credentials."""

import hashlib
import re
from dataclasses import dataclass
from uuid import UUID

import httpx

MAX_PDF_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class PlanningPDF:
    data: bytes
    filename: str
    reference: str


async def fetch_planning_pdf(cases_url, case_id, content_hash, token, *, transport=None):
    try:
        if str(UUID(case_id)) != case_id or re.fullmatch(r"[0-9a-f]{64}", content_hash) is None:
            raise ValueError("Invalid document identity")
        if not token or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError("Service access not configured")
        reference = f"t17-approved-pdf-v1:{case_id}:{content_hash}"
        async with httpx.AsyncClient(
            timeout=45, transport=transport, follow_redirects=False
        ) as client:
            async with client.stream(
                "GET",
                f"{cases_url.rstrip('/')}/{case_id}/approved-pdf/{content_hash}",
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                response.raise_for_status()
                if (
                    response.status_code != 200
                    or response.headers.get("content-type") != "application/pdf"
                    or response.headers.get("x-approved-content-hash") != content_hash
                    or response.headers.get("x-content-version") != "t17-approved-planning-v1"
                    or response.headers.get("x-pdf-reference") != reference
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
                    data, f"approved-plan-{case_id}-{content_hash[:12]}.pdf", reference
                ), ""
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return (
            None,
            "PDF unavailable. Approval remains saved. Retry the same approved document explicitly.",
        )
