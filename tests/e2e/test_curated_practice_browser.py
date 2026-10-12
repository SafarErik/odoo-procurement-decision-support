"""#33 deliberate fresh exercises, genuine scenarios, stored classification and PDF."""

import hashlib
import json
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import create_engine, text

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_curated_practice_real_saved_workflow(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    engine = create_engine(stack.env["DECISION_DATABASE_URL"])

    def counts():
        with engine.connect() as connection:
            return tuple(
                connection.execute(text("SELECT count(*) FROM " + table)).scalar_one()
                for table in ("planning_cases", "planning_case_catalog")
            )

    try:
        page.goto(stack.frontend_url + "/practice")
        expect(page.get_by_role("heading", name="Practice", exact=True)).to_be_visible()
        assert counts() == (0, 0)
        for name in (
            "Choose compare plans",
            "Choose test a supplier outage",
            "Choose make a case infeasible",
        ):
            page.get_by_role("button", name=name, exact=True).click()
            expect(page.get_by_role("heading", name="Fresh Practice draft")).to_be_visible()
            expect(
                page.get_by_role("button", name="Calculate and save fresh Practice case")
            ).to_be_enabled()
            assert counts() == (0, 0)
        for width in (1280, 1440, 768, 390, 320):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(stack.root / f"practice-{width}.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        cases = {}
        for example, button in (
            ("compare-plans", "Choose compare plans"),
            ("supplier-outage", "Choose test a supplier outage"),
            ("infeasible-demand", "Choose make a case infeasible"),
        ):
            page.goto(stack.frontend_url + "/practice")
            before = counts()
            page.get_by_role("button", name=button, exact=True).focus()
            page.keyboard.press("Enter")
            expect(
                page.get_by_role("button", name="Calculate and save fresh Practice case")
            ).to_be_visible()
            assert counts() == before
            page.get_by_role("button", name="Calculate and save fresh Practice case").click()
            expect(page.get_by_role("button", name="Open saved Practice case")).to_be_visible()
            assert counts() == (before[0] + 1, before[1] + 1)
            page.get_by_role("button", name="Open saved Practice case").click()
            expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
            identity = parse_qs(urlsplit(page.url).query)["case_id"][0]
            base = stack.client.get(f"{BASE}/{identity}").json()
            cases[example] = base
            assert base["workspace"] == "practice" and base["example_id"] == example
            assert base["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] == "102"
            expect(page.get_by_text("Saved case " + identity, exact=True)).to_be_visible()
            expect(page.locator("body")).to_contain_text("Workspace: Practice")
            if example == "compare-plans":
                page.get_by_label("Plan or No-award", exact=True).select_option("Alternative 1")
                page.get_by_label("Actor audit reference", exact=True).fill("ux33-practice-buyer")
                page.get_by_label("Reason", exact=True).fill(
                    "Compare the saved synthetic trade-off."
                )
                page.get_by_role("checkbox").check()
                page.get_by_role("button", name="Finalize this base", exact=True).click()
                expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
                expect(page.locator("body")).to_contain_text("Practice document access")
            else:
                page.get_by_role("button", name="Prepare exercise scenario", exact=True).click()
                expect(page.get_by_role("tab", name="What-if", exact=True)).to_have_attribute(
                    "data-state", "active"
                )
                assert counts() == (before[0] + 1, before[1] + 1)
                page.get_by_role("button", name="Create and save scenario", exact=True).click()
                expect(page.get_by_role("status").filter(has_text="Case saved.")).to_be_visible()
                children = stack.client.get(
                    f"{BASE}/{identity}/scenarios", params={"workspace": "practice"}
                ).json()["items"]
                assert len(children) == 1 and children[0]["workspace"] == "practice"
                if example == "infeasible-demand":
                    assert children[0]["planning_status"] == "infeasible"
                    expect(page.locator("body")).to_contain_text("No feasible plan")
                else:
                    assert children[0]["scenario_kind"] == "supplier_outage"
                    assert children[0]["planning_status"] == "optimal"
                assert counts()[1] == 3 if example == "infeasible-demand" else counts()[1] == 2
        assert len({case["case_id"] for case in cases.values()}) == 3
        stack.stop(stack.api)
        stack.start_api(stored_only=True)
        page.goto(stack.frontend_url + "/cases")
        expect(page.get_by_role("heading", name="Saved cases", exact=True)).to_be_visible()
        page.get_by_label("Workspace", exact=True).select_option("practice")
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("button", name="Open case", exact=True)).to_have_count(3)
        approved = cases["compare-plans"]
        page.get_by_label("Product or case ID", exact=True).fill(approved["case_id"])
        page.get_by_role("button", name="Refresh", exact=True).click()
        expect(page.get_by_role("button", name="Open case", exact=True)).to_have_count(1)
        page.get_by_role("button", name="Open case", exact=True).click()
        expect(page.get_by_role("heading", name="Approved", exact=True)).to_be_visible()
        expect(page.locator("body")).to_contain_text("Workspace: Practice")
        reopened = stack.client.get(f"{BASE}/{approved['case_id']}").json()
        assert reopened["snapshot_hash"] == approved["snapshot_hash"]
        page.get_by_role("button", name="View approved PDF", exact=True).click()
        region = page.get_by_role("region", name="Approved procurement PDF", exact=True)
        expect(region.locator("canvas").first).to_be_visible()
        with page.expect_download() as download_info:
            page.get_by_role("link", name="Download approved PDF", exact=True).click()
        download_info.value.save_as(stack.root / "practice-approved.pdf")
        document = stack.client.get(
            f"{BASE}/{approved['case_id']}/approved-pdf/{reopened['final_decision']['approved_content_hash']}"
        )
        assert (stack.root / "practice-approved.pdf").read_bytes() == document.content
        assert hashlib.sha256(document.content).hexdigest() == document.headers["x-pdf-sha256"]
        page.goto(stack.frontend_url + "/practice")
        page.get_by_role("button", name="Choose compare plans", exact=True).click()
        expect(
            page.get_by_role("button", name="Calculate and save fresh Practice case")
        ).to_be_visible()
        assert counts() == (5, 3)
        stack.stop(stack.api)
        page.get_by_role("button", name="Calculate and save fresh Practice case").click()
        expect(page.get_by_role("button", name="Retry the same request")).to_be_visible()
        pending = json.loads(page.get_by_label("Exact request recovery JSON").input_value())
        assert pending["payload"]["catalog_context"] == {
            "workspace": "practice",
            "example_id": "compare-plans",
        }
        expect(
            page.get_by_role("button", name="Choose test a supplier outage", exact=True)
        ).to_be_disabled()
        page.goto(stack.frontend_url + "/cases")
        expect(page).to_have_url(stack.frontend_url + "/practice")
        assert json.loads(page.get_by_label("Exact request recovery JSON").input_value()) == pending
        stack.start_api()
        page.get_by_role("button", name="Retry the same request").click()
        expect(page.get_by_role("button", name="Open saved Practice case")).to_be_visible()
        replay = stack.client.post(
            pending["url"], json=pending["payload"], headers={"Idempotency-Key": pending["key"]}
        )
        assert replay.status_code == 200 and replay.json()["idempotent_replay"]
        assert replay.json()["case_id"] != approved["case_id"] and counts() == (6, 4)
        stack.evidence["checks"].append(
            "Three entry tasks write nothing; three fresh classified bases, outage/infeasibility "
            "children, keyboard/narrow entry, stored-only Practice library/approval/PDF "
            "and exact pending recovery PASS"
        )
        stack.evidence["outcome"] = "PASS"
    finally:
        engine.dispose()
