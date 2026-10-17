"""PDF boundary, exact saved content, failure recovery and pagination contracts."""

import asyncio
import json
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from pypdf import PdfReader

from application.errors import RepositoryError
from backend.app.main import app
from document_adapter.approved_pdf import render_approved_pdf
from frontend.config import settings as frontend_settings
from frontend.planning.state import PlanningState
from frontend.planning_client import fetch_planning_case
from frontend.planning_pdf_client import fetch_planning_pdf
from tests.test_t15_planning_api import forbidden
from tests.test_t17_decisions import BASE, TOKEN, headers, intent
from tests.test_t17_decisions import configured as _configured
from tests.test_t17_decisions import stored_cases as _stored_cases

configured = _configured
stored_cases = _stored_cases


def approve(client, base, index=1):
    response = client.post(
        f"{BASE}/{base['case_id']}/final-decision", json=intent(base, index), headers=headers()
    )
    assert response.status_code == 201, response.text
    decision = response.json()["final_decision"]
    return decision, f"{BASE}/{base['case_id']}/approved-pdf/{decision['approved_content_hash']}"


def extracted(data):
    return "\n".join(p.extract_text() for p in PdfReader(BytesIO(data)).pages)


@pytest.mark.parametrize("index", [0, 1])
def test_pdf_matches_exact_approved_allocation_audit_and_terms(configured, monkeypatch, index):
    client, uow, base, *_ = configured
    decision, url = approve(client, base, index)
    original = (uow.rows.copy(), uow.decisions.rows.copy())
    monkeypatch.setattr("supplier_evaluation.artifacts.load_model", forbidden)
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    response = client.get(url, headers=headers())
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.headers["x-approved-content-hash"] == decision["approved_content_hash"]
    text = extracted(response.content)
    compact = "".join(text.split())
    content = decision["approved_content"]
    snapshot, audit, plan = (
        content["planning_snapshot"],
        content["human_decision"],
        content["selected_plan"],
    )
    for value in (
        base["case_id"],
        base["snapshot_hash"],
        decision["approved_content_hash"],
        content["content_version"],
        plan["total_cost"],
        audit["recorded_at"],
        audit["planning_reference_time"],
        audit["actor_reference"],
        snapshot["request"]["requirement"]["required_date"],
        snapshot["model_manifest"]["artifact_sha256"],
    ):
        assert "".join(str(value).split()) in compact
    for supplier in snapshot["request"]["suppliers"]:
        for name in ("supplier_id", "unit_price", "capacity", "promised_date"):
            assert str(supplier[name]) in text
        assert json.dumps(supplier["minimum_order"], sort_keys=True) in text
    assert f"{plan['risk_exposure']['numerator']}/{plan['risk_exposure']['denominator']}" in text
    assert "synthetic ML evidence" in text and "Approved original base" in text
    assert "not authenticated buyer identity" in text and "not a supplier-failure" in text
    document = uow.documents.rows[base["case_id"]]
    assert document.content_hash == decision["approved_content_hash"]
    assert document.pdf_hash == response.headers["x-pdf-sha256"]
    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", forbidden)
    download = client.get(url + "?download=true", headers=headers())
    assert download.status_code == 200 and download.content == response.content
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-pdf-reference"] == response.headers["x-pdf-reference"]
    assert (uow.rows, uow.decisions.rows) == original and len(uow.documents.rows) == 1


def test_pdf_denial_and_identity_authentication_leave_no_artifact(configured):
    client, uow, base, child, _ = configured

    def path(case):
        return f"{BASE}/{case['case_id']}/approved-pdf/" + "0" * 64

    assert client.get(path(base), headers=headers()).status_code == 422
    assert client.get(path(child), headers=headers()).status_code == 422
    assert client.get(path(base)).status_code == 401
    assert (
        client.get(f"{BASE}/{uuid4()}/approved-pdf/" + "0" * 64, headers=headers()).status_code
        == 404
    )
    assert (
        client.get(f"{BASE}/{base['case_id']}/approved-pdf/bad", headers=headers()).status_code
        == 422
    )
    client.post(
        f"{BASE}/{base['case_id']}/final-decision",
        json=intent(base, None, "no_award"),
        headers=headers(),
    )
    assert client.get(path(base), headers=headers()).status_code == 422
    assert not uow.documents.rows


def test_render_failure_and_commit_failure_preserve_approval_and_retry_same_content(
    configured, monkeypatch
):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)
    original = (uow.rows.copy(), uow.decisions.rows.copy())
    renderer = []

    def failing(content):
        renderer.append(deepcopy(content))
        raise RuntimeError("private-token-database-url")

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", failing)
    response = client.get(url, headers=headers())
    assert (
        response.status_code == 503
        and response.json()["detail"]["code"] == "approved_pdf_unavailable"
    )
    assert "private-token" not in response.text and not uow.documents.rows
    assert (
        client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["final_decision"]
        == decision
    )

    def successful(content):
        renderer.append(deepcopy(content))
        return render_approved_pdf(content)

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", successful)
    commit = uow.commit

    def fail_commit():
        raise RepositoryError("repository_failure", "save failed")

    monkeypatch.setattr(uow, "commit", fail_commit)
    assert client.get(url, headers=headers()).status_code == 503 and not uow.documents.rows
    monkeypatch.setattr(uow, "commit", commit)
    assert client.get(url, headers=headers()).status_code == 200
    assert renderer[0] == renderer[1] == renderer[2] == decision["approved_content"]
    assert (uow.rows, uow.decisions.rows) == original
    assert client.get(url[:-64] + "0" * 64, headers=headers()).status_code == 409
    document = uow.documents.rows[base["case_id"]]
    uow.documents.rows[document.case_id] = replace(document, content_hash="0" * 64)
    assert client.get(url, headers=headers()).status_code == 503


def test_long_unicode_names_rationale_provenance_paginate_without_losing_text(configured):
    client, _, base, *_ = configured
    decision, _ = approve(client, base)
    content = deepcopy(decision["approved_content"])
    identity = content["planning_snapshot"]["request"]["suppliers"][0]["supplier_id"]
    label = "Árvíztűrő Őrség Kft. Ω Ж - " + "supplier_name_" * 15
    content = json.loads(json.dumps(content, ensure_ascii=False).replace(identity, label))
    content["human_decision"]["actor_reference"] = "Árvíztűrő tükörfúrógép Ω Ж"
    content["human_decision"]["rationale"] = "Long explanation & <escaped markup> " * 55
    content["planning_snapshot"]["provenance"]["entries"] *= 3
    data, _ = render_approved_pdf(content)
    reader = PdfReader(BytesIO(data))
    assert len(reader.pages) >= 5
    compact = "".join(extracted(data).split())
    assert "".join(label.split()) in compact
    assert "Longexplanation&<escapedmarkup>" in compact
    assert "ÁrvíztűrőtükörfúrógépΩЖ" in compact
    for page in reader.pages:
        assert "Controlled demonstration" in page.extract_text()


@pytest.mark.parametrize("failure", ["unsupported_glyph", "invalid_bytes"])
def test_renderer_limits_fail_without_changing_approval(configured, monkeypatch, failure):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)

    def render(content):
        if failure == "invalid_bytes":
            return b"not a PDF", "invalid-renderer"
        content = deepcopy(content)
        content["human_decision"]["actor_reference"] = "\U0001f9d1"
        return render_approved_pdf(content)

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", render)
    assert client.get(url, headers=headers()).status_code == 503
    assert not uow.documents.rows
    assert (
        client.get(f"{BASE}/{base['case_id']}", headers=headers()).json()["final_decision"]
        == decision
    )


def test_pdf_frontend_view_download_failure_and_same_identity_retry(configured, monkeypatch):
    client, _, base, *_ = configured
    decision, _ = approve(client, base)
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://test")
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    transport = httpx.ASGITransport(app=app)
    calls = []

    async def fetch(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            return None, "PDF unavailable; approval remains saved"
        return await fetch_planning_pdf(*args, **kwargs, transport=transport)

    monkeypatch.setattr("frontend.planning.state.fetch_planning_pdf", fetch)

    async def run():
        display, _ = await fetch_planning_case(
            "http://test" + BASE, base["case_id"], TOKEN, transport=transport
        )
        state = PlanningState(_reflex_internal_init=True)
        state._show(display)
        before = state.details.copy()
        async for _ in state.request_pdf():
            pass
        assert state.details == before and state.pdf_error and not state.pdf_data_url
        async for _ in state.request_pdf():
            pass
        assert state.pdf_data_url.startswith("data:application/pdf;base64,") and not state.pdf_error
        assert calls[0] == calls[1] and TOKEN not in state.pdf_data_url
        assert state.pdf_filename.endswith(".pdf") and state.details == before
        assert decision["approved_content_hash"] in state.pdf_reference
        state._show(display)
        assert not state.pdf_data_url and not state.pdf_error

    asyncio.run(run())


@pytest.mark.parametrize(
    "corruption", ["hash", "reference", "mime", "version", "bytes", "oversize", "redirect"]
)
def test_pdf_client_fails_closed_on_unsupported_response(configured, corruption):
    client, _, base, *_ = configured
    decision, url = approve(client, base)
    good = client.get(url, headers=headers())
    response_headers = dict(good.headers)
    data = good.content
    status = 200
    if corruption in {"hash", "reference", "mime", "version"}:
        name = {
            "hash": "x-pdf-sha256",
            "reference": "x-pdf-reference",
            "mime": "content-type",
            "version": "x-content-version",
        }[corruption]
        response_headers[name] = "unsupported"
    elif corruption == "bytes":
        data = b"not a PDF"
    elif corruption == "oversize":
        data = b"x" * (2 * 1024 * 1024 + 1)
    else:
        status = 302

    def respond(request):
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        return httpx.Response(status, headers=response_headers, content=data)

    result, error = asyncio.run(
        fetch_planning_pdf(
            "http://test" + BASE,
            base["case_id"],
            decision["approved_content_hash"],
            TOKEN,
            transport=httpx.MockTransport(respond),
        )
    )
    assert result is None and "Approval remains saved" in error and TOKEN not in error
