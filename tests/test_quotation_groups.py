"""P2 open quotation-group selection: bounded, company-scoped, read-only listing."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings
from backend.app.main import app
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from tests.test_odoo_comparison_case_adapter import _payloads

URL = "/api/v2/procurement/quotation-groups"
TOKEN = "groups-test-token"


def _odoo(groups):
    """Fake JSON-2 Odoo with several groups; records every call for read-only checks."""
    orders, lines, partners = [], [], {}
    for group_id, offers in groups.items():
        base = _payloads()
        for index, order in enumerate(base["orders"][: len(offers)]):
            order_id = group_id * 10 + index
            line = dict(base["lines"][index], id=order_id * 10, order_id=[order_id, "x"])
            line["product_id"] = [42, "Bolt M8"]
            line.update(offers[index])
            order.update(
                id=order_id,
                name=f"RFQ-{order_id}",
                purchase_group_id=[group_id, f"GROUP-{group_id}"],
                order_line=[line["id"]],
                date_order=f"2026-10-{10 + group_id % 10:02d} 08:00:00",
                state=offers[index].pop("state", order["state"]) if offers[index] else "draft",
            )
            line.pop("state", None)
            orders.append(order)
            lines.append(line)
            partner = order["partner_id"][0]
            partners[partner] = {"id": partner, "commercial_partner_id": order["partner_id"]}
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append((request.url.path.rsplit("/json/2/", 1)[1], body))
        path = request.url.path
        if path.endswith("purchase.order/search_read") and body["fields"] == [
            "id",
            "purchase_group_id",
        ]:
            assert ["company_id", "=", 1] in body["domain"] and body["limit"] == 200
            open_states = next(d[2] for d in body["domain"] if d[0] == "state")
            scanned = [o for o in orders if o["state"] in open_states]
            return httpx.Response(200, json=sorted(scanned, key=lambda o: -o["id"]))
        if path.endswith("purchase.order/search_count"):
            ids = body["domain"][1][2]
            return httpx.Response(200, json=sum(o["purchase_group_id"][0] in ids for o in orders))
        if path.endswith("purchase.order/search_read"):
            ids = body["domain"][1][2]
            return httpx.Response(200, json=[o for o in orders if o["purchase_group_id"][0] in ids])
        if path.endswith("purchase.order.line/search_read"):
            ids = body["domain"][0][2]
            return httpx.Response(200, json=[x for x in lines if x["id"] in ids])
        if path.endswith("res.partner/search_read"):
            return httpx.Response(200, json=list(partners.values()))
        raise AssertionError(path)

    return httpx.MockTransport(respond), calls


@pytest.fixture
def client(monkeypatch):
    def configure(groups, company="odoo:res.company:1"):
        transport, calls = _odoo(groups)
        monkeypatch.setattr(
            "backend.app.dependencies.get_comparison_case_reader",
            lambda: OdooComparisonCaseReader(
                base_url="http://odoo.test", database="db", api_key="k", transport=transport
            ),
        )
        monkeypatch.setattr(settings, "planning_library_company_id", company)
        monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
        return TestClient(app), calls

    return configure


def get(client, query=""):
    return client.get(URL + query, headers={"Authorization": f"Bearer {TOKEN}"})


def test_lists_selectable_groups_with_product_suppliers_and_currency(client):
    test_client, calls = client({7: [{}, {}, {}]})
    response = get(test_client)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["company_id"] == "odoo:res.company:1" and data["count"] == 1
    group = data["items"][0]
    assert group["purchase_group_id"] == 7 and group["name"] == "GROUP-7"
    assert (group["product_id"], group["product_name"]) == ("odoo:product.product:42", "Bolt M8")
    assert group["currency"] == "USD" and group["quantity"] == "100.0"
    assert group["selectable"] is True and group["issue"] is None
    assert group["supplier_count"] == 3
    assert [q["supplier_name"] for q in group["quotations"]] == [
        "T6 Supplier A",
        "T6 Supplier B",
        "T6 Supplier C",
    ]
    assert group["quotations"][0]["lines"][0]["unit_price"] == "10.0"
    # Read-only: only search/read methods, never a write.
    assert {path.rsplit("/", 1)[1] for path, _ in calls} == {"search_read", "search_count"}


def test_flags_groups_that_cannot_become_cases(client):
    test_client, _ = client(
        {
            1: [{}, {}],  # two offers only
            2: [{}, {}, {"state": "purchase"}],  # one already confirmed
            3: [{}, {}, {"tax_ids": [5]}],
            4: [{}, {}, {"product_id": [43, "Nut M8"]}],
        }
    )
    issues = {g["purchase_group_id"]: g["issue"] for g in get(test_client).json()["items"]}
    assert issues == {
        1: "unsupported_offer_count",
        2: "not_all_open",
        3: "discount_or_tax",
        4: "mixed_context",
    }


def test_limit_bounds_groups_and_reports_truncation(client):
    test_client, calls = client({n: [{}, {}, {}] for n in range(1, 6)})
    data = get(test_client, "?limit=2").json()
    assert data["count"] == 2 and data["truncated"] is True
    count_call = next(body for path, body in calls if path.endswith("search_count"))
    assert len(count_call["domain"][1][2]) == 2
    assert get(test_client, "?limit=21").status_code == 422
    assert get(test_client, "?limit=0").status_code == 422


def test_requires_token_and_configured_odoo_company(client):
    test_client, _ = client({7: [{}, {}, {}]})
    assert test_client.get(URL).status_code == 401
    test_client, calls = client({7: [{}, {}, {}]}, company="synthetic-company")
    response = get(test_client)
    assert response.status_code == 503 and calls == []
    assert response.json()["detail"]["code"] == "quotation_groups_unconfigured"


def test_unreachable_and_invalid_odoo_map_to_stable_errors(monkeypatch):
    monkeypatch.setattr(settings, "planning_library_company_id", "odoo:res.company:1")
    monkeypatch.setattr(settings, "api_service_token", SecretStr(TOKEN))
    for transport, status in (
        (httpx.MockTransport(lambda r: (_ for _ in ()).throw(httpx.ConnectError("x"))), 503),
        (httpx.MockTransport(lambda r: httpx.Response(200, json={"bad": 1})), 502),
    ):
        monkeypatch.setattr(
            "backend.app.dependencies.get_comparison_case_reader",
            lambda transport=transport: OdooComparisonCaseReader(
                base_url="http://odoo.test", database="db", api_key="k", transport=transport
            ),
        )
        assert get(TestClient(app)).status_code == status
