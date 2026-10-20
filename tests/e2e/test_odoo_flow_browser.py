"""Buyer flow in the browser: open RFQ → saved case → tabs → one approval → Hungarian PDF.

Real FastAPI, PostgreSQL and Reflex; Odoo and the supplier model come from the P1
fixtures (tests/e2e/odoo_fixture_api.py).
"""

import re
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.e2e]


def _console_errors(page):
    errors = []
    page.on("console", lambda message: message.type == "error" and errors.append(message.text))
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def test_rfq_to_approved_pdf_in_hungarian_then_english(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    errors = _console_errors(page)

    page.goto(stack.frontend_url + "/rfqs")
    expect(page.get_by_role("heading", name="Odoo-ajánlatok kiválasztása")).to_be_visible()
    expect(page.get_by_text("T6 Comparison Product").first).to_be_visible()
    page.locator("#start-501").click()
    expect(page.locator("#creation-step-heading")).to_contain_text("igény")
    page.get_by_role("button", name="Tovább a beszállítói feltételekhez").click()
    expect(page.locator("#creation-step-heading")).to_contain_text("feltételek")
    supplier = page.get_by_role("button", name=re.compile(r"Supplier 1.*"))
    supplier.click()
    capacity = page.locator('input[name$="_capacity"]').first
    capacity.fill("121")
    page.get_by_role("radio", name="EN").click()
    expect(capacity).to_have_value("121")
    page.get_by_role("radio", name="HU").click()
    expect(capacity).to_have_value("121")
    page.get_by_role("button", name="Vissza az igényhez").click()
    page.get_by_role("button", name="Tovább a beszállítói feltételekhez").click()
    expect(capacity).to_have_value("121")
    page.get_by_role("button", name="Feltételek áttekintése").click()
    expect(page.get_by_role("heading", name="Áttekintés mentés előtt")).to_be_visible()
    page.locator("#calculate-save").click()

    page.wait_for_url(re.compile(r"/planning\?case_id=.+&view=overview"))
    case_id = parse_qs(urlparse(page.url).query)["case_id"][0]
    saved = stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}").json()
    assert saved["parent_id"] is None
    assert saved["snapshot"]["facts"]["input_kind"] == "odoo_quotations_odoo_history"
    expect(page.get_by_role("heading", level=1)).to_have_text("T6 Comparison Product")
    expect(page.get_by_text("Generált adat")).to_be_visible()
    expect(page.get_by_text("Az összehasonlítás mentve.")).to_be_visible()
    expect(page.get_by_text("Legkisebb költség").first).to_be_visible()
    expect(page.get_by_role("heading", name="Következő lépés")).to_be_visible()

    page.get_by_role("tab", name="Szállítók").click()
    for name in ("Supplier 1", "Supplier 4", "Supplier 6"):
        expect(page.get_by_role("region", name=name)).to_be_visible()
    expect(page.get_by_text("Szállítók összevetése")).to_be_visible()
    expect(page.locator(".recharts-surface").first).to_be_visible()

    page.get_by_role("tab", name="Tervek").click()
    expect(page.get_by_role("region", name="Tervek összehasonlítása")).to_be_visible()
    expect(page.get_by_role("img", name=re.compile("Pontdiagram"))).to_be_visible()

    page.get_by_role("tab", name="Döntés és PDF").click()
    page.locator("#final-choice").select_option("Minimum cost")
    page.locator("#final-actor").fill("e2e buyer")
    page.locator("#final-reason").fill("The minimum-cost split meets the checked requirements.")
    page.locator("input[name=demonstration]").check()
    page.locator("#decision-review-button").click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_contain_text("Jóváhagyás megerősítése")
    dialog.get_by_role("button", name="Terv jóváhagyása").click()
    expect(page.locator("#saved-decision-heading")).to_have_text("Jóváhagyva")
    decided = stack.client.get(f"/api/v2/procurement/planning-cases/{case_id}").json()
    assert decided["final_decision"]["intent"]["plan_index"] == 0

    page.get_by_role("button", name="Jóváhagyott PDF megtekintése").click()
    expect(page.get_by_role("link", name="Jóváhagyott PDF letöltése")).to_be_visible()
    expect(page.get_by_text(re.compile(r"1\. oldal / \d+"))).to_be_visible()
    link = page.get_by_role("link", name="Jóváhagyott PDF letöltése")
    assert link.get_attribute("download").endswith("-hu.pdf")

    # English switch: labels change in place; the stored case is not re-read or re-solved.
    page.get_by_role("radio", name="EN").click()
    expect(page.get_by_role("tab", name="Decision & PDF")).to_be_visible()
    expect(page.locator("#saved-decision-heading")).to_have_text("Approved")
    page.get_by_role("button", name="View approved PDF").click()
    expect(page.get_by_role("link", name="Download approved PDF")).to_have_attribute(
        "download", re.compile(r".+-en\.pdf")
    )
    page.get_by_role("tab", name="Overview").click()
    expect(page.get_by_role("heading", name="Next step")).to_be_visible()
    page.get_by_role("button", name="Audit").click()
    expect(page.get_by_text(saved["snapshot_hash"], exact=True)).to_be_visible()

    assert not [e for e in errors if "No element found" in e or "_set_focus" in e], errors
    stack.evidence["checks"].append("RFQ → case → tabs → approval → HU PDF → EN switch")
