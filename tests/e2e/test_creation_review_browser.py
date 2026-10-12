"""#35 real saved comparisons; only the read-only Odoo source is a controlled fixture."""

import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import create_engine, text

from tests.e2e.conftest import wait_until
from tests.test_odoo_comparison_case_adapter import _payloads
from tests.test_t15_odoo_planning import quotation_reader
from tools.t15_odoo_demo import prepare_odoo_assets

pytestmark = [pytest.mark.integration, pytest.mark.e2e]
BASE = "/api/v2/procurement/planning-cases"


def test_review_validate_edit_and_save_both_sources(smoke_stack, smoke_page):
    from playwright.sync_api import expect

    expect.set_options(timeout=45000)
    stack, page = smoke_stack, smoke_page
    engine = create_engine(stack.env["DECISION_DATABASE_URL"])

    def count():
        with engine.connect() as connection:
            return connection.execute(text("SELECT count(*) FROM planning_cases")).scalar_one()

    try:
        page.goto(stack.frontend_url + "/planning")
        page.get_by_role("tab", name="Demo", exact=True).click()
        page.get_by_role("button", name="Load demo inputs", exact=True).click()
        demand = page.get_by_label("Demand quantity", exact=True)
        demand.fill("0")
        page.get_by_role("button", name="Review demo terms", exact=True).click()
        expect(demand).to_have_attribute("aria-invalid", "true")
        expect(demand).to_be_focused()
        assert count() == 0
        demand.fill("11")
        page.get_by_role("button", name="Review demo terms", exact=True).click()
        expect(page.get_by_role("heading", name="Review before calculating")).to_be_focused()
        expect(demand).to_be_disabled()
        expect(page.get_by_role("region", name="Reviewed exact supplier terms")).to_contain_text(
            "EUR"
        )
        assert count() == 0
        page.get_by_role("button", name="Edit terms", exact=True).click()
        expect(demand).to_have_value("11")
        demand.fill("10")
        page.get_by_role("button", name="Review demo terms", exact=True).focus()
        page.keyboard.press("Enter")
        page.get_by_role("button", name="Create and save plan", exact=True).dblclick()
        expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
        expect(page.locator("#saved-case-heading")).to_be_focused()
        assert count() == 1
        synthetic_id = parse_qs(urlsplit(page.url).query)["case_id"][0]
        synthetic = stack.client.get(f"{BASE}/{synthetic_id}").json()
        assert synthetic["workspace"] == "practice"
        assert synthetic["snapshot"]["request"]["requirement"]["approved_quantity"] == 10

        # Prepare the existing matched Odoo fixture/model offline in owned storage.
        directory = stack.root / ".artifacts/t15-odoo-demo"

        def prepare_fixture():
            reader = quotation_reader(_payloads(), [])
            case = asyncio.run(reader.read_comparison_case(501))
            code, observed = asyncio.run(reader.read_currency_code(case.offers[0].currency_id))
            return prepare_odoo_assets(directory, case, code, observed)

        # Playwright's sync API owns an asyncio loop in this thread.
        with ThreadPoolExecutor(max_workers=1) as executor:
            prepared, _ = executor.submit(prepare_fixture).result()
        stack.stop(stack.api)
        # Only the Odoo adapter transport is mocked; app/model/CBC/PostgreSQL remain real.
        (stack.root / "creation_fixture_api.py").write_text(
            "from backend.app.main import app\n"
            "from backend.app import dependencies\n"
            "from tests.test_t15_odoo_planning import quotation_reader\n"
            "from tests.test_odoo_comparison_case_adapter import _payloads\n"
            "dependencies.get_comparison_case_reader = lambda: quotation_reader(_payloads(), [])\n",
            encoding="utf-8",
        )
        stack.env["T15_TRUSTED_MODEL_DIRECTORY"] = str(directory / "model")
        stack.env["PYTHONPATH"] = str(stack.root) + os.pathsep + stack.env.get("PYTHONPATH", "")
        stack.api = stack.start(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "creation_fixture_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                stack.api_url.rsplit(":", 1)[1],
            ],
            "fixture-api",
        )
        wait_until(stack.api_ready, "controlled fixture API")
        page.get_by_role("button", name="Cases", exact=True).click()
        page.get_by_role("button", name="New comparison", exact=True).click()
        page.get_by_role("tab", name="Odoo", exact=True).click()
        page.get_by_role("button", name="Load prepared Odoo comparison", exact=True).click()
        capacity = page.get_by_label("Capacity (explicit limit)", exact=True).first
        capacity.fill("-1")
        page.get_by_role("button", name="Review Odoo terms", exact=True).click()
        expect(capacity).to_have_attribute("aria-invalid", "true")
        expect(capacity).to_be_focused()
        assert count() == 1
        capacity.fill("120")
        page.get_by_label("MOQ (blank means none)", exact=True).first.fill("")
        page.get_by_role("button", name="Review Odoo terms", exact=True).click()
        review = page.get_by_role("region", name="Reviewed exact supplier terms", exact=True)
        expect(review).to_contain_text("None (no MOQ)")
        expect(page.locator("body")).to_contain_text("This local preview does not refresh Odoo.")
        assert count() == 1
        for width in (1280, 768, 390, 320):
            page.set_viewport_size({"width": width, "height": 900})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(stack.root / f"creation-review-{width}.png"), full_page=True)
        page.get_by_role("button", name="Create and save Odoo plan", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_role("heading", name="Minimum cost", exact=True)).to_be_visible()
        expect(page.locator("#saved-case-heading")).to_be_focused()
        assert count() == 2
        identity = parse_qs(urlsplit(page.url).query)["case_id"][0]
        saved = stack.client.get(f"{BASE}/{identity}").json()
        assert saved["workspace"] == "controlled"
        facts = saved["snapshot"]["facts"]
        assert facts["input_kind"] == "odoo_quotations_synthetic_history"
        assert facts["source_type"] == "t14_synthetic"
        suppliers = saved["snapshot"]["request"]["suppliers"]
        assert suppliers[0]["minimum_order"]["quantity"] is None
        assert [Decimal(s["unit_price"]) for s in suppliers] == [
            Decimal(s["unit_price"]) for s in prepared["controlled_input"]["suppliers"]
        ]
        sources = saved["snapshot"]["provenance"]["entries"]
        assert any(s["source_type"] == "odoo_json2" for s in sources)
        assert any(s["source_type"] == "controlled_business_terms" for s in sources)
        stack.evidence["checks"].append(
            "Review performs no POST; field errors/focus, preserved edit values, repeated-click "
            "guard, keyboard/narrow review, genuine synthetic and controlled HTTP saves PASS; "
            "Odoo transport is a read-only fixture, not live ERP evidence"
        )
        stack.evidence["outcome"] = "PASS"
    finally:
        engine.dispose()
