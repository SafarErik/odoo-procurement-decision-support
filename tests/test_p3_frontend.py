"""P3 frontend: Hungarian default, locale formatting, relabelling and the supplier view."""

import asyncio
from copy import deepcopy
from decimal import Decimal

import pytest

from application.supplier_overview import supplier_overview
from frontend.i18n import TEXT, day, money, number, percent, tr
from frontend.i18n_ui import UI_TEXT
from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case
from frontend.planning_library_client import library_row
from frontend.supplier_overview_client import map_overview
from tests.frontend_patching import patch_client
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_every_text_has_hungarian_and_english_and_screen_texts_are_merged():
    assert set(UI_TEXT) <= set(TEXT)
    for key, (hu, en) in TEXT.items():
        assert hu.strip() and en.strip(), key


@pytest.mark.parametrize(
    "value,currency,lang,expected",
    [
        ("1545.7", "HUF", "hu", "1 545,70 Ft"),
        ("1545.7", "HUF", "en", "1,545.70 HUF"),
        ("102", "EUR", "en", "€102.00"),
        ("102.000000000000000001", "EUR", "en", "€102.000000000000000001"),
        ("-7.5", "EUR", "hu", "−7,50 €"),
    ],
)
def test_money_keeps_stored_digits_and_follows_the_language(value, currency, lang, expected):
    assert money(Decimal(value), currency, lang) == expected


def test_dates_numbers_and_percentages_follow_the_language():
    assert day("2026-03-08", "hu") == "2026. márc. 8."
    assert day("2026-03-08T10:00:00+00:00", "en") == "8 Mar 2026"
    assert number(12345, "hu") == "12 345" and number("1234.5", "en", 1) == "1,234.5"
    assert percent(0.8, "hu", 0) == "80 %" and percent(0.8, "en", 0) == "80%"


def test_hungarian_is_the_default_and_mapping_uses_it(stored_cases):
    state = PlanningState(_reflex_internal_init=True)
    assert state.lang == "hu"
    base = stored_cases[1]
    display = _map_case(base, base["case_id"], "hu")
    assert display.plans[0]["title"] == "Legkisebb költség"
    assert display.plans[0]["cost"] == "102,00 €"
    assert display.details["status_label"] == "Tervek elkészültek"
    assert display.details["origin_badge"] == "Bemutató adat"  # pre-P2 synthetic demo case
    # Keys stay English so selection and decisions do not depend on the language.
    assert display.plans[0]["label"] == "Minimum cost"


def test_language_switch_relabels_without_any_http(stored_cases, monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Switching the language must not read or recalculate.")

    base = stored_cases[1]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))
    PlanningState.choose_final_plan.fn(state, "Alternative 1")
    for name in ("fetch_planning_case", "submit_planning_request", "fetch_planning_pdf"):
        patch_client(monkeypatch, name, forbidden)
    events = PlanningState.set_language.fn(state, ["en"])  # segmented control sends a list
    assert state.lang == "en" and state.plans[0]["title"] == "Minimum cost"
    assert state.plans[0]["cost"] == "€102.00"
    assert state.final_choice == "Alternative 1" and state.selected_plan["label"] == "Alternative 1"
    # Only the stored supplier overview is re-read (a GET of the saved snapshot).
    assert events and "load_supplier_overview" in str(events)
    for value in ([], ["hu", "en"], "de", "en"):
        assert PlanningState.set_language.fn(state, value) is None
    assert state.lang == "en"


def test_library_rows_accept_invalid_input_status_and_show_the_odoo_name(stored_cases):
    item = {
        "case_id": stored_cases[1]["case_id"],
        "parent_id": None,
        "created_at": "2026-10-18T10:00:00+00:00",
        "company_id": "odoo:res.company:1",
        "product_id": "odoo:product.product:7",
        "product_label": "[GEN] Steel bracket M8",
        "unit_label": "Units",
        "approved_quantity": 200,
        "quantity_unit": "odoo:uom.uom:1",
        "currency": "HUF",
        "required_date": "2026-10-25",
        "planning_status": "invalid_input",
        "decision_status": "draft",
        "source_kind": "odoo_quotations_odoo_history",
        "origin": "odoo",
        "data_origin": "generated",
        "minimum_cost": None,
        "scenario_kind": None,
        "changed_assumptions": None,
    }
    row = library_row(item, "hu")
    assert row["product"] == "[GEN] Steel bracket M8" and row["quantity"] == "200 db"
    assert row["outcome"] == tr("status_invalid_input", "hu")
    assert row["badge"] == "Generált adat" and row["minimum_cost"] == ""


def test_decision_rationale_is_saved_as_the_buyer_reviewed_it(stored_cases):
    base = stored_cases[1]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"]))
    form = {
        "choice": "Alternative 1",
        "actor": "buyer",
        "reason": "  lower risk  ",
        "demonstration": "on",
    }
    state.review_final_decision(form)
    assert state._decision_payload["rationale"] == "lower risk"
    assert state.decision_review["reason"] == "lower risk"


def test_starting_an_already_loaded_group_keeps_the_draft_and_focuses_the_terms():
    state = PlanningState(_reflex_internal_init=True)
    state.quotation_groups = [{"value": "1", "selectable": "yes"}]
    state.selected_group, state.odoo_ready = "1", True
    state._odoo_payload = {"draft": True}
    event = PlanningState.prepare_odoo_history.fn(state, "1")
    assert "creation-terms-heading" in str(event) and state._odoo_payload == {"draft": True}


def test_supplier_cards_and_kpi_charts_come_from_the_stored_overview(stored_cases):
    base = stored_cases[1]
    overview = supplier_overview(deepcopy(base["snapshot"]), "hu")
    mapped = map_overview(overview, "hu")
    assert len(mapped["cards"]) == len(base["snapshot"]["assessments"])
    card = mapped["cards"][0]
    assert card["name"].startswith("Bemutató szállító") and card["class_label"]
    assert card["metrics"] and card["path"] is not None and card["price"].endswith("€")
    with pytest.raises(ValueError):
        map_overview(overview, "en")  # the API answered in another language


def test_scenario_validation_reads_naturally_in_hungarian(stored_cases):
    from tests.test_t16_scenarios import event

    base = stored_cases[1]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))
    form = {"kind": "capacity_change", "supplier": "synthetic-S226", "capacity": "6"}
    asyncio.run(event(state, PlanningState.run_scenario, form))
    assert state.error_message.endswith("azonos az eredetivel (6 db). A 0 megszünteti.")
