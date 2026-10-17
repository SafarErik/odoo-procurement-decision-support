"""All five genuine saved disturbances, original retention and exact recovery."""

import json
import os
import sys
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest

from tests.e2e.conftest import wait_until

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_original_base_all_types_infeasibility_and_recovery(smoke_stack, smoke_page, browser):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    response = stack.client.post(
        BASE,
        json=stack.payload,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 201, response.text
    base = response.json()
    identity = base["case_id"]
    supplier = stack.payload["suppliers"][0]["supplier_id"]
    stack.stop(stack.api)
    stack.start_api(stored_only=True)

    def children():
        reply = stack.client.get(f"{BASE}/{identity}/scenarios", params={"origin": "all"})
        assert reply.status_code == 200, reply.text
        return reply.json()["items"]

    def cost_row(target):
        return (
            target.get_by_role("region", name="Exact original-base and scenario comparison")
            .get_by_role("row")
            .filter(has=target.get_by_role("rowheader", name="Minimum total cost", exact=True))
        )

    page.goto(stack.frontend_url + f"/planning?case_id={identity}&view=whatif")
    expect(page.get_by_role("heading", name="Original base before disruption")).to_be_visible()
    expect(cost_row(page).get_by_role("cell").first).to_have_text("102 EUR")
    cases = []
    for kind, fields in (
        ("supplier_outage", {}),
        ("capacity_reduction", {"New capacity limit": "4"}),
        ("price_increase", {"New price per unit": "12.00"}),
        ("demand_increase", {"New demand quantity": "25"}),
        ("combined", {"New demand quantity": "12", "New capacity limit": "4"}),
    ):
        page.get_by_label("Scenario type", exact=True).select_option(kind)
        if kind != "demand_increase":
            page.get_by_label("Supplier to change (original terms)", exact=True).select_option(
                supplier
            )
            expect(page.locator("body")).to_contain_text(
                "Original capacity: 6 units. Original price: 10"
            )
        if kind == "combined":
            before = len(children())
            page.get_by_label("New demand quantity", exact=True).fill("12")
            page.get_by_role("button", name="Create and save scenario", exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("at least two changes")
            expect(page.locator("#scenario-error")).to_be_focused()
            assert len(children()) == before
            route = page.url
            page.get_by_role("button", name="Return to original base", exact=True).click()
            expect(page.get_by_role("button", name="Stay", exact=True)).to_be_focused()
            page.get_by_role("button", name="Stay", exact=True).click()
            expect(page).to_have_url(route)
            expect(page.get_by_label("New demand quantity", exact=True)).to_have_value("12")
        for label, value in fields.items():
            page.get_by_label(label, exact=True).fill(value)
        expect(page.locator("body")).to_contain_text("Draft assumptions")
        before = len(children())
        previous = parse_qs(urlsplit(page.url).query)["case_id"][0]
        if kind == "supplier_outage":
            page.get_by_role("button", name="Create and save scenario", exact=True).dblclick()
        else:
            page.get_by_role("button", name="Create and save scenario", exact=True).focus()
            page.keyboard.press("Enter")
        expect(page.get_by_text("Saved case " + previous, exact=True)).to_have_count(0)
        expect(page.get_by_role("heading", name="Saved scenario comparison")).to_be_visible()
        expect(page.locator("#scenario-result-heading")).to_be_focused()
        page.wait_for_url("**/planning?case_id=*&view=whatif")
        current = parse_qs(urlsplit(page.url).query)["case_id"][0]
        assert current != identity and len(children()) == before + 1
        saved = stack.client.get(f"{BASE}/{current}").json()
        cases.append(saved)
        assert saved["parent_id"] == identity and saved["origin"] == "demo"
        assert saved["snapshot"]["facts"] == base["snapshot"]["facts"]
        assert saved["snapshot"]["assessments"] == base["snapshot"]["assessments"]
        assert saved["snapshot"]["scenario"]["kind"] == kind
        expect(cost_row(page).get_by_role("cell").nth(0)).to_have_text("102 EUR")
        minimum = saved["snapshot"]["result"]["minimum_cost_plan"]
        if minimum is None:
            expect(cost_row(page).get_by_role("cell").nth(1)).to_have_text("Unavailable")
            expect(page.locator("body")).to_contain_text("unavailable, not zero")
        else:
            expect(cost_row(page).get_by_role("cell").nth(1)).to_have_text(
                f"{Decimal(minimum['total_cost']):,f} EUR"
            )
        region = page.get_by_role("region", name="Exact original-base and scenario comparison")
        after = (
            {}
            if minimum is None
            else {row["supplier_id"]: row["quantity"] for row in minimum["allocations"]}
        )
        for allocation in base["snapshot"]["result"]["minimum_cost_plan"]["allocations"]:
            sid, quantity = allocation["supplier_id"], allocation["quantity"]
            row = region.get_by_role("row").filter(
                has=page.get_by_role("rowheader", name="Demo supplier " + sid.split("-")[-1])
            )
            expect(row.get_by_role("cell").nth(0)).to_have_text(str(quantity))
            expect(row.get_by_role("cell").nth(1)).to_have_text(
                str(after[sid]) if sid in after else "Unavailable"
            )
        if kind in {"demand_increase", "combined"}:
            expect(page.locator("body")).to_contain_text("not a like-for-like saving")
        expect(page.locator("body")).to_contain_text("not fresh quotations")
        expect(page.get_by_role("button", name="Review approval", exact=True)).to_have_count(0)
        expect(page.get_by_role("button", name="Review No-award", exact=True)).to_have_count(0)
        assert stack.client.get(f"{BASE}/{identity}").json() == base
    assert len(children()) == 5
    for width in (1280, 1440, 768, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(stack.root / f"scenario-comparison-{width}.png"), full_page=True)

    # Real HTTP 503 for only the original GET, injected in an owned test server.
    marker = stack.root / "original-read-unavailable"
    marker.write_text("controlled fault", encoding="utf-8")
    (stack.root / "scenario_fault_api.py").write_text(
        "from pathlib import Path\nfrom backend.app.main import app\n"
        "from starlette.responses import JSONResponse\n"
        "@app.middleware('http')\nasync def original_fault(request, call_next):\n"
        f"    if (request.method == 'GET' and request.url.path == {BASE + '/' + identity!r}\n"
        f"        and Path({str(marker)!r}).exists()):\n"
        "        return JSONResponse({'detail':'controlled read fault'}, status_code=503)\n"
        "    return await call_next(request)\n",
        encoding="utf-8",
    )
    stack.stop(stack.api)
    stack.env["PYTHONPATH"] = str(stack.root) + os.pathsep + stack.env.get("PYTHONPATH", "")
    stack.api = stack.start(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "scenario_fault_api:app",
            "--host",
            "127.0.0.1",
            "--port",
            stack.api_url.rsplit(":", 1)[1],
        ],
        "original-fault-api",
    )
    wait_until(stack.api_ready, "original-read fault API")
    context = browser.new_context(viewport={"width": 320, "height": 900})
    try:
        fresh = context.new_page()
        child = cases[3]
        fresh.goto(stack.frontend_url + f"/planning?case_id={child['case_id']}&view=whatif")
        expect(fresh.get_by_role("alert")).to_contain_text("Original-base data is unavailable")
        expect(cost_row(fresh).get_by_role("cell").first).to_have_text("Unavailable")
        marker.unlink()
        fresh.get_by_role("button", name="Retry original-base retrieval", exact=True).click()
        expect(cost_row(fresh).get_by_role("cell").first).to_have_text("102 EUR")
        expect(cost_row(fresh).get_by_role("cell").nth(1)).to_have_text("Unavailable")
        expect(fresh.locator("#scenario-result-heading")).to_be_focused()
        fresh.screenshot(
            path=str(stack.root / "infeasible-original-retained-320.png"), full_page=True
        )
        assert len(children()) == 5
        fresh.get_by_label("Scenario type", exact=True).select_option("demand_increase")
        fresh.get_by_label("New demand quantity", exact=True).fill("12")
        route = fresh.url
        stack.stop(stack.api)
        fresh.get_by_role("button", name="Create and save scenario", exact=True).click()
        expect(
            fresh.get_by_role("button", name="Retry the same request", exact=True)
        ).to_be_visible()
        record = fresh.get_by_label("Exact request recovery JSON", exact=True)
        pending = json.loads(record.input_value())
        assert pending["url"].endswith(f"/{identity}/scenarios")
        fresh.goto(stack.frontend_url + "/cases")
        expect(fresh).to_have_url(route)
        assert json.loads(record.input_value()) == pending
        stack.start_api(stored_only=True)
        fresh.get_by_role("button", name="Retry the same request", exact=True).click()
        expect(
            fresh.get_by_role("button", name="Retry the same request", exact=True)
        ).to_have_count(0)
        expect(fresh.locator("#scenario-result-heading")).to_be_focused()
        assert len(children()) == 6
        assert stack.client.get(f"{BASE}/{identity}").json() == base
    finally:
        context.close()
    page.get_by_role("button", name="Return to original base", exact=True).click()
    expect(page.get_by_text("Saved case " + identity, exact=True)).to_be_visible()
    stack.evidence["checks"].append(
        "All five real original-base scenarios, bounded combined validation, immutable base/ML, "
        "classification/grouping, genuine infeasibility, keyboard/narrow comparison, focused "
        "save/retry, controlled original-GET 503 and real process-outage exact recovery PASS"
    )
    stack.evidence["outcome"] = "PASS"
