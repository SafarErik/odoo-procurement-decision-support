"""Compare actual saved 3/5/10-supplier plans; selections never finalize a case."""

import json
from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from frontend.planning_client import _supplier_label
from tools.t15_demo import prepare_assets

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_exact_comparison_selection_reflow_and_zoom(smoke_stack, smoke_page, playwright):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    payload = prepare_assets(stack.root / ".artifacts/t15-demo/model", supplier_count=10)
    cases = []
    for count, epsilons in ((3, ["0"]), (5, ["0.05", "0.1", "0.2"]), (10, ["0.1"])):
        request = deepcopy(payload)
        request["suppliers"] = request["suppliers"][:count]
        request["policy"]["epsilons"] = epsilons
        request["catalog_context"] = {"workspace": "practice"}
        if count == 10:
            request["suppliers"][0]["supplier_id"] = (
                "Árvíztűrő 供应商 " + "Long supplier name " * 8
            ).strip()
        response = stack.client.post(BASE, json=request, headers={"Idempotency-Key": str(uuid4())})
        assert response.status_code == 201, response.text
        cases.append(response.json())
    impossible = deepcopy(payload)
    impossible["requirement"]["approved_quantity"] = 1000
    response = stack.client.post(BASE, json=impossible, headers={"Idempotency-Key": str(uuid4())})
    assert response.status_code == 201, response.text
    infeasible = response.json()
    stack.stop(stack.api)
    stack.start_api(stored_only=True)
    engine = create_engine(stack.env["DECISION_DATABASE_URL"])

    def counts():
        with engine.connect() as connection:
            return tuple(
                connection.execute(text("SELECT count(*) FROM " + table)).scalar_one()
                for table in ("planning_cases", "planning_final_decisions")
            )

    try:
        for case in cases:
            identity = case["case_id"]
            supplier_count = len(case["snapshot"]["request"]["suppliers"])
            page.set_viewport_size({"width": 1440, "height": 900})
            page.goto(stack.frontend_url + f"/planning?case_id={identity}&view=plans")
            expect(page.get_by_role("heading", name="Your allocation options")).to_be_visible()
            summary = page.get_by_role("region", name="Selected plan and next step")
            expect(summary).to_contain_text("Select a saved plan explicitly")
            expect(
                page.get_by_role("button", name="Review selected plan", exact=True)
            ).to_be_disabled()
            result = case["snapshot"]["result"]
            plans = [result["minimum_cost_plan"], *result["alternatives"]]
            labels = ["Minimum cost", *[f"Alternative {i}" for i in range(1, len(plans))]]
            aligned = page.get_by_role("region", name="Aligned saved plan comparison")
            cost_row = aligned.get_by_role("row").filter(
                has=page.get_by_role("rowheader", name="Total cost", exact=True)
            )
            assert cost_row.get_by_role("cell").all_text_contents() == [
                f"{Decimal(p['total_cost']):,f} EUR" for p in plans
            ]
            exposure_row = aligned.get_by_role("row").filter(
                has=page.get_by_role("rowheader", name="Synthetic model exposure", exact=True)
            )
            for cell, plan in zip(exposure_row.get_by_role("cell").all(), plans, strict=True):
                fraction = plan["risk_exposure"]
                expect(cell).to_contain_text(f"{fraction['numerator']}/{fraction['denominator']}")
            for supplier in case["snapshot"]["request"]["suppliers"]:
                name = _supplier_label(supplier["supplier_id"])
                row = aligned.get_by_role("row").filter(
                    has=page.get_by_role("rowheader").filter(has_text=name)
                )
                expected = [
                    next(
                        a["quantity"]
                        for a in p["allocations"]
                        if a["supplier_id"] == supplier["supplier_id"]
                    )
                    for p in plans
                ]
                assert row.get_by_role("cell").all_text_contents() == [
                    f"{q} piece" for q in expected
                ]
            before = counts()
            page.get_by_text("Cost–exposure chart and exact values", exact=True).click()
            chart_values = page.get_by_role("region", name="Saved plan chart values")
            for plan in plans:
                fraction = plan["risk_exposure"]
                expect(chart_values).to_contain_text(
                    f"{fraction['numerator']}/{fraction['denominator']}"
                )
                expect(chart_values).to_contain_text(f"{Decimal(plan['total_cost']):,f} EUR")
            page.get_by_text("Cost–exposure chart and exact values", exact=True).click()
            for label, plan in zip(labels, plans, strict=True):
                button = page.get_by_role("button", name=f"Select {label} for review", exact=True)
                button.focus()
                page.keyboard.press("Enter")
                expect(button).to_have_attribute("aria-pressed", "true")
                expect(summary).to_contain_text(f"{Decimal(plan['total_cost']):,f} EUR")
                for allocation in plan["allocations"]:
                    if allocation["quantity"]:
                        expect(summary).to_contain_text(
                            f"{_supplier_label(allocation['supplier_id'])}: "
                            f"{allocation['quantity']} piece"
                        )
                expect(page.get_by_label("Saved plan for approval", exact=True)).to_have_value(
                    label
                )
                page.get_by_role("button", name="Review selected plan", exact=True).click()
                expect(page.locator("#final-decision-heading")).to_be_focused()
                assert counts() == before
            if len(plans) == 1:
                expect(page.locator("body")).to_contain_text("No distinct alternative was found")
            for width in (1280, 1440, 768, 390, 320):
                page.set_viewport_size({"width": width, "height": 900})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                button = page.get_by_role(
                    "button", name=f"Select {labels[-1]} for review", exact=True
                )
                expect(button).to_have_attribute("aria-pressed", "true")
                button.focus()
                page.keyboard.press("Enter")
                page.screenshot(
                    path=str(stack.root / f"comparison-{supplier_count}-{width}.png"),
                    full_page=True,
                )
            page.get_by_role("tab", name="Suppliers", exact=True).click()
            expect(summary).to_contain_text(labels[-1])
            page.get_by_role("button", name="Review selected plan", exact=True).click()
            expect(page.locator("#final-decision-heading")).to_be_focused()
            assert counts() == before
            assert stack.client.get(f"{BASE}/{identity}").json() == case

        page.goto(stack.frontend_url + f"/planning?case_id={infeasible['case_id']}&view=plans")
        expect(page.get_by_text("No feasible plan", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Select Minimum cost for review")).to_have_count(0)
        expect(page.get_by_role("button", name="Review selected plan", exact=True)).to_be_disabled()
        assert infeasible["snapshot"]["result"]["minimum_cost_plan"] is None

        # Native browser zoom, in an owned temporary profile/extension only.
        extension = stack.root / "comparison-zoom-extension"
        extension.mkdir()
        (extension / "manifest.json").write_text(
            json.dumps(
                {
                    "manifest_version": 3,
                    "name": "Comparison zoom check",
                    "version": "1.0",
                    "permissions": ["tabs"],
                    "background": {"service_worker": "background.js"},
                }
            ),
            encoding="utf-8",
        )
        (extension / "background.js").write_text(
            "chrome.runtime.onInstalled.addListener(() => {});", encoding="utf-8"
        )
        context = playwright.chromium.launch_persistent_context(
            str(stack.root / "comparison-zoom-profile"),
            channel="chromium",
            headless=True,
            args=[f"--disable-extensions-except={extension}", f"--load-extension={extension}"],
            viewport={"width": 1280, "height": 900},
        )
        try:
            worker = (
                context.service_workers[0]
                if context.service_workers
                else context.wait_for_event("serviceworker")
            )
            zoom_page = context.new_page()
            zoom_page.goto(
                stack.frontend_url + f"/planning?case_id={cases[-1]['case_id']}&view=plans"
            )
            expect(zoom_page.get_by_role("heading", name="Your allocation options")).to_be_visible()
            factor = worker.evaluate("""async () => {
                const [tab] = await chrome.tabs.query({url:'http://127.0.0.1/*'});
                await chrome.tabs.setZoom(tab.id, 2);
                return chrome.tabs.getZoom(tab.id);
            }""")
            assert factor == 2
            zoom_page.wait_for_function("window.devicePixelRatio === 2 && window.innerWidth <= 640")
            assert zoom_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            zoom_page.get_by_role(
                "button", name="Select Alternative 1 for review", exact=True
            ).click()
            zoom_page.get_by_role("button", name="Review selected plan", exact=True).click()
            expect(zoom_page.locator("#final-decision-heading")).to_be_focused()
            zoom_page.screenshot(
                path=str(stack.root / "comparison-200-percent.png"), full_page=True
            )
            stack.evidence["native_browser_zoom"] = factor
        finally:
            context.close()
        page.goto(stack.frontend_url + f"/planning?case_id={cases[0]['case_id']}&view=plans")
        page.get_by_role("button", name="Record No-award", exact=True).click()
        expect(page.get_by_role("region", name="Selected plan and next step")).to_contain_text(
            "No-award: no allocation is selected"
        )
        page.get_by_role("button", name="Review No-award decision", exact=True).click()
        page.get_by_label("Actor audit reference", exact=True).fill("comparison keyboard test")
        page.get_by_label("Reason", exact=True).fill("Decline this controlled demonstration.")
        page.get_by_role("checkbox").check()
        page.get_by_role("button", name="Review No-award", exact=True).focus()
        page.keyboard.press("Enter")
        page.get_by_role("button", name="Confirm No-award", exact=True).click()
        expect(page.get_by_role("heading", name="No-award", exact=True)).to_be_visible()
        final = stack.client.get(f"{BASE}/{cases[0]['case_id']}").json()
        assert final["final_decision"]["intent"]["outcome"] == "no_award"
        assert final["final_decision"]["approved_content"] is None
        stack.evidence["checks"].append(
            "Actual 3/5/10-supplier saved results, variable alternatives, exact costs/quantities, "
            "long non-Latin labels, explicit read-only selection across views, keyboard review "
            "focus, 1280/1440/768/390/320 and native 200% zoom PASS; model unconfigured on GET"
        )
        stack.evidence["outcome"] = "PASS"
    finally:
        engine.dispose()
