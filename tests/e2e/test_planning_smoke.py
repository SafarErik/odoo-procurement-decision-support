"""Buyer flow and genuine server-side backend outage, without mocked HTTP."""

import hashlib
import json
import re
from uuid import UUID

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]


def test_buyer_flow_and_backend_recovery(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    page.goto(stack.frontend_url + "/planning")
    page.get_by_role("tab", name="Demo", exact=True).click()
    page.get_by_role("button", name="Load demo inputs", exact=True).click()
    expect(page.get_by_label("Demand quantity", exact=True)).to_have_value("10")
    page.get_by_role("button", name="Review demo terms", exact=True).click()
    page.get_by_role("button", name="Create and save plan", exact=True).click()
    expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name="Alternative 1", exact=True)).to_be_visible()
    expect(page.get_by_role("status").filter(has_text="Case saved.")).to_be_visible()
    ids = re.findall(
        r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", page.locator("body").inner_text()
    )
    case_id = str(UUID(ids[0]))
    response = stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}")
    assert response.status_code == 200
    created = response.json()
    result = created["snapshot"]["result"]
    assert created["parent_id"] is None and result["status"] == "optimal"
    assert result["minimum_cost_plan"]["total_cost"] == "102"
    for index, plan in enumerate([result["minimum_cost_plan"], *result["alternatives"]]):
        comparison = page.get_by_role("region", name="Aligned saved plan comparison")
        cost_row = comparison.get_by_role("row").filter(
            has=page.get_by_role("rowheader", name="Total cost", exact=True)
        )
        expect(cost_row.get_by_role("cell").nth(index)).to_have_text(f"{plan['total_cost']} EUR")
        for row in plan["allocations"]:
            supplier = "Demo supplier " + row["supplier_id"].removeprefix("synthetic-")
            allocation = comparison.get_by_role("row").filter(
                has=page.get_by_role("rowheader").filter(has_text=supplier)
            )
            expect(allocation.get_by_role("cell").nth(index)).to_have_text(
                f"{row['quantity']} piece"
            )
        assert sum(row["quantity"] for row in plan["allocations"]) == 10
    stack.evidence["checks"].append(
        "Created base; both saved costs and supplier quantities match API"
    )
    page.get_by_role("button", name="Select Alternative 1 for review", exact=True).click()
    page.get_by_role("button", name="Review decision", exact=True).click()
    expect(page.locator("#final-decision-heading")).to_be_focused()
    page.get_by_label("Actor audit reference", exact=True).fill("t18-browser-buyer")
    page.get_by_label("Reason", exact=True).fill(
        "Accept the saved cost premium for lower synthetic exposure."
    )
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Finalize this base", exact=True).click()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    expect(page.get_by_text("Selected plan: Alternative 1", exact=True)).to_be_visible()
    approved = stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}").json()
    assert approved["snapshot"] == created["snapshot"]
    decision = approved["final_decision"]
    assert decision["intent"]["outcome"] == "approve"
    assert decision["intent"]["actor_reference"] == "t18-browser-buyer"
    assert decision["approved_content"]["selected_plan"] == result["alternatives"][0]
    stack.evidence["checks"].append("Explicit alternative approval and unchanged original snapshot")
    stack.stop(stack.api)
    stack.start_api(stored_only=True)
    page.reload()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    page.get_by_text("Open or create a comparison", exact=True).click()
    page.get_by_label("Case ID", exact=True).fill(case_id)
    page.get_by_role("button", name="Load stored case", exact=True).click()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    assert stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}").json() == approved
    stack.stop(stack.api)
    page.get_by_role("button", name="View approved PDF", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("PDF unavailable. Approval remains saved.")
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="Download approved PDF", exact=True)).to_have_count(0)
    stack.start_api(stored_only=True)
    page.get_by_role("button", name="View approved PDF", exact=True).click()
    expect(page.get_by_role("status").filter(has_text="The PDF is ready.")).to_be_visible()
    region = page.get_by_role("region", name="Approved procurement PDF", exact=True)
    expect(region.locator("canvas").first).to_be_visible()
    expect(region).to_contain_text("t18-browser-buyer")
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Download approved PDF", exact=True).click()
    download = download_info.value
    download.save_as(stack.root / "approved.pdf")
    data = (stack.root / "approved.pdf").read_bytes()
    pdf = stack.client.get(
        f"/api/v2/procurement/planning-cases/{case_id}/approved-pdf/{decision['approved_content_hash']}"
    )
    assert pdf.status_code == 200 and data == pdf.content
    assert hashlib.sha256(data).hexdigest() == pdf.headers["x-pdf-sha256"]
    page.screenshot(path=str(stack.root / "approved-pdf.png"), full_page=True)
    stack.evidence["checks"].append(
        "Model-unconfigured stored reopening; PDF outage alert and explicit recovery; "
        "rendered/downloaded exact PDF"
    )

    stack.stop(stack.api)
    page.get_by_text("Open or create a comparison", exact=True).click()
    page.get_by_role("button", name="Load stored case", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Planning data is unavailable")
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_have_count(0)
    stack.start_api()
    page.get_by_role("button", name="Load stored case", exact=True).click()
    expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
    assert stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}").json() == approved
    stack.evidence["checks"].append(
        "Actual FastAPI outage; visible GET error and explicit identical recovery"
    )

    page.get_by_text("Open or create a comparison", exact=True).click()
    page.get_by_role("tab", name="Demo", exact=True).click()
    page.get_by_role("button", name="Load demo inputs", exact=True).click()
    pending_route = page.url
    stack.stop(stack.api)
    page.get_by_role("button", name="Review demo terms", exact=True).click()
    page.get_by_role("button", name="Create and save plan", exact=True).click()
    expect(page.get_by_role("button", name="Retry the same request", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Create and save plan", exact=True)).to_be_disabled()
    expect(page.get_by_role("alert")).to_contain_text("The outcome is unconfirmed")
    recovery = page.get_by_label("Exact request recovery JSON", exact=True)
    pending = json.loads(recovery.input_value())
    for destination in ("/cases", f"/planning?case_id={case_id}&view=audit"):
        page.goto(stack.frontend_url + destination)
        expect(
            page.get_by_role("button", name="Retry the same request", exact=True)
        ).to_be_visible()
        expect(page).to_have_url(pending_route)
        assert json.loads(recovery.input_value()) == pending
    stack.evidence["checks"].append(
        "Pending create survived Cases and another-case bookmark navigation with exact key/payload"
    )
    page.screenshot(path=str(stack.root / "pending-save.png"), full_page=True)
    stack.start_api()
    assert json.loads(recovery.input_value()) == pending
    page.get_by_role("button", name="Retry the same request", exact=True).click()
    expect(page.get_by_role("button", name="Retry the same request", exact=True)).to_have_count(0)
    expect(
        page.get_by_role("heading", name="Record the final decision", exact=True)
    ).to_be_visible()
    replay = stack.client.post(
        pending["url"], json=pending["payload"], headers={"Idempotency-Key": pending["key"]}
    )
    assert replay.status_code == 200 and replay.json()["idempotent_replay"]
    expect(page.get_by_text("Saved case " + replay.json()["case_id"], exact=True)).to_be_visible()
    stack.evidence["checks"].append(
        "Actual FastAPI outage; exact pending payload/key and explicit idempotent recovery"
    )
    stack.evidence.update(
        case_id=case_id,
        approved_content_hash=decision["approved_content_hash"],
        pdf_sha256=hashlib.sha256(data).hexdigest(),
        recovery_key=pending["key"],
        recovery_case_id=replay.json()["case_id"],
        outcome="PASS",
    )
