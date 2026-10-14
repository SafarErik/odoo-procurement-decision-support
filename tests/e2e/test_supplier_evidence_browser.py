"""Buyer explanations to exact stored audit, real read-only HTTP and native zoom."""

import json
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from frontend.planning_client import _supplier_label

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_supplier_explanation_to_exact_evidence_keyboard_reflow_and_zoom(
    smoke_stack, smoke_page, playwright
):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    request = deepcopy(stack.payload)
    request["suppliers"][0]["supplier_id"] = "Árvíztűrő 供应商 " + "UnbrokenSupplier" * 12
    reply = stack.client.post(BASE, json=request, headers={"Idempotency-Key": str(uuid4())})
    assert reply.status_code == 201, reply.text
    original = reply.json()
    children = []
    for suppliers in (request["suppliers"][:1], request["suppliers"]):
        reply = stack.client.post(
            f"{BASE}/{original['case_id']}/scenarios",
            json={
                "kind": "supplier_outage",
                "suppliers": [
                    {"supplier_id": s["supplier_id"], "available": False} for s in suppliers
                ],
                "source": request["requirement_source"],
            },
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert reply.status_code == 201, reply.text
        children.append(reply.json())
    stack.stop(stack.api)
    stack.start_api(stored_only=True)

    def open_view(case, view="suppliers"):
        page.goto(stack.frontend_url + f"/planning?case_id={case['case_id']}&view={view}")
        expect(page.get_by_role("heading", name="Why these supplier assessments?")).to_be_visible()

    open_view(original)
    expect(page.locator("body")).to_contain_text("not a failure probability")
    expect(page.get_by_text("What should I test?", exact=True)).to_have_count(0)
    for assessment in original["snapshot"]["assessments"]:
        feature = assessment["snapshot"]
        region = page.get_by_role(
            "region",
            name="Supplier assessment: " + _supplier_label(feature["context"]["supplier_id"]),
        )
        expect(region).to_contain_text(
            "Schedule watch" if assessment["predicted_class"] else "Schedule regular"
        )
        expect(region).to_contain_text(f"{feature['values'][1]:g} completed receipts")
        expect(region).to_contain_text(
            datetime.fromisoformat(feature["cutoff"].replace("Z", "+00:00")).isoformat()
        )
        summary = region.locator("summary")
        summary.focus()
        page.keyboard.press("Enter")
        assert summary.evaluate("el => el.parentElement.open")
        expect(region).to_contain_text("rounded for reading")
        page.keyboard.press("Enter")
    expect(page.locator("body")).to_contain_text("does not mean the supplier is excluded")
    expect(page.locator("body")).to_contain_text("declared capacity")
    page.get_by_role("button", name="Inspect exact evidence in Audit", exact=True).click()
    expect(page.locator("#audit-evidence-heading")).to_be_focused()
    expect(page).to_have_url(
        stack.frontend_url + f"/planning?case_id={original['case_id']}&view=audit"
    )
    expect(page.locator("body")).to_contain_text("ML evidence remain synthetic")
    details = page.locator("summary").filter(has_text="Saved inputs, policy and allocations")
    assert not details.evaluate("el => el.parentElement.open")
    details.focus()
    page.keyboard.press("Enter")
    exact = page.get_by_role("region", name="Exact saved supplier inputs", exact=True)
    for supplier in original["snapshot"]["request"]["suppliers"]:
        row = exact.get_by_role("row").filter(has_text=_supplier_label(supplier["supplier_id"]))
        expect(row).to_contain_text(f"{Decimal(supplier['unit_price']):,f}")
        expect(row).to_contain_text(supplier["promised_date"])
    expect(page.locator("body")).to_contain_text(original["snapshot_hash"])
    trees = page.locator("summary").filter(has_text="Supplier tree paths and model evidence")
    trees.focus()
    page.keyboard.press("Enter")
    tree = page.locator("summary").filter(has_text="— exact tree record").first
    tree.focus()
    page.keyboard.press("Enter")
    expect(page.locator("body")).to_contain_text(original["snapshot"]["assessments"][0]["model_id"])
    raw = page.locator("summary").filter(has_text="Complete saved snapshot JSON")
    raw.focus()
    page.keyboard.press("Enter")
    record = page.get_by_role("region", name="Complete saved snapshot JSON", exact=True)
    assert json.loads(record.inner_text()) == original["snapshot"]
    for width in (1280, 1440, 768, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        exact.focus()
        page.keyboard.press("ArrowRight")
        assert exact.evaluate("el => el.getBoundingClientRect().right <= innerWidth")
        if width <= 390:
            assert exact.evaluate("el => el.scrollWidth > el.clientWidth")
            page.wait_for_function(
                "document.querySelector('[aria-label=\"Exact saved supplier inputs\"]')"
                ".scrollLeft > 0"
            )
        record.focus()
        page.keyboard.press("PageDown")
        page.wait_for_function(
            "document.querySelector('[aria-label=\"Complete saved snapshot JSON\"]').scrollTop > 0"
        )
        assert record.evaluate("el => el.scrollTop > 0")
        page.screenshot(path=str(stack.root / f"supplier-audit-{width}.png"))
    for case in children:
        open_view(case)
        expect(page.locator("body")).to_contain_text("Excluded: declared unavailable")
        expect(page.locator("body")).to_contain_text("do not reclassify suppliers")
        assert stack.client.get(f"{BASE}/{case['case_id']}").json() == case
    expect(page.locator("body")).to_contain_text("cannot cover demand")
    expect(page.locator("body")).to_contain_text("No proven allocation is saved")
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    extension = stack.root / "supplier-zoom-extension"
    extension.mkdir()
    (extension / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Supplier evidence zoom check",
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
        str(stack.root / "supplier-zoom-profile"),
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
        zoom = context.new_page()
        zoom.goto(stack.frontend_url + f"/planning?case_id={original['case_id']}&view=suppliers")
        expect(zoom.get_by_role("heading", name="Why these supplier assessments?")).to_be_visible()
        factor = worker.evaluate("""async () => {
            const [tab] = await chrome.tabs.query({url:'http://127.0.0.1/*'});
            await chrome.tabs.setZoom(tab.id, 2);
            return chrome.tabs.getZoom(tab.id);
        }""")
        assert factor == 2
        zoom.wait_for_function("window.devicePixelRatio === 2 && window.innerWidth <= 640")
        assert zoom.evaluate("document.documentElement.scrollWidth <= innerWidth")
        zoom.get_by_role("button", name="Inspect exact evidence in Audit", exact=True).click()
        zoom.get_by_text("Saved inputs, policy and allocations", exact=True).click()
        zoom.get_by_text("Complete saved snapshot JSON", exact=True).click()
        assert zoom.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert (
            json.loads(zoom.get_by_role("region", name="Complete saved snapshot JSON").inner_text())
            == original["snapshot"]
        )
        zoom.screenshot(path=str(stack.root / "supplier-audit-200-percent.png"))
        stack.evidence["native_browser_zoom"] = factor
    finally:
        context.close()
    stack.stop(stack.api)
    page.goto(stack.frontend_url + f"/planning?case_id={original['case_id']}&view=suppliers")
    expect(
        page.get_by_role("alert").filter(has_text="Planning data is unavailable")
    ).to_be_visible()
    expect(page.get_by_role("heading", name="Why these supplier assessments?")).to_have_count(0)
    stack.start_api(stored_only=True)
    page.reload()
    expect(page.get_by_role("heading", name="Why these supplier assessments?")).to_be_visible()
    assert stack.client.get(f"{BASE}/{original['case_id']}").json() == original
    log = (stack.root / "api.log").read_text(encoding="utf-8")
    assert log.count('"POST ') == 3  # Only fixture preparation; all evidence work is stored-only.
    stack.evidence["checks"].append(
        "Saved classes/sample/reference/applicability and real exclusions vs zero allocation; "
        "buyer-to-exact Audit keyboard disclosure/scoped scrolling, full snapshot equality, "
        "long/missing-business labels, base/feasible/infeasible lineage, five viewport widths, "
        "native 200% zoom, model-unconfigured reads and actual GET outage/reopen PASS"
    )
    stack.evidence["outcome"] = "PASS"
