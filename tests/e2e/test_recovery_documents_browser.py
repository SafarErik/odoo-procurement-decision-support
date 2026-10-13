"""Real scenario uncertainty and competing finalization; no HTTP stubs."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_pending_scenario_and_finalized_conflict_reopen_only(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    request = deepcopy(stack.payload)
    request["suppliers"][0]["supplier_id"] = "Árvíztűrő 供应商 " + "LongSupplier" * 14
    reply = stack.client.post(
        BASE,
        json=request | {"catalog_context": {"workspace": "practice"}},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert reply.status_code == 201
    original = reply.json()
    identity = original["case_id"]
    stack.stop(stack.api)
    stack.start_api(stored_only=True)
    route = stack.frontend_url + f"/planning?case_id={identity}&view=whatif"
    page.goto(route)
    page.get_by_label("Scenario type").select_option("capacity_reduction")
    supplier = request["suppliers"][0]["supplier_id"]
    page.get_by_label("Supplier to change (original terms)").select_option(supplier)
    page.get_by_label("New capacity limit").fill("4")
    stack.stop(stack.api)
    page.get_by_role("button", name="Create and save scenario").click()
    expect(page.get_by_role("button", name="Retry the same request")).to_be_visible()
    recovery = page.get_by_label("Exact request recovery JSON")
    pending = json.loads(recovery.input_value())
    assert pending["url"].endswith(f"/{identity}/scenarios")
    expect(page.get_by_role("button", name="Cases", exact=True)).to_be_disabled()
    expect(page).to_have_url(route)
    page.goto(stack.frontend_url + "/cases")
    expect(page).to_have_url(route)
    assert json.loads(recovery.input_value()) == pending
    expect(page.get_by_role("button", name="Create and save scenario")).to_be_disabled()
    page.screenshot(path=str(stack.root / "uncertain-scenario.png"))
    stack.start_api(stored_only=True)
    page.get_by_role("button", name="Retry the same request").click()
    expect(page.locator("#scenario-result-heading")).to_be_focused()
    replay = stack.client.post(
        pending["url"], json=pending["payload"], headers={"Idempotency-Key": pending["key"]}
    )
    assert replay.status_code == 200 and replay.json()["idempotent_replay"]
    child = replay.json()
    assert child["parent_id"] == identity
    children = stack.client.get(f"{BASE}/{identity}/scenarios", params={"workspace": "practice"})
    assert [row["case_id"] for row in children.json()["items"]] == [child["case_id"]]
    assert stack.client.get(f"{BASE}/{identity}").json() == original

    page.goto(stack.frontend_url + f"/planning?case_id={identity}&view=plans")
    page.get_by_role("button", name="Select Alternative 1 for review").click()
    page.get_by_role("button", name="Review decision", exact=True).click()
    page.get_by_label("Actor audit reference").fill("browser buyer")
    page.get_by_label("Reason", exact=True).fill("Prefer the alternative")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Review approval").click()
    other = {
        "snapshot_hash": original["snapshot_hash"],
        "outcome": "approve",
        "plan_index": 0,
        "actor_reference": "competing buyer",
        "rationale": None,
        "demonstration_acknowledged": True,
    }
    reply = stack.client.post(
        f"{BASE}/{identity}/final-decision", json=other, headers={"Idempotency-Key": str(uuid4())}
    )
    assert reply.status_code == 201
    approved = reply.json()
    page.get_by_role("button", name="Confirm approval", exact=True).click()
    expect(page.get_by_role("heading", name="Reopen the recorded decision")).to_be_visible()
    expect(page.locator("#request-recovery-heading")).to_be_focused()
    expect(page.locator("body")).to_contain_text("another approval attempt cannot replace it")
    expect(page.get_by_role("button", name="Review approval")).to_have_count(0)
    expect(page.get_by_role("button", name="Retry the same request")).to_have_count(0)
    conflict_record = recovery.input_value()
    for width in (1280, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(stack.root / f"decision-conflict-{width}.png"))
    stack.stop(stack.api)
    page.get_by_role("button", name="Reopen saved decision").click()
    expect(page.get_by_role("button", name="Reopen saved decision")).to_be_visible()
    assert recovery.input_value() == conflict_record
    expect(page.get_by_role("button", name="Review approval")).to_have_count(0)
    stack.start_api(stored_only=True)
    page.get_by_role("button", name="Reopen saved decision").click()
    expect(page.locator("#saved-decision-heading")).to_be_focused()
    expect(page.get_by_text("Selected plan: Minimum cost", exact=True)).to_be_visible()
    expect(page.locator("body")).to_contain_text("competing buyer")
    assert stack.client.get(f"{BASE}/{identity}").json() == approved
    log = (stack.root / "api.log").read_text(encoding="utf-8")
    assert log.count(f"POST {BASE}/{identity}/final-decision") == 2
    stack.evidence.update(outcome="PASS", case_id=identity, scenario_id=child["case_id"])
    stack.evidence["checks"].append(
        "Actual scenario outage preserved payload/key across navigation; one stored child; "
        "real competing HTTP 409 paused approval; failed GET kept context/proof; explicit "
        "stored-only GET reopened the other immutable decision with no additional POST."
    )
