"""#34 real navigation, draft safety, responsive drawer and browser zoom."""

import json
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_workspace_navigation_and_recovery(smoke_stack, smoke_page, playwright):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page

    def save(payload):
        response = stack.client.post(BASE, json=payload, headers={"Idempotency-Key": str(uuid4())})
        assert response.status_code == 201, response.text
        return response.json()

    earlier = save(stack.payload)
    practice = save(stack.payload | {"catalog_context": {"workspace": "practice"}})
    page.goto(stack.frontend_url + "/cases")
    expect(page.get_by_role("heading", name="Saved cases", exact=True)).to_be_visible()
    for workspace, case in (("unclassified", earlier), ("practice", practice)):
        page.get_by_label("Workspace", exact=True).select_option(workspace)
        page.get_by_role("button", name="Refresh", exact=True).click()
        page.get_by_role("button", name="Open case", exact=True).click()
        expect(page.get_by_text("Saved case " + case["case_id"], exact=True)).to_be_visible()
        for label, view in (
            ("What-if", "whatif"),
            ("Suppliers", "suppliers"),
            ("Audit", "audit"),
            ("Plans", "plans"),
        ):
            page.get_by_role("tab", name=label, exact=True).focus()
            page.keyboard.press("Enter")
            expect(page).to_have_url(
                stack.frontend_url + f"/planning?case_id={case['case_id']}&view={view}"
            )
        page.get_by_role("button", name="Cases", exact=True).click()

    # Draft cancellation keeps values; discard is deliberate and removes the draft.
    page.get_by_role("button", name="New comparison", exact=True).click()
    page.get_by_role("tab", name="Demo", exact=True).click()
    page.get_by_role("button", name="Load demo inputs", exact=True).click()
    page.get_by_label("Demand quantity", exact=True).fill("11")
    page.get_by_role("button", name="Cases", exact=True).click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    expect(page.get_by_role("button", name="Stay", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Cases", exact=True)).to_be_focused()
    expect(page.get_by_label("Demand quantity", exact=True)).to_have_value("11")
    page.get_by_role("button", name="Cases", exact=True).click()
    page.get_by_role("button", name="Discard draft", exact=True).click()
    expect(page.get_by_role("heading", name="Saved cases", exact=True)).to_be_visible()
    page.goto(stack.frontend_url + f"/planning?case_id={practice['case_id']}&view=whatif")
    page.get_by_label("Supplier to change (original terms)", exact=True).select_option(
        stack.payload["suppliers"][0]["supplier_id"]
    )
    page.get_by_label("New capacity limit", exact=True).fill("3")
    page.get_by_role("tab", name="Plans", exact=True).click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    page.get_by_role("button", name="Stay", exact=True).click()
    expect(page.get_by_role("tab", name="What-if", exact=True)).to_be_focused()
    expect(page.get_by_label("New capacity limit", exact=True)).to_have_value("3")
    page.get_by_role("tab", name="Plans", exact=True).click()
    page.get_by_role("button", name="Discard draft", exact=True).click()
    expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()

    for width in (1280, 1440, 768, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(stack.root / f"workspace-{width}.png"), full_page=True)
        if width < 1024:
            page.get_by_role("button", name="Workspace menu", exact=True).focus()
            page.keyboard.press("Enter")
            expect(page.get_by_role("dialog")).to_be_visible()
            expect(page.locator("#drawer-cases")).to_be_focused()
            assert page.get_by_role("dialog").evaluate("e => e.scrollWidth <= e.clientWidth")
            page.keyboard.press("Escape")
            expect(page.get_by_role("button", name="Workspace menu", exact=True)).to_be_focused()
    page.emulate_media(reduced_motion="reduce")
    assert page.evaluate("matchMedia('(prefers-reduced-motion:reduce)').matches")
    page.get_by_role("button", name="Workspace menu", exact=True).click()
    page.get_by_role("button", name="Open RFQs", exact=True).click()
    expect(
        page.get_by_role("heading", name="Open requests for quotation", exact=True)
    ).to_be_visible()
    expect(page.get_by_role("alert")).to_be_visible()  # Odoo deliberately unconfigured.

    page.set_viewport_size({"width": 1280, "height": 900})
    page.get_by_role("button", name="Practice", exact=True).click()
    page.get_by_role("button", name="Choose compare plans", exact=True).click()
    page.get_by_role("button", name="Review Practice terms", exact=True).click()
    stack.stop(stack.api)
    page.get_by_role("button", name="Calculate and save fresh Practice case").click()
    expect(page.get_by_role("button", name="Retry the same request")).to_be_visible()
    recovery = json.loads(page.get_by_label("Exact request recovery JSON").input_value())
    for destination in ("/", "/cases", f"/planning?case_id={earlier['case_id']}&view=audit"):
        page.goto(stack.frontend_url + destination)
        expect(page).to_have_url(stack.frontend_url + "/practice")
        assert (
            json.loads(page.get_by_label("Exact request recovery JSON").input_value()) == recovery
        )
    stack.start_api()
    page.get_by_role("button", name="Retry the same request").click()
    expect(page.get_by_role("button", name="Open saved Practice case")).to_be_visible()
    page.get_by_role("button", name="Cases", exact=True).click()
    stack.stop(stack.api)
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(page.get_by_role("alert")).to_be_visible()
    expect(page.get_by_role("button", name="Open case", exact=True)).to_have_count(0)
    stack.start_api(stored_only=True)

    # A test-only extension calls the native tab zoom API in an owned browser profile.
    # CSS transforms/device emulation would not prove actual browser text enlargement.
    extension = stack.root / "zoom-extension"
    extension.mkdir()
    (extension / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Owned browser zoom check",
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
        str(stack.root / "zoom-profile"),
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
        zoom_page.goto(stack.frontend_url + f"/planning?case_id={practice['case_id']}&view=plans")
        expect(zoom_page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
        native_zoom = worker.evaluate("""async () => {
            const [tab] = await chrome.tabs.query({url:'http://127.0.0.1/*'});
            await chrome.tabs.setZoom(tab.id, 2);
            return chrome.tabs.getZoom(tab.id);
        }""")
        assert native_zoom == 2
        zoom_page.wait_for_function("window.devicePixelRatio === 2 && window.innerWidth <= 640")
        assert zoom_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        expect(zoom_page.get_by_role("button", name="Workspace menu", exact=True)).to_be_visible()
        zoom_page.screenshot(path=str(stack.root / "browser-200-percent.png"), full_page=True)
        stack.evidence["native_browser_zoom"] = native_zoom
    finally:
        context.close()
    stack.evidence["checks"].append(
        "Earlier/Practice reopening, sections, draft Stay/Discard, keyboard focus, "
        "rail/drawer reflow, reduced motion, native 200% zoom and exact pending recovery"
    )
    stack.evidence["outcome"] = "PASS"
