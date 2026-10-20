"""Phone width: case list, scenario with its chart, and empty/error states."""

import re
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]


def _no_horizontal_scroll(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


def _create_case(client):
    """One base case through the same API calls the Open RFQs page makes."""
    url = "/api/v2/procurement/planning-cases"
    preview = client.get(url + "/odoo-history/preview", params={"purchase_group_id": 501})
    assert preview.status_code == 200, preview.text
    payload = {"purchase_group_id": 501, "terms": preview.json()["terms"]}
    created = client.post(
        url + "/from-odoo-history", json=payload, headers={"Idempotency-Key": str(uuid4())}
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_cases_scenario_and_states_at_375_px(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    page.set_viewport_size({"width": 375, "height": 812})
    base = _create_case(stack.client)

    page.goto(stack.frontend_url + "/cases")
    expect(page.get_by_role("heading", name="Ügyek", level=1)).to_be_visible()
    # Phones get cards; the desktop table is in the DOM but hidden, so match visible only.
    expect(page.get_by_text("T6 Comparison Product").locator("visible=true").first).to_be_visible()
    expect(page.get_by_text("Döntésre vár").locator("visible=true").first).to_be_visible()
    assert _no_horizontal_scroll(page)

    page.get_by_role("button", name="Megnyitás").locator("visible=true").first.click()
    page.wait_for_url(re.compile(r"/planning\?case_id=" + base["case_id"]))
    expect(page.get_by_role("heading", level=1)).to_have_text("T6 Comparison Product")
    assert _no_horizontal_scroll(page)

    page.get_by_role("tab", name="Mi történne, ha…?").click()
    page.locator("#stress-kind").select_option("price_change")
    page.locator("#stress-supplier").select_option(index=1)
    page.locator("#stress-price").fill("abc")
    page.get_by_role("button", name="Forgatókönyv futtatása és mentése").click()
    expect(page.locator("#scenario-error")).to_contain_text("pozitív")
    page.locator("#stress-price").fill("1.25")
    # The form drops a second submit within 0.5 s (double-click guard); pause like a person.
    page.wait_for_timeout(700)
    page.get_by_role("button", name="Forgatókönyv futtatása és mentése").click()
    expect(page.locator("#scenario-result-heading")).to_have_text("Árváltozás")
    expect(page.get_by_role("region", name="Alapügy és forgatókönyv")).to_be_visible()
    expect(page.locator(".recharts-surface").first).to_be_visible()
    assert _no_horizontal_scroll(page)
    stored = stack.client.get(f"/api/v2/procurement/planning-cases/{base['case_id']}").json()
    assert stored["snapshot_hash"] == base["snapshot_hash"]  # the base never changes

    page.get_by_role("button", name="Menü").click()
    page.locator("#drawer-cases").click()
    page.locator("#library-search").fill("nincs-ilyen-termek")
    page.locator("#library-search").press("Enter")
    expect(page.get_by_role("heading", name="Nincs találat")).to_be_visible()

    page.goto(stack.frontend_url + f"/planning?case_id={uuid4()}&view=overview")
    expect(page.get_by_role("heading", name="Az ügy nem nyitható meg")).to_be_visible()
    expect(page.get_by_role("button", name="Vissza az ügyekhez")).to_be_visible()
    assert _no_horizontal_scroll(page)
    stack.evidence["checks"].append("375 px: cases, price scenario, empty and error states")
