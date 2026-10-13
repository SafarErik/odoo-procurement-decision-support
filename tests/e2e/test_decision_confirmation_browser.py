"""Real confirmation/cancel, separate No-award and exact pending finalization."""

import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_deliberate_decisions_cancel_reopen_child_and_recovery(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page

    def create():
        reply = stack.client.post(
            BASE,
            json=stack.payload | {"catalog_context": {"workspace": "practice"}},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert reply.status_code == 201, reply.text
        return reply.json()

    base, declined = create(), create()
    identity = base["case_id"]
    result = base["snapshot"]["result"]
    alternative = result["alternatives"][0]
    reply = stack.client.post(
        f"{BASE}/{identity}/scenarios",
        json={
            "kind": "demand_increase",
            "approved_quantity": 25,
            "suppliers": [],
            "source": {
                "source_type": "controlled_business_terms",
                "source_reference": "ux38",
                "observed_at": stack.payload["as_of"],
            },
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert reply.status_code == 201, reply.text
    child = reply.json()
    route = stack.frontend_url + f"/planning?case_id={identity}&view=plans"
    page.goto(route)
    page.get_by_role("button", name="Select Alternative 1 for review", exact=True).click()
    page.get_by_role("button", name="Review decision", exact=True).click()
    actor = "Buyer Árvíztűrő " * 10
    reason = "Review the saved exposure trade-off. " + "A" * 400
    page.get_by_label("Actor audit reference", exact=True).fill(actor)
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Review approval", exact=True).click()
    expect(page.locator("#final-reason")).to_be_focused()
    expect(page.get_by_role("alertdialog")).to_have_count(0)
    page.get_by_label("Reason", exact=True).fill(" ")
    page.get_by_role("button", name="Review approval", exact=True).click()
    expect(page.locator("#decision-error")).to_be_focused()
    assert stack.client.get(f"{BASE}/{identity}").json()["final_decision"] is None
    page.get_by_label("Reason", exact=True).fill(reason)
    page.get_by_role("button", name="Review approval", exact=True).click()
    dialog = page.get_by_role("alertdialog", name="Confirm approval", exact=True)
    expect(dialog).to_be_visible()
    expect(page.locator("#decision-confirm-cancel")).to_be_focused()
    expect(dialog).to_contain_text(f"{Decimal(alternative['total_cost']):,f} EUR")
    expect(dialog).to_contain_text(actor.strip())
    expect(dialog).to_contain_text(reason)
    expect(dialog).to_contain_text("Practice shares application storage")
    expect(dialog).to_contain_text("No Odoo order is created")
    expect(dialog).to_contain_text(stack.payload["requirement"]["required_date"])
    for row in alternative["allocations"]:
        if row["quantity"]:
            expect(dialog).to_contain_text(
                "Demo supplier " + row["supplier_id"].split("-")[-1] + f": {row['quantity']} piece"
            )
    for width in (1280, 1440, 768, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert dialog.evaluate("el => el.scrollWidth <= el.clientWidth")
        assert dialog.evaluate(
            "el => el.getBoundingClientRect().left >= 0 && "
            "el.getBoundingClientRect().right <= innerWidth"
        )
        assert page.locator("#decision-confirm-cancel").evaluate(
            "el => el.getBoundingClientRect().top >= 0 && "
            "el.getBoundingClientRect().bottom <= innerHeight"
        )
        page.screenshot(path=str(stack.root / f"decision-confirmation-{width}.png"))
    page.keyboard.press("Escape")
    expect(dialog).to_have_count(0)
    expect(page.locator("#decision-review-button")).to_be_focused()
    expect(page.get_by_label("Actor audit reference", exact=True)).to_have_value(actor)
    expect(page.get_by_label("Reason", exact=True)).to_have_value(reason)
    assert stack.client.get(f"{BASE}/{identity}").json()["final_decision"] is None
    page.get_by_role("button", name="Review approval", exact=True).click()
    page.get_by_role("button", name="Confirm approval", exact=True).dblclick()
    expect(page.locator("#saved-decision-heading")).to_be_focused()
    expect(page.get_by_role("button", name="Review approval", exact=True)).to_have_count(0)
    approved = stack.client.get(f"{BASE}/{identity}").json()
    assert approved["snapshot"] == base["snapshot"]
    decision = approved["final_decision"]
    assert decision["approved_content"]["selected_plan"] == alternative
    assert decision["intent"]["actor_reference"] == actor.strip()
    assert decision["intent"]["rationale"] == reason
    assert (stack.root / "api.log").read_text(encoding="utf-8").count(
        f'"POST {BASE}/{identity}/final-decision '
    ) == 1
    stack.stop(stack.api)
    stack.start_api(stored_only=True)
    page.reload()
    expect(page.get_by_text("Selected plan: Alternative 1", exact=True)).to_be_visible()
    expect(page.locator("body")).to_contain_text(
        datetime.fromisoformat(decision["audit"]["recorded_at"].replace("Z", "+00:00")).isoformat()
    )
    assert stack.client.get(f"{BASE}/{identity}").json()["final_decision"] == decision
    page.get_by_role("tab", name="Audit", exact=True).click()
    expect(page.locator("#saved-decision-heading")).to_have_count(1)
    expect(page.locator("#audit-decision-heading")).to_have_count(1)

    page.goto(stack.frontend_url + f"/planning?case_id={declined['case_id']}&view=plans")
    page.get_by_role("button", name="Record No-award", exact=True).click()
    page.get_by_label("Actor audit reference", exact=True).fill("declining buyer")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Review No-award", exact=True).click()
    expect(page.locator("#final-reason")).to_be_focused()
    page.get_by_label("Reason", exact=True).fill("Decline these controlled options.")
    page.get_by_role("button", name="Review No-award", exact=True).click()
    expect(page.get_by_role("alertdialog", name="Confirm No-award")).to_contain_text(
        "No allocation will be approved"
    )
    page.get_by_role("button", name="Cancel", exact=True).click()
    assert stack.client.get(f"{BASE}/{declined['case_id']}").json()["final_decision"] is None
    page.get_by_role("button", name="Review No-award", exact=True).click()
    route = page.url
    stack.stop(stack.api)
    page.get_by_role("button", name="Confirm No-award", exact=True).click()
    expect(page.get_by_role("button", name="Retry the same request", exact=True)).to_be_visible()
    expect(page.locator("#request-recovery-heading")).to_be_focused()
    record = page.get_by_label("Exact request recovery JSON", exact=True)
    pending = json.loads(record.input_value())
    assert pending["payload"]["outcome"] == "no_award"
    assert pending["payload"]["plan_index"] is None
    page.goto(stack.frontend_url + "/cases")
    expect(page).to_have_url(route)
    assert json.loads(record.input_value()) == pending
    stack.start_api(stored_only=True)
    page.get_by_role("button", name="Retry the same request", exact=True).click()
    expect(page.locator("#saved-decision-heading")).to_be_focused()
    expect(page.get_by_role("button", name="View approved PDF", exact=True)).to_have_count(0)
    saved_decline = stack.client.get(f"{BASE}/{declined['case_id']}").json()
    assert saved_decline["snapshot"] == declined["snapshot"]
    assert saved_decline["final_decision"]["approved_content"] is None
    assert saved_decline["final_decision"]["idempotency_key"] == pending["key"]
    page.reload()
    expect(page.get_by_role("heading", name="No-award", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Record No-award", exact=True)).to_have_count(0)
    page.goto(stack.frontend_url + f"/planning?case_id={child['case_id']}&view=plans")
    expect(page.locator("body")).to_contain_text("Stress scenarios remain analytical")
    expect(page.get_by_role("button", name="Review approval", exact=True)).to_have_count(0)
    expect(page.get_by_role("button", name="Record No-award", exact=True)).to_have_count(0)
    rejected = stack.client.post(
        f"{BASE}/{child['case_id']}/final-decision",
        json=pending["payload"] | {"snapshot_hash": child["snapshot_hash"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert rejected.status_code == 422 and "scenario_finalization_forbidden" in rejected.text
    assert stack.client.get(f"{BASE}/{child['case_id']}").json()["final_decision"] is None
    stack.evidence["checks"].append(
        "Real alternative review/validation/Escape/cancel/single-save double-click, long/narrow "
        "exact confirmation, immutable reopening/Audit, separate reasoned No-award with actual "
        "API-outage exact pending recovery, no No-award PDF and UI/API child rejection PASS"
    )
    stack.evidence["outcome"] = "PASS"
