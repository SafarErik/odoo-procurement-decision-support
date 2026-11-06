"""Fixtures shared by the fast and integration tests.

Two generated histories exist on purpose: ``odoo_history`` ends at the fixed
``REFERENCE_NOW`` and backs cases with exact expected values; ``history`` ends at the
current hour for tests that let case creation read the real clock.
"""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings as backend_settings
from backend.app.main import app
from frontend.config import settings as frontend_settings
from frontend.odoo_history_client import fetch_odoo_history, fetch_quotation_groups
from frontend.planning.state import PlanningState
from frontend.planning_client import _map_case, submit_planning_request
from tests.helpers.frontend_patching import consume, patch_client
from tests.helpers.in_memory_uow import MemoryPlanningUnitOfWork
from tests.helpers.odoo_fakes import COMPANY, build_history, install_fake_odoo
from tests.helpers.planning_api import (
    TOKEN,
    controlled_terms,
    create_case,
    forbidden,
    odoo_case_api,
)

# Generated history, training split and saved cases all end here, so exact expected
# values do not depend on the day the suite runs (see ``planning_api.odoo_case_api``).
REFERENCE_NOW = datetime(2026, 11, 5, 18, tzinfo=UTC)


@pytest.fixture(scope="session")
def odoo_history(tmp_path_factory):
    """Generated Odoo-shaped purchase history and a tree trained on it, once per session."""
    return build_history(tmp_path_factory.mktemp("odoo-history"), REFERENCE_NOW)


@pytest.fixture(scope="module")
def history(tmp_path_factory):
    """Generated history and trained tree ending at the current hour (real clock)."""
    return build_history(tmp_path_factory.mktemp("history-model"))


@pytest.fixture
def fake_odoo(history, monkeypatch):
    """Fake read-only Odoo over ``history`` and an empty in-memory store: ``(calls, uow)``."""
    calls = install_fake_odoo(history, monkeypatch)
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    return calls, uow


@pytest.fixture(scope="module")
def stored_cases(odoo_history):
    """A stored Odoo-history base with two outage scenarios (one infeasible), via HTTP.

    Returns ``(uow, base, feasible_child, infeasible_child)``.
    """
    uow = MemoryPlanningUnitOfWork()
    with pytest.MonkeyPatch.context() as patch, odoo_case_api(odoo_history, uow, patch) as client:
        terms = controlled_terms(client)
        base = create_case(client, terms)
        children = []
        for selected in (terms["suppliers"][:1], terms["suppliers"]):
            child = client.post(
                f"/api/v2/procurement/planning-cases/{base['case_id']}/scenarios",
                json={
                    "kind": "supplier_outage",
                    "source": terms["requirement_source"],
                    "suppliers": [
                        {"supplier_id": s["supplier_id"], "available": False} for s in selected
                    ],
                },
                headers={"Idempotency-Key": str(uuid4())},
            )
            assert child.status_code == 201, child.text
            children.append(child.json())
    return uow, base, *children


@pytest.fixture
def decision_api(stored_cases, monkeypatch):
    """HTTP client over a copy of ``stored_cases`` where Odoo, scoring and solving are forbidden.

    Yields ``(client, uow, base, child, infeasible)``.
    """
    original, base, child, infeasible = stored_cases
    uow = MemoryPlanningUnitOfWork()
    uow.rows = original.rows.copy()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(backend_settings, "api_service_token", SecretStr(TOKEN))
    for name in (
        "infer_odoo_history_features",
        "planning_solver_factory",
        "resolve_odoo_history_input",
    ):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    for name in ("assemble_planning_input", "create_procurement_plans"):
        monkeypatch.setattr(f"application.planning_cases.{name}", forbidden)
    with TestClient(app) as client:
        yield client, uow, base, child, infeasible


@pytest.fixture
def scenario_state(stored_cases, monkeypatch):
    """English cockpit showing the stored base, posting scenarios to the real API and CBC.

    Odoo and scoring are forbidden. Returns ``(state, uow, base, posts, transport)``.
    """
    existing, base, _, _ = stored_cases
    uow = MemoryPlanningUnitOfWork()
    uow.rows = dict(existing.rows)
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    for name in ("infer_odoo_history_features", "resolve_odoo_history_input"):
        monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
    monkeypatch.setattr("application.planning_cases.assemble_planning_input", forbidden)
    monkeypatch.setattr(backend_settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    transport, calls = httpx.ASGITransport(app=app), []

    async def post(url, body, key, token, lang="en"):
        calls.append((url, deepcopy(body), key))
        return await submit_planning_request(url, body, key, token, lang=lang, transport=transport)

    patch_client(monkeypatch, "submit_planning_request", post)
    state = PlanningState(_reflex_internal_init=True)
    state.lang = "en"  # the assertions read English texts
    state._show(_map_case(base, base["case_id"]))
    return state, uow, base, calls, transport


@pytest.fixture
def prepared_state(fake_odoo, monkeypatch):
    """A cockpit that listed the open groups, chose group 501 and read its history preview.

    Returns ``(state, form)`` with the form prefilled from the preview's terms.
    """
    asgi = httpx.ASGITransport(app=app)
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://api.test")
    monkeypatch.setattr(frontend_settings, "api_service_token", SecretStr(TOKEN))
    monkeypatch.setattr(backend_settings, "planning_library_company_id", COMPANY)
    for name, function in (
        ("fetch_quotation_groups", fetch_quotation_groups),
        ("fetch_odoo_history", fetch_odoo_history),
    ):

        async def through_api(*args, function=function, **kwargs):
            return await function(*args, **kwargs, transport=asgi)

        patch_client(monkeypatch, name, through_api)
    state = PlanningState(_reflex_internal_init=True)
    state.lang = "en"  # the assertions read English texts
    consume(state, PlanningState.load_quotation_groups)
    assert [g["value"] for g in state.quotation_groups] == ["501"], state.error_message
    assert (
        state.selected_group == "501"
        and "T6 Comparison Product" in (state.quotation_groups[0]["label"])
    )
    consume(state, PlanningState.load_odoo_history)
    assert state.odoo_ready and state.odoo_history_mode, state.error_message
    terms = state._odoo_payload["controlled_input"]
    form = {
        "odoo_quantity": str(terms["requirement"]["approved_quantity"]),
        "odoo_required_date": terms["requirement"]["required_date"],
    }
    for s in terms["suppliers"]:
        form.update(
            {
                s["supplier_id"] + "_capacity": str(s["capacity"]),
                s["supplier_id"] + "_moq": "5",
                s["supplier_id"] + "_promised_date": s["promised_date"],
                **{
                    f"{s['supplier_id']}_{name}_{end}": str(s[f"{name}_quantities"][bound])
                    for name in ("price", "delivery")
                    for end, bound in (("min", "minimum"), ("max", "maximum"))
                },
            }
        )
    return state, form
