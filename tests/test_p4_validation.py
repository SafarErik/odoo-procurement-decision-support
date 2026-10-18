"""P4 validation tools: evaluation groups seeding, reference optimum, latency and demo report."""

import json
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from fastapi.testclient import TestClient

from backend.app.main import app
from tests.test_odoo_purchase_history import configured as _configured
from tests.test_odoo_purchase_history import history as _history
from tests.test_t13_planning import request, scored, supplier
from tools import demo
from tools.milp_evaluation import (
    describe,
    measure_workload,
    nearest_rank,
    reference_plans,
    solver_check,
    variants,
)
from tools.seed_odoo_history import (
    ALLOWED_DATABASE,
    OdooWriter,
    apply_evaluation_groups,
    build_plan,
    evaluation_groups,
)

configured, history = _configured, _history
TOKEN = {"Authorization": "Bearer history-test-token"}
BASE = "/api/v2/procurement/planning-cases"
CLOCK = datetime(2026, 10, 17, tzinfo=UTC)


# --- Seeder: evaluation quotation groups ----------------------------------------------


def test_evaluation_groups_are_deterministic_nested_and_quote_the_rfq_product():
    plan = build_plan(CLOCK)
    groups = evaluation_groups(plan)
    assert groups == evaluation_groups(build_plan(CLOCK))
    assert {size: len(codes) for size, codes in groups.items()} == {5: 5, 10: 10}
    assert groups[5][:4] == plan.rfq_suppliers and groups[10][:5] == groups[5]
    suppliers = {s.code: s for s in plan.suppliers}
    assert all(plan.rfq_product in suppliers[c].products for c in groups[10])
    assert len(set(groups[10])) == 10


def fake_odoo(existing_groups=False):
    calls = []

    def respond(request):
        model, method = request.url.path.split("/")[-2:]
        body = json.loads(request.content)
        calls.append((model, method, body))
        if (model, method) == ("ir.config_parameter", "get_param"):
            return httpx.Response(200, json=ALLOWED_DATABASE)
        if (model, method) == ("res.users", "context_get"):
            return httpx.Response(200, json={"uid": 2})
        if (model, method) == ("res.users", "has_group"):
            return httpx.Response(200, json=True)
        if (model, method) == ("product.product", "search_read"):
            return httpx.Response(200, json=[{"id": 42, "uom_id": [1, "Units"]}])
        if (model, method) == ("res.company", "search_read"):
            return httpx.Response(200, json=[{"id": 1}])
        if (model, method) == ("purchase.order", "search_read"):
            return httpx.Response(200, json=[{"purchase_group_id": [7, "G"]}] * existing_groups)
        if (model, method) == ("res.partner", "search_read"):
            refs = body["domain"][0][2]
            return httpx.Response(200, json=[{"id": 100 + i, "ref": r} for i, r in enumerate(refs)])
        if (model, method) == ("purchase.order", "create"):
            return httpx.Response(200, json=[len(calls)])
        if (model, method) == ("purchase.order.group", "create"):
            return httpx.Response(200, json=[len(calls)])
        raise AssertionError((model, method))

    writer = OdooWriter(
        "http://odoo.test", ALLOWED_DATABASE, "key", transport=httpx.MockTransport(respond)
    )
    return writer, calls


def test_evaluation_groups_write_tagged_rfqs_after_target_check_and_reuse_on_rerun():
    plan = build_plan(CLOCK)
    writer, calls = fake_odoo()
    groups = apply_evaluation_groups(plan, writer, log=lambda _: None)
    assert calls[0][:2] == ("ir.config_parameter", "get_param")
    created = [body["vals_list"][0] for m, method, body in calls if (m, method) == (
        "purchase.order", "create"
    )]  # fmt: skip
    assert len(created) == 15 and set(groups) == {5, 10}
    assert all(v["origin"].startswith("PDSS-GEN-P1:RFQ") for v in created)
    assert all(v["partner_ref"] == "PDSS-GEN-P1" for v in created)
    assert all(v["order_line"][0][2]["product_qty"] == 200 for v in created)

    writer, calls = fake_odoo(existing_groups=True)
    assert apply_evaluation_groups(plan, writer, log=lambda _: None) == {5: 7, 10: 7}
    assert not [c for c in calls if c[1] == "create"]


# --- Reference optimum and invariants -------------------------------------------------


def test_nearest_rank_p95_uses_the_29th_of_30_values():
    values = [i / 1000 for i in range(1, 31)]
    assert nearest_rank(values, 0.95) == 0.029
    assert describe(values)["p95_ms"] == 29.0 and describe(values)["n"] == 30


def test_solver_matches_exhaustive_reference_on_controlled_variants():
    data = scored(
        request(
            quantity=12,
            suppliers=(
                supplier("A", "2", 8),
                supplier("B", "2.5", 8),
                supplier("C", "3", 12),
                supplier("D", "2", 6),
            ),
            concentration=Decimal("0.8"),
        ),
        values=("0.8", "0.4", "0", "0.6"),
        epsilons=(Decimal("0.05"), Decimal("0.1"), Decimal("0.3")),
    )
    checks = {name: solver_check(name, v, 2, 0) for name, v in variants(data)}
    for name, check in checks.items():
        assert check["reference_match"], (name, check["failures"])
        assert check["repeated_identical"] and check["permutation_identical"], name
    assert checks["stored_request"]["status"] == "optimal"
    assert checks["stored_request"]["distinct_alternatives"] >= 1
    # Equal prices: the tie-break gives the earliest supplier ids the largest quantities.
    assert checks["equal_prices_tie_break"]["minimum_cost_quantities"] == {
        "A": 8,
        "B": 4,
        "C": 0,
        "D": 0,
    }
    for name in (
        "max_suppliers_1_infeasible",
        "moq_combination_infeasible",
        "demand_x5_infeasible",
    ):
        assert checks[name]["status"] == "infeasible" and not checks[name]["reference_feasible"]


def test_reference_detects_a_wrong_plan():
    data = scored(request(quantity=10))
    expected = reference_plans(data)
    assert expected["minimum"] == (6, 4, 0)
    from tools.milp_evaluation import check_result, timed_solve

    result, _, runs = timed_solve(data)
    assert runs >= 1 and check_result(data, result, expected) == []
    assert check_result(data, result, expected | {"minimum": (4, 6, 0)}) == [
        "minimum-cost plan differs from the reference optimum"
    ]


# --- HTTP latency and demo report on the fake Odoo ------------------------------------


def test_measure_workload_times_create_scenario_retry_and_get(configured):
    _, uow = configured
    with TestClient(app, headers=TOKEN) as client:
        terms = client.get(f"{BASE}/odoo-history/preview?purchase_group_id=501").json()["terms"]
        measured = measure_workload(client, 501, terms, ("0.05", "0.1", "0.2"), 2, 1)
    assert set(measured["latency"]) == {"create", "scenario", "exact_retry", "get"}
    assert all(v["n"] == 2 for v in measured["latency"].values())
    assert measured["infeasible_scenario_status"] == "infeasible"
    assert measured["distinct_minimum_cost_allocations"] == 1
    assert measured["base"]["snapshot"]["request"]["policy"]["epsilons"] == ["0.05", "0.1", "0.2"]
    assert len(uow.rows) == 3 * 2 + 1  # (base + scenario) per run, one infeasible scenario


def test_demo_runs_flow_replays_and_writes_summary(configured, monkeypatch, tmp_path):
    with TestClient(app, headers=TOKEN) as client:

        @contextmanager
        def same_client(env, token, log):
            yield client

        monkeypatch.setattr(demo, "api", same_client)
        monkeypatch.setattr(demo, "_env", lambda: {"API_SERVICE_TOKEN": "t", "ODOO_DATABASE": "x"})
        monkeypatch.setattr(
            demo,
            "open_groups",
            lambda client: [
                {
                    "purchase_group_id": 501,
                    "supplier_count": 3,
                    "product_name": "Product",
                    "quantity": "200",
                    "currency": "USD",
                    "quotations": [{"supplier_id": "s", "supplier_name": "Supplier"}],
                }
            ],
        )
        # The fake Odoo keeps answering; the isolation probe must then refuse the run.
        report = tmp_path / "report.json"
        args = ["--directory", str(tmp_path), "--report", str(report)]
        assert demo.main(args) == 1 and not report.exists()

        real_get = client.get

        def unreachable_preview(url, **kwargs):
            if url.endswith("/odoo-history/preview") and calls["isolated"]:
                return httpx.Response(503, json={})
            return real_get(url, **kwargs)

        calls = {"isolated": False}
        original_api = same_client

        @contextmanager
        def phased(env, token, log):
            calls["isolated"] = env.get("ODOO_BASE_URL") == demo.ISOLATED["ODOO_BASE_URL"]
            with original_api(env, token, log) as c:
                yield c

        monkeypatch.setattr(demo, "api", phased)
        monkeypatch.setattr(client, "get", unreachable_preview)
        assert demo.main(args) == 0
    summary = json.loads(report.read_text())
    assert (
        summary["stored_replay"]["passed"]
        and summary["stored_replay"]["odoo_preview_status"] == 503
    )
    assert set(summary["pdf"]) == {"hu", "en"}
    assert summary["decisions"]["no_award"]["outcome"] == "no_award"
    kinds = {s["kind"] for s in summary["scenarios"]}
    assert kinds == {
        "supplier_outage",
        "capacity_change",
        "demand_change",
        "price_change",
        "combined",
    }
    assert summary["scenarios"][-1]["status"] == "infeasible"
    assert summary["base_case"]["plans"][0]["label"] == "minimum_cost"
    assert len(summary["supplier_assessment"]) == 3
