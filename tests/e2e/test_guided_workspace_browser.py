"""Home, responsive case navigation and deliberate no-award on an isolated database."""

import re

import pytest

from tests.e2e.test_cases_scenarios_mobile_browser import _create_case, _no_horizontal_scroll

pytestmark = [pytest.mark.integration, pytest.mark.e2e]

ACTIVE_TAB_VISIBLE = """() => {
    const list = document.getElementById('case-tablist');
    const tab = list?.querySelector('[role="tab"][data-state="active"]');
    if (!tab || tab.id !== 'view-decision') return false;
    const active = tab.getBoundingClientRect(), bounds = list.getBoundingClientRect();
    return active.left >= bounds.left - 1 && active.right <= bounds.right + 1;
}"""


def test_home_responsive_saved_case_and_no_award(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    page.goto(stack.frontend_url)
    expect(page.get_by_role("heading", name="Döntésre váró ügyek")).to_be_visible()
    expect(page.get_by_text(re.compile("Még nincs mentett ügy"))).to_be_visible()
    base = _create_case(stack.client)
    page.reload()
    expect(page.get_by_role("button", name=re.compile("Ügy folytatása")).first).to_be_visible()

    for width in (1440, 1280, 768, 390):
        page.set_viewport_size({"width": width, "height": 900})
        assert _no_horizontal_scroll(page), f"Home overflow at {width}"
        page.screenshot(path=str(stack.root / f"home-{width}.png"), full_page=True)

    page.get_by_role("button", name=re.compile("Ügy folytatása")).first.click()
    page.wait_for_url(re.compile(r"/planning\?case_id=" + base["case_id"]))
    for width in (1440, 1280, 768, 390):
        page.set_viewport_size({"width": width, "height": 900})
        for tab, name in (
            ("overview", "Áttekintés"),
            ("suppliers", "Szállítók"),
            ("plans", "Tervek"),
            ("scenarios", "Mi lenne, ha…?"),
        ):
            page.get_by_role("tab", name=name, exact=True).click()
            expect(page.get_by_role("tab", name=name, exact=True)).to_have_attribute(
                "data-state", "active"
            )
            if tab == "suppliers":
                expect(page.get_by_role("region", name="Supplier 1", exact=True)).to_be_visible()
            if tab == "scenarios":
                expect(page.get_by_text("Forgatókönyvek betöltése…")).not_to_be_visible()
            assert _no_horizontal_scroll(page), f"{tab} overflow at {width}"
            page.evaluate("window.scrollTo(0, 0)")
            page.screenshot(path=str(stack.root / f"{tab}-{width}.png"), full_page=True)

    page.emulate_media(reduced_motion="reduce")
    page.get_by_role("tab", name="Tervek", exact=True).click()
    page.get_by_role("button", name="Kiválasztás", exact=True).first.click()
    page.get_by_role("button", name="Döntés áttekintése").click()
    page.wait_for_function(ACTIVE_TAB_VISIBLE)
    page.get_by_role("button", name="Most nem rendelünk").click()
    page.locator("#final-actor").fill("Isolated usability test")
    page.locator("#final-reason").fill("The buyer requests revised supplier terms.")
    page.locator("input[name=demonstration]").check()
    page.locator("#decision-review-button").click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    before = stack.client.get(f"/api/v2/procurement/planning-cases/{base['case_id']}").json()
    assert before["final_decision"] is None
    page.locator("#decision-review-button").click()
    dialog.get_by_role("button", name="Megerősítem: nem rendelünk").click()
    expect(page.locator("#saved-decision-heading")).to_have_text("Nem rendelünk")
    expect(page.get_by_role("button", name="Jóváhagyott PDF megtekintése")).to_have_count(0)
    closed_url = page.url
    page.reload()
    expect(page.locator("#saved-decision-heading")).to_have_text("Nem rendelünk")
    page.wait_for_function(ACTIVE_TAB_VISIBLE)
    assert page.url == closed_url
    assert _no_horizontal_scroll(page)
    page.screenshot(path=str(stack.root / "no-award-390.png"), full_page=True)
    stack.evidence["checks"].append(
        "Empty/populated home; 1440/1280/768/390 px case views; reduced motion; "
        "cancel confirmation; No-award and reload without PDF"
    )
