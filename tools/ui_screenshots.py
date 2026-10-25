"""Capture UI evidence screenshots (desktop 1440x900 and 375 px) from a running dev stack.

Read-only navigation; it does not approve, save or change anything. Usage:
``python tools/ui_screenshots.py docs/evidence/p3 <approved case id>`` with ``tools.dev api``
and ``tools.dev ui`` running. Writes PNGs plus report.json (console errors, overflow).
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
OUT = Path(sys.argv[1])
CASE = sys.argv[2]
OUT.mkdir(parents=True, exist_ok=True)
report = {"console_errors": [], "overflow": {}}


def shot(page, name, *, full=False):
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    report["overflow"][name] = page.evaluate(
        "document.documentElement.scrollWidth - window.innerWidth"
    )


def tab(page, name):
    page.get_by_role("tab", name=name).click()
    page.wait_for_timeout(1200)


with sync_playwright() as p:
    browser = p.chromium.launch()
    for label, size in (("desktop", (1440, 900)), ("mobile", (375, 812))):
        context = browser.new_context(
            viewport={"width": size[0], "height": size[1]}, device_scale_factor=1
        )
        page = context.new_page()
        page.on(
            "console",
            lambda m, label=label: (
                m.type == "error" and report["console_errors"].append(f"{label}: {m.text}")
            ),
        )
        page.goto(BASE + "/cases")
        page.get_by_text("Megnyitás").locator("visible=true").first.wait_for()
        shot(page, f"01-cases-{label}-hu")
        page.goto(BASE + "/rfqs")
        page.get_by_text("Ajánlatok megtekintése").locator("visible=true").first.wait_for()
        shot(page, f"02-rfqs-{label}-hu")
        page.goto(f"{BASE}/planning?case_id={CASE}&view=overview")
        page.get_by_role("heading", level=1).wait_for()
        shot(page, f"03-overview-{label}-hu", full=True)
        tab(page, "Szállítók")
        shot(page, f"04-suppliers-{label}-hu", full=True)
        tab(page, "Tervek")
        shot(page, f"05-plans-{label}-hu", full=True)
        tab(page, "Mi lenne, ha…?")
        shot(page, f"06-scenarios-{label}-hu", full=True)
        tab(page, "Döntés és PDF")
        shot(page, f"07-decision-{label}-hu", full=True)
        page.get_by_role("radio", name="EN").click()
        page.wait_for_timeout(1500)
        tab(page, "Plans")
        shot(page, f"08-plans-{label}-en", full=True)
        page.get_by_role("radio", name="HU").click()
        page.wait_for_timeout(1500)
        page.goto(f"{BASE}/planning?case_id=00000000-0000-4000-8000-000000000000&view=overview")
        page.get_by_text("Az ügy nem nyitható meg").wait_for()
        shot(page, f"09-case-error-{label}-hu")
        page.goto(BASE + "/cases")
        page.locator("#library-search").fill("nincs-ilyen")
        page.locator("#library-search").press("Enter")
        page.get_by_text("Nincs találat").wait_for()
        shot(page, f"10-cases-empty-{label}-hu")
        context.close()
    browser.close()
(OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
print(json.dumps(report, indent=2, ensure_ascii=False))
