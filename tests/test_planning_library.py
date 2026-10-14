"""Library trust boundaries, stored summaries, bookmark and pending-write safety."""

import asyncio
import base64
import json
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
import reflex as rx
from reflex.istate.data import RouterData

from application.decision_cases import RepositoryError
from application.planning_library import case_summary, library_query, list_planning_cases
from application.planning_serialization import snapshot_json
from backend.app.config import settings
from backend.app.main import app
from frontend.planning.library import library_page
from frontend.planning.state import PlanningState
from frontend.planning_library_client import fetch_library
from tests.test_t17_decisions import configured as _configured
from tests.test_t17_decisions import headers, intent
from tests.test_t17_decisions import stored_cases as _stored_cases

configured = _configured
stored_cases = _stored_cases
BASE = "/api/v2/procurement/planning-cases"


@pytest.mark.parametrize(
    "params",
    [
        {"workspace": "all"},
        {"status": "approve"},
        {"q": "x" * 81},
        {"limit": 0},
        {"limit": 51},
        {"limit": True},
        {"cursor": "!"},
        {"cursor": "x" * 1025},
        {"parent_id": "not-a-uuid"},
    ],
)
def test_query_rejects_invalid_filters(params):
    with pytest.raises(ValueError):
        library_query("company", **params)


def test_cursor_binds_every_filter_and_scope():
    query = library_query("company", "unclassified", q="  product  ")
    assert query.q == "product" and query.limit == 20
    value = {"context": query.context, "time": datetime.now(UTC).isoformat(), "id": str(uuid4())}
    cursor = base64.urlsafe_b64encode(json.dumps(value).encode()).decode()
    assert library_query("company", "unclassified", q="product", cursor=cursor).after
    for changes in (
        {"company": "other"},
        {"status": "approved"},
        {"workspace": "practice"},
        {"q": "other"},
        {"limit": 10},
        {"parent_id": str(uuid4())},
    ):
        with pytest.raises(ValueError):
            library_query(
                **(
                    {
                        "company": "company",
                        "workspace": "unclassified",
                        "q": "product",
                        "cursor": cursor,
                    }
                    | changes
                )
            )
    for time in ("2026-01-01T00:00:00", "2026-01-01T00:00:00+02:00"):
        value["time"] = time
        with pytest.raises(ValueError):
            library_query(
                "company",
                "unclassified",
                q="product",
                cursor=base64.urlsafe_b64encode(json.dumps(value).encode()).decode(),
            )
    with pytest.raises(RepositoryError):
        library_query("")


def test_http_validation_and_fail_closed_scope(configured, monkeypatch):
    client, uow, base, *_ = configured
    monkeypatch.setattr(settings, "planning_library_company_id", "")
    assert client.get(BASE, headers=headers()).status_code == 503
    assert client.get(BASE).status_code == 401
    monkeypatch.setattr(
        settings, "planning_library_company_id", base["snapshot"]["facts"]["company_id"]
    )
    for params in (
        {"company": "other"},
        {"workspace": "all"},
        {"status": "bad"},
        {"q": "x" * 81},
        {"limit": "-1"},
        {"limit": "51"},
        {"limit": "1.0"},
        {"cursor": "!"},
    ):
        assert client.get(BASE, params=params, headers=headers()).status_code == 422
    assert client.get(BASE + "?status=all&status=draft", headers=headers()).status_code == 422
    monkeypatch.setattr(
        uow,
        "list_saved",
        lambda query: [(uow.rows[base["case_id"]], "unclassified", None, None)],
        raising=False,
    )
    page = client.get(BASE, params={"workspace": "unclassified"}, headers=headers())
    assert page.status_code == 200
    summary = page.json()["items"][0]
    assert summary["workspace"] == "unclassified" and summary["decision_status"] == "draft"
    assert "snapshot" not in summary and "assessments" not in summary
    original = uow.rows[base["case_id"]]
    monkeypatch.setattr(
        uow,
        "list_saved",
        lambda query: [(replace(original, snapshot="{}"), "unclassified", None, None)],
    )
    response = client.get(BASE, headers=headers())
    assert (
        response.status_code == 503 and response.json()["detail"]["code"] == "invalid_library_data"
    )


def test_summaries_preserve_source_lineage_and_decision(configured):
    client, uow, base, child, _ = configured
    company = base["snapshot"]["facts"]["company_id"]
    row = case_summary(uow.rows[child["case_id"]], "unclassified", None, None, company)
    assert row["parent_id"] == base["case_id"] and row["scenario_kind"]
    assert row["changed_assumptions"] == {
        k: child["snapshot"]["scenario"][k] for k in ("approved_quantity", "suppliers")
    }
    client.post(f"{BASE}/{base['case_id']}/final-decision", json=intent(base), headers=headers())
    assert (
        case_summary(
            uow.rows[base["case_id"]],
            "unclassified",
            None,
            uow.decisions.get(base["case_id"]),
            company,
        )["decision_status"]
        == "approved"
    )
    with pytest.raises(ValueError):
        list_planning_cases(uow, library_query(company, parent_id=child["case_id"]))
    with pytest.raises(RepositoryError):
        case_summary(uow.rows[base["case_id"]], "unclassified", None, None, "other")
    invalid = deepcopy(child["snapshot"])
    invalid["scenario"]["suppliers"][0]["available"] = True
    with pytest.raises(RepositoryError):
        case_summary(
            replace(uow.rows[child["case_id"]], snapshot=snapshot_json(invalid)),
            "unclassified",
            None,
            None,
            company,
        )


def test_library_http_client_unavailable_and_invalid_data():
    async def flow():
        for response in (
            httpx.Response(503),
            httpx.Response(200, json={"items": [{}], "next_cursor": None}),
        ):
            page, error = await fetch_library(
                "http://test", "secret", {}, transport=httpx.MockTransport(lambda request: response)
            )
            assert page is None and error and "secret" not in error

    asyncio.run(flow())


def test_bookmark_clear_invalid_previous_and_pending_guard(configured, monkeypatch):
    from frontend.config import settings as frontend_settings
    from frontend.planning_client import fetch_planning_case

    _, _, base, *_ = configured
    monkeypatch.setattr(frontend_settings, "backend_base_url", "http://test")

    async def fetch(url, case_id, token):
        return await fetch_planning_case(
            url, case_id, headers()["Authorization"][7:], transport=httpx.ASGITransport(app=app)
        )

    monkeypatch.setattr("frontend.planning.state.fetch_planning_case", fetch)

    async def flow():
        root = rx.State(_reflex_internal_init=True)
        state = root.get_substate(PlanningState.get_full_name().split("."))
        root.router = RouterData.from_router_data(
            {"asPath": "/planning?case_id=" + base["case_id"] + "&view=audit"}
        )
        async for _ in state.load_bookmark():
            pass
        assert state.has_case and state.view == "audit"
        root.router = RouterData.from_router_data(
            {"asPath": "/planning?case_id=" + base["case_id"] + "&view=bad"}
        )
        async for _ in state.load_bookmark():
            pass
        assert not state.has_case and not state.details
        state.has_pending = True
        state._pending = {"key": "same", "payload": {"quantity": 10}}
        before = deepcopy(state._pending)
        async for _ in state.load_bookmark():
            pass
        async for _ in state.library_on_load():
            pass
        assert state._pending == before and state.open_saved_case(base["case_id"]) is None
        assert state.open_library() is None
        root.router = RouterData.from_router_data({"asPath": state._pending_route})
        assert [event async for event in state.load_bookmark()] == []

    asyncio.run(flow())
    assert library_page()
