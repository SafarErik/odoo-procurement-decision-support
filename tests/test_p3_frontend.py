"""P3 frontend: Hungarian default, locale formatting, relabelling and the supplier view."""

import asyncio
from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

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


def test_each_text_key_is_defined_in_exactly_one_module():
    # The modules are merged with dict.update, so a second definition silently hides the
    # first one; every key must have a single source of truth.
    import ast
    from pathlib import Path

    keys = []
    for module, variable in (
        ("i18n.py", "TEXT"),
        ("i18n_ui.py", "UI_TEXT"),
        ("i18n_revamp.py", "REVAMP_TEXT"),
    ):
        tree = ast.parse((Path("frontend") / module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign | ast.AnnAssign) and isinstance(node.value, ast.Dict):
                target = node.targets[0] if isinstance(node, ast.Assign) else node.target
                if getattr(target, "id", None) == variable:
                    keys += [key.value for key in node.value.keys]
    assert len(keys) == len(TEXT)
    assert sorted(key for key in set(keys) if keys.count(key) > 1) == []


@pytest.mark.parametrize(
    "value,currency,lang,expected",
    [
        ("1545.7", "HUF", "hu", "1 545,70 Ft"),
        ("1545.7", "HUF", "en", "1,545.70 HUF"),
        ("102", "EUR", "en", "€102.00"),
        ("102.000000000000000001", "EUR", "en", "€102.000000000000000001"),
        ("1.00000000000000000000000000000001", "EUR", "en", "€1.00000000000000000000000000000001"),
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
    assert display.plans[0]["title"] == "Legolcsóbb terv"
    # An alternative names the tightest cost allowance that produced it; the cheapest plan none.
    assert display.plans[0]["budget"] == ""
    assert display.plans[1]["budget"].startswith("legfeljebb +")
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
    assert state.lang == "en" and state.plans[0]["title"] == "Cheapest plan"
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
    assert "creation-step-heading" in str(event) and state._odoo_payload == {"draft": True}
    assert state.creation_step == 1


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


def _scenario_item(base_id, kind="supplier_outage", quantity=10):
    return {
        "case_id": str(uuid4()),
        "parent_id": base_id,
        "created_at": "2026-10-18T10:00:00+00:00",
        "company_id": "demo:company:1",
        "product_id": "demo:product:1",
        "product_label": "Demo product",
        "unit_label": "Units",
        "approved_quantity": quantity,
        "quantity_unit": "demo:uom:1",
        "currency": "EUR",
        "required_date": "2026-10-25",
        "planning_status": "optimal",
        "decision_status": "draft",
        "source_kind": "controlled_synthetic",
        "origin": "demo",
        "data_origin": "synthetic",
        "minimum_cost": "102.00",
        "scenario_kind": kind,
        "changed_assumptions": None,
    }


def _scenario_pages(base_id, calls, pages):
    async def fetch(url, token, params, *, lang="en", transport=None):
        calls.append((url, dict(params)))
        raw, cursor, error = pages.pop(0)
        if raw is None:
            return None, error
        return {
            "items": [library_row(i, lang) for i in raw],
            "raw": raw,
            "next_cursor": cursor,
        }, ""

    return fetch


async def _drain(handler, state, *args):
    async for _ in handler.fn(state, *args):
        pass


def test_base_scenarios_tab_lists_saved_scenarios_read_only(stored_cases, monkeypatch):
    base = stored_cases[1]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))
    first = [_scenario_item(base["case_id"]), _scenario_item(base["case_id"], "demand_change", 12)]
    more = [_scenario_item(base["case_id"], "price_change")]
    calls = []
    pages = [(first, "next-page", ""), (more, "", "")]
    patch_client(monkeypatch, "fetch_library", _scenario_pages(base["case_id"], calls, pages))

    asyncio.run(_drain(PlanningState.load_base_scenarios, state, False))
    assert calls[0][0].endswith(f"/{base['case_id']}/scenarios") and calls[0][1] == {}
    assert [r["scenario"] for r in state.base_scenarios] == [
        tr("kind_supplier_outage", "hu"),
        tr("kind_demand_change", "hu"),
    ]
    assert state.base_scenarios[1]["quantity"] == "12 db"
    assert state.base_scenarios[0]["outcome"] == tr("status_optimal", "hu")
    assert state.base_scenarios_cursor == "next-page" and not state.base_scenarios_loading

    asyncio.run(_drain(PlanningState.load_base_scenarios, state, True))
    assert calls[1][1] == {"cursor": "next-page"} and len(state.base_scenarios) == 3
    assert state.base_scenarios_cursor == ""
    asyncio.run(_drain(PlanningState.load_base_scenarios, state, True))  # no further page
    assert len(calls) == 2

    PlanningState.set_language.fn(state, "en")
    assert len(calls) == 2 and state.base_scenarios[2]["scenario"] == tr("kind_price_change", "en")


def test_base_scenarios_show_empty_and_error_and_never_load_for_a_scenario(
    stored_cases, monkeypatch
):
    base, child = stored_cases[1], stored_cases[2]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))
    calls = []
    pages = [(None, "", tr("err_library", "hu")), ([], "", "")]
    patch_client(monkeypatch, "fetch_library", _scenario_pages(base["case_id"], calls, pages))

    asyncio.run(_drain(PlanningState.load_base_scenarios, state, False))
    assert state.base_scenarios_error == UI_TEXT["err_base_scenarios"][0]
    assert state.base_scenarios == []
    asyncio.run(_drain(PlanningState.load_base_scenarios, state, False))  # Retry
    assert state.base_scenarios_error == "" and state.base_scenarios == []
    assert state.base_scenarios_case == base["case_id"]
    assert UI_TEXT["no_scenarios"][0] == "Ehhez az ügyhöz még nincs forgatókönyv."

    # Saving a scenario shows the child: the base list is dropped and reloads on return.
    state._show(_map_case(child, child["case_id"], "hu"))
    assert state.base_scenarios_case == "" and state.base_scenarios == []
    asyncio.run(_drain(PlanningState.load_base_scenarios, state, False))
    assert len(calls) == 2


def test_base_scenarios_page_for_a_case_no_longer_open_is_dropped(stored_cases, monkeypatch):
    base, child = stored_cases[1], stored_cases[2]
    state = PlanningState(_reflex_internal_init=True)
    state._show(_map_case(base, base["case_id"], "hu"))

    async def fetch(url, token, params, *, lang="en", transport=None):
        state._show(_map_case(child, child["case_id"], "hu"))  # another case opened meanwhile
        raw = [_scenario_item(base["case_id"])]
        return {"items": [library_row(i, lang) for i in raw], "raw": raw, "next_cursor": ""}, ""

    patch_client(monkeypatch, "fetch_library", fetch)
    asyncio.run(_drain(PlanningState.load_base_scenarios, state, False))
    assert state.base_scenarios == [] and not state.base_scenarios_loading


def test_a_search_submitted_during_a_library_reload_is_applied(monkeypatch):
    # Returning to Cases re-runs on_load while the list from the earlier visit is still loaded.
    state = PlanningState(_reflex_internal_init=True)
    state.library_loaded = True
    calls = []

    async def fetch(url, token, params, *, lang="en", transport=None):
        calls.append(dict(params))
        if len(calls) == 1:  # the buyer presses Enter while the reload is on its way
            await _drain(PlanningState.refresh_library, state, {"q": " nincs-ilyen-termek "})
            assert len(calls) == 1 and state.library_loading
        return {"items": [], "raw": [], "next_cursor": ""}, ""

    patch_client(monkeypatch, "fetch_library", fetch)
    asyncio.run(_drain(PlanningState.library_on_load, state))
    assert [c["q"] for c in calls] == ["", "nincs-ilyen-termek"]
    assert state.library_search == "nincs-ilyen-termek" and not state.library_loading


def test_library_filters_stay_usable_while_a_loaded_list_reloads():
    from frontend.planning.library import _filters

    rendered = str(_filters())
    start = rendered.index('id:"library-search"')
    search = rendered[rendered.rindex("jsx(", 0, start) : start]
    assert "library_loaded" in search and "library_loading" not in search


def test_plan_proved_only_by_the_balanced_stage_is_named_and_shows_largest_share(stored_cases):
    payload = deepcopy(stored_cases[1])
    for run in payload["snapshot"]["result"]["runs"]:
        if run["plan_index"] == 1:
            run["kind"] = "diversified"
    display = _map_case(payload, payload["case_id"], "hu")
    assert display.plans[1]["title"] == "Kiegyensúlyozott terv"
    assert display.plans[1]["balanced"] == ""  # the title already says it
    assert display.plans[0]["largest_share"].endswith("%")
