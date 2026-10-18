"""Real scenario uncertainty and competing finalization; no HTTP stubs."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_comparison_recovery_saves_once_without_approval(smoke_stack, smoke_page):
    from playwright.sync_api import expect
    from sqlalchemy import create_engine, text

    stack, page = smoke_stack, smoke_page
    engine = create_engine(stack.env["DECISION_DATABASE_URL"])

    def counts():
        with engine.connect() as connection:
            return tuple(
                connection.execute(text("SELECT count(*) FROM " + table)).scalar_one()
                for table in ("planning_cases", "planning_final_decisions", "planning_documents")
            )

    try:
        page.goto(stack.frontend_url + "/planning")
        expect(page.get_by_text("Unsaved draft", exact=True)).to_be_visible()
        page.get_by_role("tab", name="Demo", exact=True).click()
        page.get_by_role("button", name="Load demo inputs", exact=True).click()
        page.get_by_role("button", name="Review demo terms", exact=True).click()
        assert counts() == (0, 0, 0)
        stack.stop(stack.api)
        page.get_by_role("button", name="Calculate and save comparison", exact=True).click()
        expect(
            page.get_by_role("button", name="Retry the same request", exact=True)
        ).to_be_visible()
        expect(page.locator("body")).to_contain_text("Approval is not a recovery step.")
        expect(
            page.get_by_text("Save response unconfirmed — recover the same request", exact=True)
        ).to_be_visible()
        expect(page.locator("body")).to_contain_text(
            "it does not delete comparisons already saved in the database"
        )
        pending = json.loads(page.get_by_label("Exact request recovery JSON").input_value())
        for width in (1280, 320):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(
                path=str(stack.root / f"comparison-pending-{width}.png"), full_page=True
            )
        page.set_viewport_size({"width": 1280, "height": 900})
        stack.start_api()
        page.get_by_role("button", name="Retry the same request", exact=True).click()
        expect(page.get_by_text("Comparison saved. Approval is a separate choice.")).to_be_visible()
        expect(
            page.get_by_text("Saved comparison — awaiting a decision", exact=True)
        ).to_be_visible()
        expect(page.locator("#saved-case-heading")).to_be_focused()
        assert counts() == (1, 0, 0)
        replay = stack.client.post(
            pending["url"], json=pending["payload"], headers={"Idempotency-Key": pending["key"]}
        )
        assert replay.status_code == 200 and replay.json()["idempotent_replay"]
        saved = replay.json()
        assert saved["final_decision"] is None and counts() == (1, 0, 0)
        page.get_by_role("button", name="Select Alternative 1 for review", exact=True).click()
        expect(page.get_by_text("Selected plan — not yet approved", exact=True)).to_be_visible()
        page.get_by_role("button", name="Review selected plan", exact=True).click()
        assert counts() == (1, 0, 0)
        page.screenshot(path=str(stack.root / "comparison-recovered-selected.png"), full_page=True)
        page.reload()
        expect(
            page.get_by_role("heading", name="Record the final decision", exact=True)
        ).to_be_visible()
        assert stack.client.get(f"{BASE}/{saved['case_id']}").json() == saved | {
            "idempotent_replay": False
        }
        assert counts() == (1, 0, 0)
        stack.evidence["checks"].append(
            "Real API outage; exact comparison replay saves one case, zero final decisions and "
            "zero documents. Selection/review/reopening require no approval."
        )
        stack.evidence["outcome"] = "PASS"
    finally:
        engine.dispose()


def test_pending_scenario_and_finalized_conflict_reopen_only(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    request = deepcopy(stack.payload)
    request["suppliers"][0]["supplier_id"] = "Árvíztűrő 供应商 " + "LongSupplier" * 14
    reply = stack.client.post(
        BASE,
        json=request,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert reply.status_code == 201
    original = reply.json()
    identity = original["case_id"]
    stack.stop(stack.api)
    stack.start_api(stored_only=True)
    route = stack.frontend_url + f"/planning?case_id={identity}&view=whatif"
    page.goto(route)
    page.get_by_label("Scenario type").select_option("capacity_change")
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
    children = stack.client.get(f"{BASE}/{identity}/scenarios", params={"origin": "all"})
    assert [row["case_id"] for row in children.json()["items"]] == [child["case_id"]]
    assert stack.client.get(f"{BASE}/{identity}").json() == original

    page.goto(stack.frontend_url + f"/planning?case_id={identity}&view=plans")
    page.get_by_role("button", name="Select Alternative 1 for review").click()
    page.get_by_role("button", name="Review selected plan", exact=True).click()
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
    page.get_by_role("button", name="Approve plan", exact=True).click()
    expect(page.get_by_role("heading", name="Reopen the recorded decision")).to_be_visible()
    expect(page.locator("#request-recovery-heading")).to_be_focused()
    expect(page.locator("body")).to_contain_text("another approval attempt cannot replace it")
    expect(page.get_by_role("button", name="Review approval")).to_have_count(0)
    expect(page.get_by_role("button", name="Retry the same request")).to_have_count(0)
    conflict_record = recovery.input_value()
    expect(
        page.get_by_text("Decision conflict — reopen the saved comparison", exact=True)
    ).to_be_visible()
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
