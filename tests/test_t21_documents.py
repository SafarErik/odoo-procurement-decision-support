"""PDF v3 boundary: HU/EN plan and audit artifacts from exact approved content, recovery."""

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
from application.planning_documents import PlanningDocument
from backend.app.main import app
from document_adapter.approved_pdf import render_audit_pdf, render_plan_pdf
from frontend.config import settings as frontend_settings
from frontend.i18n import tr
from frontend.planning.state import PlanningState
from frontend.planning_client import fetch_planning_case
from frontend.planning_pdf_client import fetch_planning_pdf
from tests.frontend_patching import patch_client
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
    assert response.headers["content-language"] == "hu"
    assert response.headers["content-disposition"].startswith("inline;")
    assert "jovahagyott-beszerzesi-terv" in response.headers["content-disposition"]
    assert response.headers["x-approved-content-hash"] == decision["approved_content_hash"]
    assert response.headers["x-document-kind"] == "plan"
    assert response.headers["x-pdf-reference"] == (
        f"t17-approved-pdf-v3:{base['case_id']}:hu:plan:{decision['approved_content_hash']}"
    )
    reader = PdfReader(BytesIO(response.content))
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
        decision["approved_content_hash"],
        audit["actor_reference"].strip(),
        snapshot["model_manifest"]["metadata"]["model_id"][:12],
    ):
        assert "".join(str(value).split()) in compact
    total = plan["total_cost"]
    assert f"{int(total) if '.' not in total else total},00EUR".replace(".", ",") in compact
    required = snapshot["request"]["requirement"]["required_date"].replace("-", ".") + "."
    assert required in compact
    allocated = [a for a in plan["allocations"] if a["quantity"] > 0]
    pages = [page.extract_text() for page in reader.pages]
    proposals = [p for p in pages if "Rendelési tétel" in p]
    assert len(proposals) == len(allocated)
    for page, allocation in zip(proposals, allocated, strict=True):
        assert allocation["supplier_id"] in page and str(allocation["quantity"]) in page
    unit = snapshot["request"]["requirement"]["quantity_unit"]
    assert unit == "piece" and " piece" not in text and " db" in text  # Odoo unit name mapped
    assert pages[0].count("Jóváhagyott beszerzési terv") >= 1 and "Összefoglaló" in pages[0]
    # Plan: supplier assessment table and verification identifiers; no audit detail.
    assert len(pages) <= len(allocated) + 2
    assert "Beszállítói értékelések" in pages[0] and "Kockázati pontszám" in pages[0]
    for supplier in snapshot["request"]["suppliers"]:
        assert supplier["supplier_id"] in pages[0]
    assert "Ellenőrzési azonosítók" in pages[-1] and "Audit nézetéből" in pages[-1]
    assert "Tervezési feltételezések" in proposals[0]
    for absent in (
        "Mezőszintű adatforrások",
        "Döntési útvonal",
        "Audit melléklet –",
        "Modellfájl SHA-256",
    ):
        assert absent not in text
    assert snapshot["model_manifest"]["artifact_sha256"] not in compact
    assert base["snapshot_hash"] not in compact
    assert '{"' not in text and "numerator" not in text  # no raw JSON
    assert "szintetikus bemutató modellből" in pages[0]
    document = uow.documents.rows[(base["case_id"], "hu", "plan")]
    assert document.content_hash == decision["approved_content_hash"]
    assert document.pdf_hash == response.headers["x-pdf-sha256"]
    english = client.get(url, params={"language": "en"}, headers=headers())
    assert english.status_code == 200 and english.headers["content-language"] == "en"
    english_text = extracted(english.content)
    assert english_text.count("Order line") == len(allocated)
    assert " piece" not in english_text and " pcs" in english_text
    assert "Verification identifiers" in english_text and "Planning assumptions" in english_text
    assert "Approved procurement plan" in english_text and "Decision path" not in english_text
    assert english.content != response.content and len(uow.documents.rows) == 2
    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", forbidden)
    download = client.get(url + "?download=true", headers=headers())
    assert download.status_code == 200 and download.content == response.content
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-pdf-reference"] == response.headers["x-pdf-reference"]
    assert (uow.rows, uow.decisions.rows) == original and len(uow.documents.rows) == 2
    assert client.get(url + "?language=de", headers=headers()).status_code == 422


def test_pre_p2_english_artifact_is_served_unchanged_as_plan(configured, monkeypatch):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)
    content_hash = decision["approved_content_hash"]
    legacy = PlanningDocument(
        base["case_id"],
        "t17-approved-planning-v1",
        content_hash,
        f"t17-approved-pdf-v1:{base['case_id']}:{content_hash}",
        "reportlab/ProcurementDejaVu/layout-v1",
        b"%PDF-1.4\nlegacy english bytes\n%%EOF",
        "en",
    )
    uow.documents.rows[(base["case_id"], "en", "plan")] = legacy
    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", forbidden)
    response = client.get(url, params={"language": "en"}, headers=headers())
    assert response.status_code == 200 and response.content == legacy.pdf
    assert response.headers["x-pdf-reference"] == legacy.reference
    assert response.headers["x-document-kind"] == "plan"
    from backend.app.dependencies import render_approved_document

    monkeypatch.setattr(
        "backend.app.routes.planning_cases.render_approved_document", render_approved_document
    )
    hungarian = client.get(url, headers=headers())
    assert hungarian.status_code == 200 and hungarian.headers["content-language"] == "hu"
    assert uow.documents.rows[(base["case_id"], "en", "plan")] is legacy


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

    def failing(content, language, kind):
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

    def successful(content, language, kind):
        renderer.append(deepcopy(content))
        return render_plan_pdf(content, language)

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
    document = uow.documents.rows[(base["case_id"], "hu", "plan")]
    uow.documents.rows[(document.case_id, "hu", "plan")] = replace(document, content_hash="0" * 64)
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
    for render, header in (
        (render_plan_pdf, "Jóváhagyott beszerzési terv"),
        (render_audit_pdf, "Audit melléklet"),
    ):
        data, _ = render(content)
        reader = PdfReader(BytesIO(data))
        assert len(reader.pages) >= 3
        compact = "".join(extracted(data).split())
        assert "".join(label.split()) in compact
        assert "Longexplanation&<escapedmarkup>" in compact
        assert "ÁrvíztűrőtükörfúrógépΩЖ" in compact
        for page in reader.pages:
            assert header in page.extract_text()


@pytest.mark.parametrize("failure", ["unsupported_glyph", "invalid_bytes"])
def test_renderer_limits_fail_without_changing_approval(configured, monkeypatch, failure):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)

    def render(content, language, kind):
        if failure == "invalid_bytes":
            return b"not a PDF", "invalid-renderer"
        content = deepcopy(content)
        content["human_decision"]["actor_reference"] = "\U0001f9d1"
        return render_plan_pdf(content, language)

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

    patch_client(monkeypatch, "fetch_planning_pdf", fetch)

    async def run():
        display, _ = await fetch_planning_case(
            "http://test" + BASE, base["case_id"], TOKEN, transport=transport
        )
        state = PlanningState(_reflex_internal_init=True)
        state.lang = "en"  # the assertions below read English texts
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
    "corruption",
    ["hash", "reference", "mime", "version", "language", "kind", "bytes", "oversize", "redirect"],
)
def test_pdf_client_fails_closed_on_unsupported_response(configured, corruption):
    client, _, base, *_ = configured
    decision, url = approve(client, base)
    good = client.get(url, headers=headers())
    response_headers = dict(good.headers)
    data = good.content
    status = 200
    if corruption in {"hash", "reference", "mime", "version", "language", "kind"}:
        name = {
            "hash": "x-pdf-sha256",
            "reference": "x-pdf-reference",
            "mime": "content-type",
            "version": "x-content-version",
            "language": "content-language",
            "kind": "x-document-kind",
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
    # Hungarian is the default document language, so the message is Hungarian too.
    assert result is None and error == tr("err_pdf", "hu") and TOKEN not in error


def test_pdf_names_a_plan_proved_only_by_the_balanced_stage(configured):
    client, _, base, *_ = configured
    decision, _ = approve(client, base, 1)
    content = deepcopy(decision["approved_content"])
    for run in content["planning_snapshot"]["result"]["runs"]:
        if run["plan_index"] == 1:
            run["kind"] = "diversified"
    hu, _ = render_plan_pdf(content, "hu")
    en, _ = render_plan_pdf(content, "en")
    assert "Kiegyensúlyozott terv" in extracted(hu)
    assert "Balanced plan" in extracted(en)
    assert "Rendelési tétel – jóváhagyott terv" in extracted(hu)


def test_plan_and_audit_documents_share_content_and_are_stored_per_kind(configured, monkeypatch):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)
    content_hash = decision["approved_content_hash"]
    monkeypatch.setattr("supplier_evaluation.artifacts.load_model", forbidden)
    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", forbidden)
    first = {}
    for language in ("hu", "en"):
        for kind in ("plan", "audit"):
            response = client.get(
                url, params={"language": language, "kind": kind}, headers=headers()
            )
            assert response.status_code == 200, response.text
            assert response.headers["x-document-kind"] == kind
            assert response.headers["content-language"] == language
            assert response.headers["x-approved-content-hash"] == content_hash
            assert response.headers["x-pdf-reference"] == (
                f"t17-approved-pdf-v3:{base['case_id']}:{language}:{kind}:{content_hash}"
            )
            first[(language, kind)] = response
    assert set(uow.documents.rows) == {
        (base["case_id"], language, kind) for language in ("hu", "en") for kind in ("plan", "audit")
    }
    assert len({r.content for r in first.values()}) == 4
    names = {key: r.headers["content-disposition"] for key, r in first.items()}
    assert "jovahagyott-beszerzesi-terv" in names[("hu", "plan")]
    assert "approved-procurement-plan" in names[("en", "plan")]
    assert f"audit-melleklet-{base['case_id']}" in names[("hu", "audit")]
    assert f"audit-appendix-{base['case_id']}" in names[("en", "audit")]
    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", forbidden)
    for (language, kind), response in first.items():
        again = client.get(url, params={"language": language, "kind": kind}, headers=headers())
        assert again.status_code == 200 and again.content == response.content
    audit = extracted(first[("hu", "audit")].content)
    compact = "".join(audit.split())
    content = decision["approved_content"]
    assert "Audit melléklet – jóváhagyott beszerzési terv" in audit
    for heading in (
        "Mezőszintű adatforrások",
        "Beszállítóértékelő modell",
        "Döntési útvonal",
        "Döntési napló",
        "Optimalizálás",
    ):
        assert heading in audit
    for value in (
        base["case_id"],
        base["snapshot_hash"],
        content_hash,
        content["planning_snapshot"]["model_manifest"]["artifact_sha256"],
    ):
        assert value in compact
    assert "Rendelési tétel" not in audit
    english = extracted(first[("en", "audit")].content)
    assert "Audit appendix – approved procurement plan" in english
    assert "Field-level data sources" in english and "Decision log" in english


@pytest.mark.parametrize("renderer", ["layout-v3", "layout-v4"])
def test_stored_combined_v2_document_stays_the_plan_and_audit_is_added(
    configured, monkeypatch, renderer
):
    client, uow, base, *_ = configured
    decision, url = approve(client, base)
    content_hash = decision["approved_content_hash"]
    legacy = PlanningDocument(
        base["case_id"],
        "t17-approved-planning-v1",
        content_hash,
        f"t17-approved-pdf-v2:{base['case_id']}:hu:{content_hash}",
        f"reportlab/ProcurementDejaVu/{renderer}",
        b"%PDF-1.4\ncombined plan and audit appendix\n%%EOF",
        "hu",
        "plan",
    )
    uow.documents.rows[(base["case_id"], "hu", "plan")] = legacy
    calls = []

    def render(content, language, kind):
        calls.append(kind)
        return render_audit_pdf(content, language)

    monkeypatch.setattr("backend.app.routes.planning_cases.render_approved_document", render)
    plan = client.get(url, headers=headers())
    assert plan.status_code == 200 and plan.content == legacy.pdf
    assert plan.headers["x-pdf-reference"] == legacy.reference and not calls
    assert plan.headers["x-document-kind"] == "plan"
    audit = client.get(url, params={"kind": "audit"}, headers=headers())
    assert audit.status_code == 200 and calls == ["audit"]
    assert audit.headers["x-approved-content-hash"] == content_hash
    assert audit.headers["x-pdf-reference"].startswith("t17-approved-pdf-v3:")
    assert uow.documents.rows[(base["case_id"], "hu", "plan")] is legacy
    assert "Audit melléklet" in extracted(audit.content)
    # A v2 reference is never accepted for the audit kind.
    uow.documents.rows[(base["case_id"], "hu", "audit")] = replace(legacy, kind="audit")
    assert client.get(url, params={"kind": "audit"}, headers=headers()).status_code == 503


def test_no_document_of_either_kind_without_approval_and_unknown_kind_rejected(configured):
    client, uow, base, child, _ = configured
    for kind in ("plan", "audit"):
        for case in (base, child):  # unapproved base, scenario
            response = client.get(
                f"{BASE}/{case['case_id']}/approved-pdf/" + "0" * 64,
                params={"kind": kind},
                headers=headers(),
            )
            assert response.status_code == 422
    _, url = approve(client, base)
    assert client.get(url, params={"kind": "summary"}, headers=headers()).status_code == 422
    assert not uow.documents.rows


def test_no_award_has_no_document_of_either_kind(configured):
    client, uow, base, *_ = configured
    client.post(
        f"{BASE}/{base['case_id']}/final-decision",
        json=intent(base, None, "no_award"),
        headers=headers(),
    )
    for kind in ("plan", "audit"):
        response = client.get(
            f"{BASE}/{base['case_id']}/approved-pdf/" + "0" * 64,
            params={"kind": kind},
            headers=headers(),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "approved_pdf_ineligible"
    assert not uow.documents.rows


def test_application_rejects_unknown_document_kind(configured):
    from application.planning_cases import PlanningCaseError
    from application.planning_documents import approved_document

    _, uow, base, *_ = configured
    with pytest.raises(PlanningCaseError) as error:
        approved_document(uow, base["case_id"], "0" * 64, forbidden, "hu", "summary")
    assert error.value.code == "invalid_document_kind"


def test_audit_view_fetches_audit_appendix_with_same_error_handling(configured, monkeypatch):
    client, _, base, *_ = configured
    decision, _ = approve(client, base)
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://test")
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    transport = httpx.ASGITransport(app=app)
    calls = []

    async def fetch(*args, **kwargs):
        calls.append(kwargs["kind"])
        if len(calls) == 1:
            return None, "PDF unavailable; approval remains saved"
        return await fetch_planning_pdf(*args, **kwargs, transport=transport)

    patch_client(monkeypatch, "fetch_planning_pdf", fetch)

    async def run():
        display, _ = await fetch_planning_case(
            "http://test" + BASE, base["case_id"], TOKEN, transport=transport
        )
        state = PlanningState(_reflex_internal_init=True)
        state.lang = "en"
        state._show(display)
        async for _ in state.request_audit_pdf():
            pass
        assert state.audit_pdf_error and not state.audit_pdf_data_url and not state.pdf_error
        async for _ in state.request_audit_pdf():
            pass
        assert state.audit_pdf_data_url.startswith("data:application/pdf;base64,")
        assert not state.audit_pdf_error and not state.pdf_data_url
        assert state.audit_pdf_filename.startswith("audit-appendix-")
        assert f":en:audit:{decision['approved_content_hash']}" in state.audit_pdf_reference
        assert calls == ["audit", "audit"]
        state._show(display)
        assert not state.audit_pdf_data_url and not state.audit_pdf_error

    asyncio.run(run())


def test_audit_view_pdf_requires_an_approved_case(configured):
    _, _, base, *_ = configured

    async def run():
        state = PlanningState(_reflex_internal_init=True)
        state.lang = "en"
        state.has_case = True
        state.details = {"case_id": base["case_id"], "final_outcome": ""}
        async for _ in state.request_audit_pdf():
            pass
        assert state.audit_pdf_error == tr("err_pdf_not_approved", "en")

    asyncio.run(run())
