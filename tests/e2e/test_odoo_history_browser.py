"""Opt-in live restricted Odoo -> Reflex -> stored planning/approval/PDF acceptance."""

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
from dotenv import dotenv_values

from tests.e2e.conftest import wait_until
from tools.t17_demo import run_flow, verify_stored

pytestmark = [
    pytest.mark.integration,
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.getenv("RUN_ODOO_HISTORY_E2E") != "true",
        reason="Explicit RUN_ODOO_HISTORY_E2E=true required for bounded local Odoo reads.",
    ),
]
BASE = "/api/v2/procurement/planning-cases"


def test_live_history_to_saved_approval_pdf(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    root = Path(__file__).resolve().parents[2]
    original = dotenv_values(root / ".env", encoding="utf-8-sig")
    testcopy = dotenv_values(root / ".env.v2-history-test", encoding="utf-8-sig")
    assert testcopy["ODOO_DATABASE"] == "procurement_v2_history_test_v1"
    stack.stop(stack.api)
    stack.env.update(
        ODOO_BASE_URL=original["ODOO_BASE_URL"],
        ODOO_API_KEY=original["ODOO_API_KEY"],
        ODOO_HISTORY_DATABASE=testcopy["ODOO_DATABASE"],
        ODOO_HISTORY_API_KEY=testcopy["ODOO_T7S_API_KEY"],
        ODOO_HISTORY_QUOTATION_API_KEY=testcopy["ODOO_API_KEY"],
        ODOO_HISTORY_MODEL_DIRECTORY=str(
            root / ".artifacts/v2-odoo-history-integration/qualified-model"
        ),
        PLANNING_LIBRARY_COMPANY_ID="odoo:res.company:1",
    )
    stack.start_api()
    page.goto(stack.frontend_url + "/planning")
    page.get_by_role("tab", name="Odoo", exact=True).click()
    page.get_by_role("button", name="Use history from Odoo", exact=True).click()
    expect(page.locator("body")).to_contain_text("100.00%")
    expect(page.locator("body")).to_contain_text("66.67%")
    expect(page.locator("body")).to_contain_text("33.33%")
    page.get_by_role("button", name="Review Odoo terms", exact=True).click()
    page.get_by_role("button", name="Calculate and save comparison", exact=True).click()
    expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
    page.wait_for_url("**/planning?case_id=*&view=plans")
    case_id = parse_qs(urlsplit(page.url).query)["case_id"][0]
    preview = stack.client.get(BASE + "/odoo-history/local-v1").json()
    replay_payload = {k: preview[k] for k in ("profile_id", "profile_revision", "terms")}
    replay_key = str(uuid4())
    replay_headers = {"Idempotency-Key": replay_key}
    replay_base = stack.client.post(
        BASE + "/from-odoo-history", json=replay_payload, headers=replay_headers
    )
    assert replay_base.status_code == 201
    saved = stack.client.get(BASE + "/" + case_id).json()
    assert saved["snapshot"]["facts"]["source_type"] == "odoo_projection"
    capture = json.loads(saved["snapshot"]["facts"]["history"])
    assert capture["evidence"]["database"] == testcopy["ODOO_DATABASE"]
    assert [p["value"] for p in capture["performance"]] == ["100.00", "66.67", "33.33"]
    page.goto(stack.frontend_url + f"/planning?case_id={case_id}&view=suppliers")
    expect(page.get_by_role("heading", name="Why these supplier assessments?")).to_be_visible()
    expect(page.locator("body")).to_contain_text("completed purchase lines")
    page.goto(stack.frontend_url + f"/planning?case_id={case_id}&view=whatif")
    page.get_by_label("Scenario type", exact=True).select_option("supplier_outage")
    page.get_by_label("Supplier to change (original terms)", exact=True).select_option(
        "odoo:res.partner:53"
    )
    page.get_by_role("button", name="Create and save scenario", exact=True).click()
    expect(page.get_by_role("heading", name="Saved scenario comparison")).to_be_visible()
    page.goto(stack.frontend_url + f"/planning?case_id={case_id}&view=plans")
    page.get_by_role("button", name="Select Minimum cost for review", exact=True).click()
    page.get_by_role("button", name="Review selected plan", exact=True).click()
    page.get_by_label("Actor audit reference", exact=True).fill("odoo-history-technical-acceptance")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Review approval", exact=True).click()
    page.get_by_role("button", name="Approve plan", exact=True).click()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    page.get_by_role("button", name="View approved PDF", exact=True).click()
    expect(page.get_by_role("status").filter(has_text="The PDF is ready.")).to_be_visible()
    approved = stack.client.get(BASE + "/" + case_id).json()
    content_hash = approved["final_decision"]["approved_content_hash"]
    pdf = stack.client.get(BASE + f"/{case_id}/approved-pdf/{content_hash}")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
    (stack.root / "approved-history.pdf").write_bytes(pdf.content)
    stack.evidence["checks"].append(
        "Live Odoo history -> UI creation -> actual tree/CBC -> scenario -> approval/PDF"
    )
    matrix_report = run_flow(
        stack.root,
        stack.client,
        "Odoo history functional acceptance",
        "Approve the saved lower exposure alternative.",
        "No purchase authorized in this separate functional test.",
        odoo_history=True,
    )
    matrix = json.loads(matrix_report.read_text())
    assert len(matrix["scenarios"]) == 6
    stack.evidence["checks"].append(
        "Odoo-history: all five stress types, infeasible demand, alternative approval and No-award"
    )
    stack.stop(stack.api)
    stack.compose("restart", "decision-db")
    stack.env.update(
        ODOO_BASE_URL="http://127.0.0.1:1",
        ODOO_API_KEY="",
        ODOO_HISTORY_API_KEY="",
        ODOO_HISTORY_QUOTATION_API_KEY="",
        ODOO_HISTORY_MODEL_DIRECTORY="",
        ODOO_HISTORY_DATABASE="",
    )
    stack.start_api(stored_only=True)
    wait_until(
        lambda: stack.client.get(BASE + "/" + case_id).status_code == 200,
        "stored helper cases after database/API restart",
    )
    verify_stored(matrix_report, stack.client)
    page.reload()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    replay = stack.client.get(BASE + "/" + case_id)
    assert replay.status_code == 200 and replay.json() == approved
    exact = stack.client.post(
        BASE + "/from-odoo-history", json=replay_payload, headers=replay_headers
    )
    assert exact.status_code == 200
    assert exact.json()["case_id"] == replay_base.json()["case_id"]
    assert exact.json()["snapshot_hash"] == replay_base.json()["snapshot_hash"]
    again = stack.client.get(BASE + f"/{case_id}/approved-pdf/{content_hash}")
    assert again.status_code == 200 and again.content == pdf.content
    library = stack.client.get(BASE, params={"workspace": "controlled"})
    assert library.status_code == 200 and any(
        row["case_id"] == case_id for row in library.json()["items"]
    )
    stack.evidence["checks"].append(
        "Database/API restart: scenarios/decisions, exact replay/library/PDF without upstream; "
        "owner Odoo never stopped"
    )
    stack.evidence["odoo_history"] = {
        "case_id": case_id,
        "snapshot_hash": saved["snapshot_hash"],
        "capture_hash": capture["capture_hash"],
        "origin": capture["evidence"]["origin"],
        "pdf_sha256": hashlib.sha256(pdf.content).hexdigest(),
    }
