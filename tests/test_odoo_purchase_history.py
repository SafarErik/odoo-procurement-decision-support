"""Odoo purchase history -> features/labels -> trained tree -> saved planning case (P1)."""

import asyncio
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.errors import RepositoryError
from application.planning_cases import validate_snapshot
from application.planning_history import capture_features, capture_origin
from application.planning_serialization import snapshot_json
from application.purchase_history import (
    PurchaseHistoryQuery,
    PurchaseLineHistory,
    ReceiptEvent,
)
from application.rfqs import ProcurementDataResponseError
from backend.app.config import settings
from backend.app.main import app
from frontend.planning_client import _map_case
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.product_history_reader import OdooProductHistoryReader
from supplier_evaluation.contracts import (
    HISTORY_FEATURES,
    Context,
    QuantityValidity,
    canonical,
    digest,
)
from supplier_evaluation.history_model import (
    check_manifest_metadata,
    evaluate,
    load_model,
    path_text,
    save_model,
    train,
)
from supplier_evaluation.purchase_history import (
    build_rows,
    feature_snapshot,
    feature_values,
    problematic_label,
    split_rows,
)
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tests.test_odoo_comparison_case_adapter import _payloads
from tools.seed_odoo_history import (
    ALLOWED_DATABASE,
    OdooWriter,
    SeedRefused,
    build_plan,
    plan_summary,
)

BASE = "/api/v2/procurement/planning-cases"
DATABASE = ALLOWED_DATABASE
COMPANY = "odoo:res.company:1"
PRODUCTS = {"PRD-01": 42, "PRD-02": 43, "PRD-03": 44}
QUOTED = (1, 4, 6)  # SUP-01 reliable, SUP-04 steady late, SUP-06 deteriorating; all sell PRD-01
ADDON = (
    Path(__file__).resolve().parents[1]
    / "infra/odoo/addons/t7s_inventory_history_projection/product_history_policy.py"
)


def _policy():
    spec = importlib.util.spec_from_file_location("pdss_product_history_policy", ADDON)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


policy = _policy()
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def line(n, expected, receipts, *, confirmed=None, qty="100", supplier="odoo:res.partner:9"):
    return PurchaseLineHistory(
        f"odoo:purchase.order.line:{n}",
        f"odoo:purchase.order:{n}",
        COMPANY,
        supplier,
        "odoo:product.product:42",
        "odoo:uom.uom:1",
        Decimal(qty),
        expected,
        confirmed or expected - timedelta(days=10),
        tuple(
            ReceiptEvent(f"odoo:stock.move:{n}{i}", at, Decimal(q))
            for i, (at, q) in enumerate(receipts)
        ),
    )


def plan_lines(now):
    """The seeder's generated plan as neutral Odoo-shaped history (no Odoo involved)."""
    plan = build_plan(now)
    out = []
    for n, order in enumerate(plan.orders, 1):
        out.append(
            PurchaseLineHistory(
                f"odoo:purchase.order.line:{n}",
                f"odoo:purchase.order:{n}",
                COMPANY,
                f"odoo:res.partner:{300 + int(order.supplier[4:])}",
                f"odoo:product.product:{PRODUCTS[order.product]}",
                "odoo:uom.uom:1",
                Decimal(order.quantity),
                order.expected_at,
                order.ordered_at + timedelta(hours=2),
                tuple(
                    ReceiptEvent(f"odoo:stock.move:{n}{i}", r.at, Decimal(r.quantity))
                    for i, r in enumerate(order.receipts)
                ),
            )
        )
    return tuple(out)


@pytest.fixture(scope="module")
def history(tmp_path_factory):
    return build_history(tmp_path_factory.mktemp("history-model"))


def build_history(directory):
    """Generated Odoo-shaped history and a tree trained on it, saved in ``directory``."""
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    lines = plan_lines(now)
    rows, coverage = build_rows(lines, extracted_at=now)
    boundary = max(r.cutoff for r in rows) - timedelta(days=92)
    boundary = boundary.replace(day=1 if boundary.day < 16 else 16)
    split = split_rows(rows, boundary=boundary)
    model = train(split, database=DATABASE, data_origin="generated")
    save_model(model, directory)
    return {
        "now": now,
        "lines": lines,
        "rows": rows,
        "split": split,
        "model": model,
        "dir": directory,
    }


# --- Odoo addon export policy ---------------------------------------------------------


def _request(**overrides):
    values = {
        "company_id": 1,
        "product_id": 42,
        "date_from": "2026-01-01 00:00:00",
        "date_to": "2026-03-01 00:00:00",
        "limit": 10,
        "now": datetime(2026, 3, 2),
    }
    return policy.validate_product_request(**(values | overrides))


def _evidence():
    return {
        "lines": [
            {"id": 10, "purchase_order_id": 20, "product_id": 42, "product_uom_id": 1,
             "ordered_quantity": "100.0", "expected_arrival_at": "2026-01-10 12:00:00",
             "company_id": 1, "qty_received_method": "stock_moves"}
        ],
        "orders": [{"id": 20, "supplier_id": 40, "company_id": 1, "state": "purchase",
                    "confirmed_at": "2026-01-01 09:00:00"}],
        "partners": [{"id": 40, "commercial_partner_id": 41}],
        "moves": [
            {"id": 50 + i, "purchase_order_line_id": 10, "stock_picking_id": 60 + i,
             "product_id": 42, "product_uom_id": 1, "quantity": q, "state": "done",
             "processed_at": at, "company_id": 1, "source_location_usage": src,
             "destination_location_usage": dst, "return_of_move_id": ret}
            for i, (q, at, src, dst, ret) in enumerate((
                ("40.0", "2026-01-10 08:00:00", "supplier", "internal", None),
                ("60.0", "2026-01-15 08:00:00", "supplier", "internal", None),
                ("5.0", "2026-01-20 08:00:00", "internal", "supplier", 50),
            ))
        ],
        "pickings": [
            {"id": 60, "state": "done", "processed_at": "2026-01-10 08:00:00",
             "picking_type_code": "incoming", "backorder_of_picking_id": None, "company_id": 1},
            {"id": 61, "state": "done", "processed_at": "2026-01-15 08:00:00",
             "picking_type_code": "incoming", "backorder_of_picking_id": 60, "company_id": 1},
            {"id": 62, "state": "done", "processed_at": "2026-01-20 08:00:00",
             "picking_type_code": "outgoing", "backorder_of_picking_id": None, "company_id": 1},
        ],
    }  # fmt: skip


def test_export_policy_emits_lines_with_receipts_backorders_and_returns():
    records = policy.build_product_history(_request(), **_evidence())
    assert len(records) == 1 and tuple(records[0]) == policy.LINE_FIELDS
    record = records[0]
    assert record["commercial_partner_id"] == 41
    assert [r["quantity"] for r in record["receipts"]] == ["40.0", "60.0"]
    assert record["receipts"][1]["backorder_of_picking_id"] == 60
    assert record["returned_quantity"] == "5.0"
    assert record["order_confirmed_at"] == "2026-01-01 09:00:00"


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"limit": policy.MAX_LINES + 1}, "limit must not exceed"),
        ({"date_from": "2024-12-01 00:00:00"}, "must not exceed 366 days"),
        ({"date_to": "2026-04-01 00:00:00"}, "must not be in the future"),
        ({"product_id": True}, "product_id must be a positive integer"),
        ({"date_from": "2026-03-01 00:00:00"}, "earlier than date_to"),
    ],
)
def test_export_policy_rejects_unbounded_requests(overrides, message):
    with pytest.raises(policy.ProductHistoryPolicyError, match=message):
        _request(**overrides)


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda e: e["lines"][0].update(product_id=99), "another product"),
        (lambda e: e["lines"][0].update(company_id=2), "company boundary"),
        (lambda e: e["orders"][0].update(state="draft"), "state is unsupported"),
        (lambda e: e["moves"][0].update(product_uom_id=2), "product or unit"),
        (lambda e: e["pickings"][0].update(processed_at="2026-01-11 08:00:00"), "disagree"),
        (lambda e: e["lines"][0].update(expected_arrival_at="2026-03-05 00:00:00"), "window"),
    ],
)
def test_export_policy_fails_closed_on_ambiguous_evidence(mutate, message):
    evidence = _evidence()
    mutate(evidence)
    with pytest.raises(policy.ProductHistoryPolicyError, match=message):
        policy.build_product_history(_request(), **evidence)


# --- JSON-2 adapter ------------------------------------------------------------------


def export_response(lines, data):
    start = datetime.strptime(data["date_from"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    end = datetime.strptime(data["date_to"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    fmt = "%Y-%m-%d %H:%M:%S"
    chosen = [
        x
        for x in lines
        if x.product_id == f"odoo:product.product:{data['product_id']}"
        and start <= x.expected_at < end
    ]
    records = [
        {
            "purchase_order_line_id": int(x.line_id.rsplit(":", 1)[1]),
            "purchase_order_id": int(x.order_id.rsplit(":", 1)[1]),
            "commercial_partner_id": int(x.supplier_id.rsplit(":", 1)[1]),
            "product_uom_id": 1,
            "ordered_quantity": f"{x.ordered_quantity}.0",
            "expected_arrival_at": x.expected_at.strftime(fmt),
            "order_confirmed_at": x.confirmed_at.strftime(fmt),
            "receipts": [
                {"stock_move_id": int(r.event_id.rsplit(":", 1)[1]), "stock_picking_id": 1,
                 "processed_at": r.received_at.strftime(fmt), "quantity": f"{r.quantity}.0",
                 "backorder_of_picking_id": None}
                for r in x.receipts
            ],
            "returned_quantity": "0",
        }
        for x in chosen
    ]  # fmt: skip
    return {
        "schema_version": "pdss.product_history.v1",
        "company_id": data["company_id"],
        "product_id": data["product_id"],
        "date_from": data["date_from"],
        "date_to": data["date_to"],
        "result_count": len(records),
        "lines": records,
    }


def _reader(respond):
    return OdooProductHistoryReader(
        base_url="http://odoo.test",
        database=DATABASE,
        api_key="history-only",
        transport=httpx.MockTransport(respond),
    )


def test_reader_maps_export_to_neutral_lines(history):
    now = history["now"]
    query = PurchaseHistoryQuery(
        COMPANY, "odoo:product.product:42", now - timedelta(days=200), now - timedelta(days=100)
    )

    def respond(request):
        assert request.url.path.endswith("/procurement.product.history.export/read_product_history")
        assert request.headers["Authorization"] == "Bearer history-only"
        assert request.headers["X-Odoo-Database"] == DATABASE
        return httpx.Response(
            200, json=export_response(history["lines"], json.loads(request.content))
        )

    snapshot = asyncio.run(_reader(respond).read_purchase_history(query))
    assert snapshot.lines and snapshot.source_type == "odoo_purchase_history"
    assert f"|database={DATABASE}|" in snapshot.source_reference
    assert all(x.product_id == "odoo:product.product:42" for x in snapshot.lines)


@pytest.mark.parametrize("mutation", ["echo", "schema", "truncated", "count"])
def test_reader_rejects_inconsistent_or_truncated_exports(history, mutation):
    now = history["now"]
    query = PurchaseHistoryQuery(
        COMPANY, "odoo:product.product:42", now - timedelta(days=200), now - timedelta(days=100), 5
    )

    def respond(request):
        data = export_response(history["lines"], json.loads(request.content))
        if mutation == "echo":
            data["product_id"] = 43
        elif mutation == "schema":
            data["schema_version"] = "other"
        elif mutation == "count":
            data["result_count"] += 1
        else:
            data["lines"] = data["lines"][:5]
            data["result_count"] = 5
        return httpx.Response(200, json=data)

    with pytest.raises(ProcurementDataResponseError):
        asyncio.run(_reader(respond).read_purchase_history(query))


# --- Features and labels -------------------------------------------------------------


def test_features_use_only_what_was_known_at_the_cutoff():
    cutoff = T0 + timedelta(days=200)
    early = [
        line(1, cutoff - timedelta(days=100), [(cutoff - timedelta(days=101), "100")]),
        line(2, cutoff - timedelta(days=80), [(cutoff - timedelta(days=75), "100")]),
        line(3, cutoff - timedelta(days=60), [(cutoff - timedelta(days=60), "60"),
                                              (cutoff - timedelta(days=50), "40")]),
        # Received only after the cutoff: unknown at cutoff, so open and censored.
        line(4, cutoff - timedelta(days=30), [(cutoff + timedelta(days=1), "100")]),
    ]  # fmt: skip
    values = dict(zip(HISTORY_FEATURES, feature_values(early, cutoff), strict=True))
    assert values["order_count"] == 4
    assert values["on_time_rate"] == 0.5
    assert values["fill_rate"] == 0.75
    assert values["partial_share"] == 0.5
    assert values["mean_lateness_days"] == round((-1 + 5 + 0 + 30) / 4, 6)
    assert values["days_since_last_receipt"] == 50
    # A line confirmed after the cutoff, or due inside the 14-day gap, changes nothing.
    later = [
        *early,
        line(5, cutoff - timedelta(days=40), [], confirmed=cutoff + timedelta(hours=1)),
        line(6, cutoff - timedelta(days=5), []),
    ]
    assert feature_values(later, cutoff) == feature_values(early, cutoff)
    assert feature_values(early[:2], cutoff) is None


def test_problematic_label_uses_mean_delay_and_fill_in_the_next_window():
    cutoff = T0

    def due(delay_days, qty):
        return [
            line(
                i,
                cutoff + timedelta(days=10 * i),
                [(cutoff + timedelta(days=10 * i + delay_days), qty)],
            )
            for i in (1, 2)
        ]

    assert problematic_label(due(0, "100"), cutoff) == (0, cutoff + timedelta(days=74))
    assert problematic_label(due(4, "100"), cutoff)[0] == 1
    assert problematic_label(due(0, "80"), cutoff)[0] == 1
    assert problematic_label(due(0, "100")[:1], cutoff) is None


def test_split_is_supplier_disjoint_and_temporally_purged(history):
    split = history["split"]
    train_suppliers = {r.context.supplier_id for r in split.train}
    assert train_suppliers.isdisjoint({r.context.supplier_id for r in split.test})
    assert max(r.label_available_at for r in split.train) <= split.boundary
    assert min(r.cutoff for r in split.test + split.temporal_test) >= split.boundary
    assert {r.label for r in split.test} == {0, 1}


# --- Training, evaluation, artifact ---------------------------------------------------


def test_training_selects_depth_on_train_only_and_reports_baselines(history):
    model, split = history["model"], history["split"]
    selection = model.metadata["depth_selection"]
    assert str(selection["chosen"]) in selection["scores"]
    assert model.metadata["data_origin"] == "generated"
    assert model.metadata["training_id"] != "" and model.metadata["database"] == DATABASE
    report = evaluate(model, split)
    primary = report["primary_supplier_and_time_holdout"]
    assert set(primary["baselines"]) == {
        "majority_class",
        "expert_rule_on_time_below_80pct",
        "learned_single_split",
    }
    assert primary["rows"] == len(split.test)
    assert primary["decision_tree"]["confusion_matrix_labels_0_1"]
    assert all("support" in c for c in primary["decision_tree"]["per_class"])


def test_artifact_roundtrip_inference_and_readable_path(history, tmp_path):
    model, manifest = load_model(history["dir"], trusted_local=True)
    assert manifest["metadata"] == history["model"].metadata
    now = history["now"]
    context = Context("odoo:res.partner:304", COMPANY, "odoo:product.product:42", "odoo:uom.uom:1")
    snapshot = feature_snapshot(
        history["lines"], context, now, now, f"x|database={DATABASE}|company=1|capture=y"
    )
    assessment = model.infer(snapshot, QuantityValidity(1, 1000, "default"))
    assert assessment.mapping_version == "leaf-exposure-odoo-history-v2"
    text = path_text(assessment)
    assert len(text) == len(assessment.path) + 1 and "risk score" in text[-1]
    other = feature_snapshot(history["lines"], context, now, now, "x|database=other|c=1")
    with pytest.raises(ValueError, match="database"):
        model.infer(other, QuantityValidity(1, 1000, "default"))
    for name in ("manifest.json", "tree.joblib"):
        (tmp_path / name).write_bytes((history["dir"] / name).read_bytes())
    (tmp_path / "tree.joblib").write_bytes((tmp_path / "tree.joblib").read_bytes() + b"x")
    with pytest.raises(ValueError, match="checksum"):
        load_model(tmp_path, trusted_local=True)
    with pytest.raises(ValueError, match="trusted"):
        load_model(history["dir"])


# --- Backend case lifecycle ------------------------------------------------------------


def forbidden(*args, **kwargs):
    raise AssertionError("Stored operation re-read Odoo, scored or solved")


def install_fake_odoo(history, monkeypatch):
    """Fake read-only Odoo (group 501, its history) plus the trained history model."""
    payloads, calls = _payloads(), []
    for order, quote_line, partner, n in zip(
        payloads["orders"], payloads["lines"], payloads["partners"], QUOTED, strict=True
    ):
        order["partner_id"] = [300 + n, f"Supplier {n}"]
        order["date_order"] = "2026-10-15 08:00:00"
        partner.update(id=300 + n, commercial_partner_id=[300 + n, f"Supplier {n}"])
        quote_line["product_qty"] = 200.0

    def respond(request):
        data = json.loads(request.content)
        calls.append(request.url.path)
        assert request.headers["X-Odoo-Database"] == DATABASE
        if request.url.path.endswith("read_product_history"):
            assert request.headers["Authorization"] == "Bearer history-only"
            return httpx.Response(200, json=export_response(history["lines"], data))
        assert request.headers["Authorization"] == "Bearer rfq-only"
        path = request.url.path
        if path.endswith("purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if path.endswith("purchase.order/search_read"):
            return httpx.Response(200, json=payloads["orders"])
        if path.endswith("purchase.order.line/search_read"):
            return httpx.Response(200, json=payloads["lines"])
        if path.endswith("res.partner/search_read"):
            return httpx.Response(200, json=payloads["partners"])
        if path.endswith("res.currency/search_read"):
            return httpx.Response(200, json=[{"id": 2, "name": "USD"}])
        raise AssertionError(path)

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(
        "backend.app.dependencies.get_comparison_case_reader",
        lambda: OdooComparisonCaseReader(
            base_url="http://odoo.test", database=DATABASE, api_key="rfq-only", transport=transport
        ),
    )
    monkeypatch.setattr(
        "backend.app.dependencies.get_purchase_history_reader",
        lambda: OdooProductHistoryReader(
            base_url="http://odoo.test",
            database=DATABASE,
            api_key="history-only",
            transport=transport,
        ),
    )
    monkeypatch.setattr(settings, "odoo_database", DATABASE)
    monkeypatch.setattr(settings, "odoo_history_data_origin", "generated")
    monkeypatch.setattr(settings, "supplier_history_model_directory", history["dir"])
    monkeypatch.setattr(settings, "api_service_token", SecretStr("history-test-token"))
    return calls


@pytest.fixture
def configured(history, monkeypatch):
    calls = install_fake_odoo(history, monkeypatch)
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    return calls, uow


def headers(key=None):
    return {"Authorization": "Bearer history-test-token", "Idempotency-Key": key or str(uuid4())}


def test_odoo_history_case_lifecycle_and_stored_only_replay(configured, monkeypatch):
    calls, uow = configured
    with TestClient(app) as client:
        preview = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        )
        assert preview.status_code == 200, preview.text
        data = preview.json()
        assert data["model_readiness"] == "ready" and data["data_origin"] == "generated"
        assert len(data["history"]) == 3 and set(data["history"][0]) >= {
            "on_time_rate",
            "fill_rate",
        }
        payload = {"purchase_group_id": 501, "terms": data["terms"]}
        key = str(uuid4())
        response = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
        assert response.status_code == 201, response.text
        base = response.json()
        facts = base["snapshot"]["facts"]
        assert facts["source_type"] == "odoo_purchase_history"
        assert facts["comparison_case_id"] == "odoo:purchase.order.group:501"
        assert base["snapshot"]["model_manifest"]["metadata"]["data_origin"] == "generated"
        mapped = _map_case(base, base["case_id"])
        assert len(mapped.assessments) == 3
        assert all("settled lines" in a["history_summary"] for a in mapped.assessments)
        provenance = {p["canonical_path"]: p for p in base["snapshot"]["provenance"]["entries"]}
        for assessment in base["snapshot"]["assessments"]:
            supplier = assessment["snapshot"]["context"]["supplier_id"]
            assert provenance[f"facts.suppliers[{supplier}].receipts"]["source_type"] == (
                "odoo_purchase_history"
            )
        before = len(calls)
        for name in ("resolve_odoo_history_input", "infer_odoo_history_features"):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        replay = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
        assert replay.status_code == 200 and replay.json()["snapshot_hash"] == base["snapshot_hash"]
        scenario = {
            "kind": "supplier_outage",
            "source": payload["terms"]["policy_source"],
            "suppliers": [{"supplier_id": "odoo:res.partner:306", "available": False}],
        }
        child = client.post(
            BASE + f"/{base['case_id']}/scenarios", json=scenario, headers=headers()
        )
        assert child.status_code == 201, child.text
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        approved = client.post(
            BASE + f"/{base['case_id']}/final-decision",
            headers=headers(),
            json={
                "snapshot_hash": base["snapshot_hash"],
                "outcome": "approve",
                "plan_index": 0,
                "actor_reference": "test-owner",
                "demonstration_acknowledged": True,
            },
        )
        assert approved.status_code == 201, approved.text
        content_hash = approved.json()["final_decision"]["approved_content_hash"]
        pdf = client.get(
            BASE + f"/{base['case_id']}/approved-pdf/{content_hash}", headers=headers()
        )
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
        assert client.get(BASE + f"/{base['case_id']}", headers=headers()).status_code == 200
        monkeypatch.setattr(settings, "planning_library_company_id", facts["company_id"])
        monkeypatch.setattr(
            uow,
            "list_saved",
            lambda query: [(uow.rows[base["case_id"]], uow.decisions.get(base["case_id"]))],
            raising=False,
        )
        library = client.get(BASE, headers=headers())
        assert library.status_code == 200, library.text
        assert [i["origin"] for i in library.json()["items"]] == ["odoo"]
        # P3 list fields: stored Odoo product name, minimum cost and the model's data origin.
        item = library.json()["items"][0]
        assert item["product_label"] == "T6 Comparison Product"
        assert item["minimum_cost"] == base["snapshot"]["result"]["minimum_cost_plan"]["total_cost"]
        assert item["data_origin"] == "generated"
        assert len(calls) == before and len(uow.rows) == 2


def create_history_case(client):
    preview = client.get(BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers())
    assert preview.status_code == 200, preview.text
    payload = {"purchase_group_id": 501, "terms": preview.json()["terms"]}
    response = client.post(BASE + "/from-odoo-history", json=payload, headers=headers())
    assert response.status_code == 201, response.text
    return response.json()


def test_supplier_overview_reads_only_the_stored_case(configured, monkeypatch):
    calls, _ = configured
    with TestClient(app) as client:
        base = create_history_case(client)
        before = len(calls)
        for name in ("resolve_odoo_history_input", "infer_odoo_history_features"):
            monkeypatch.setattr(f"backend.app.routes.planning_cases.{name}", forbidden)
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        url = BASE + f"/{base['case_id']}/suppliers"
        hu = client.get(url, headers=headers())
        en = client.get(url + "?language=en", headers=headers())
        assert hu.status_code == en.status_code == 200, hu.text
        hu, en = hu.json(), en.json()
        assert hu["language"] == "hu" and hu["case_id"] == base["case_id"]
        labels = dict(base["snapshot"]["facts"]["labels"])
        assert hu["product_name"] == labels[hu["product_id"]] == "T6 Comparison Product"
        assert all(r["supplier_name"].startswith("Supplier ") for r in hu["suppliers"])
        assert all(r["offer_reference"].startswith("T6-RFQ-") for r in hu["suppliers"])
        request = base["snapshot"]["request"]
        assert hu["product_id"] == request["requirement"]["product_id"]
        assert [r["supplier_id"] for r in hu["suppliers"]] == [
            s["supplier_id"] for s in request["suppliers"]
        ]
        minimum = base["snapshot"]["result"]["minimum_cost_plan"]["allocations"]
        assert {
            r["supplier_id"]: r["allocation"]["minimum_cost_quantity"] for r in hu["suppliers"]
        } == {a["supplier_id"]: a["quantity"] for a in minimum}
        for row_hu, row_en, stored in zip(
            hu["suppliers"], en["suppliers"], base["snapshot"]["assessments"], strict=True
        ):
            assert row_hu["product_id"] == request["requirement"]["product_id"]
            assert [m["feature"] for m in row_hu["history"]["metrics"]] == list(HISTORY_FEATURES)
            assert [m["value"] for m in row_hu["history"]["metrics"]] == stored["snapshot"][
                "values"
            ]
            assert row_hu["assessment"]["score"] == stored["score"]
            assert len(row_hu["assessment"]["path"]) == len(stored["path"])
            assert row_hu["assessment"]["class_label"] in {"rendben", "problémás"}
            assert row_en["assessment"]["class_label"] in {"regular", "problematic"}
            assert "Hasonló múltbeli esetek" in row_hu["assessment"]["summary"]
            assert "Similar past cases" in row_en["assessment"]["summary"]
            for step in row_hu["assessment"]["path"]:
                assert step["text"].endswith(".") and (
                    "legfeljebb" in step["text"] or "felett" in step["text"]
                )
        assert client.get(url + "?language=de", headers=headers()).status_code == 422
        missing = client.get(BASE + f"/{uuid4()}/suppliers", headers=headers())
        assert missing.status_code == 404
        assert len(calls) == before


def test_plan_and_audit_pdfs_name_odoo_suppliers_and_state_generated_history(configured):
    from io import BytesIO

    from pypdf import PdfReader

    with TestClient(app) as client:
        base = create_history_case(client)
        approved = client.post(
            BASE + f"/{base['case_id']}/final-decision",
            headers=headers(),
            json={
                "snapshot_hash": base["snapshot_hash"],
                "outcome": "approve",
                "plan_index": 0,
                "actor_reference": "Sáfár Erik",
                "demonstration_acknowledged": True,
            },
        )
        content_hash = approved.json()["final_decision"]["approved_content_hash"]
        url = BASE + f"/{base['case_id']}/approved-pdf/{content_hash}"
        pages, audits = {}, {}
        for language in ("hu", "en"):
            pdf = client.get(url, params={"language": language}, headers=headers())
            pages[language] = [
                " ".join(p.extract_text().split()) for p in PdfReader(BytesIO(pdf.content)).pages
            ]
            audit = client.get(
                url, params={"language": language, "kind": "audit"}, headers=headers()
            )
            assert audit.headers["x-document-kind"] == "audit"
            assert audit.headers["x-approved-content-hash"] == content_hash
            audits[language] = " ".join(
                " ".join(p.extract_text().split()) for p in PdfReader(BytesIO(audit.content)).pages
            )
    minimum = base["snapshot"]["result"]["minimum_cost_plan"]["allocations"]
    allocated = [a for a in minimum if a["quantity"] > 0]
    labels = dict(base["snapshot"]["facts"]["labels"])
    proposals = [p for p in pages["hu"] if "Rendelési tétel" in p]
    assert len(proposals) == len(allocated)
    for page, allocation in zip(proposals, allocated, strict=True):
        assert labels[allocation["supplier_id"]] in page and "T6 Comparison Product" in page
        assert "T6-RFQ-" in page and "USD" in page
    assert "generált (szimulált) Odoo beszerzési" in pages["hu"][0]
    assert "generated (simulated) Odoo purchase history" in pages["en"][0]
    # The plan names the Odoo product without its reference; the audit document keeps it.
    for language in ("hu", "en"):
        plan = " ".join(pages[language])
        assert len(pages[language]) <= len(allocated) + 2
        # Display names only on the plan; Odoo references stay in the audit document.
        for reference in ("odoo:product.product:", "odoo:res.partner:", "odoo:purchase.order"):
            assert reference not in plan
            assert reference in audits[language]
    assert "Tervezési feltételezések" in proposals[0]
    assert "nem beszállítói vállalások" in proposals[0]
    assert "Planning assumptions" in pages["en"][1] and "not supplier commitments" in pages["en"][1]
    last = pages["hu"][-1]
    assert "Ellenőrzési azonosítók" in last, last
    assert content_hash in "".join(last.split())
    assert "Audit nézetéből" in pages["hu"][-1] and "Döntési útvonal" not in " ".join(pages["hu"])
    appendix = audits["hu"]
    assert DATABASE in appendix and "odoo:purchase.order.group:501" in appendix
    assert "Határidőre teljesített szállítások aránya" in appendix
    # Fixed English record sentences: Hungarian first, the stored original quoted verbatim.
    recorded = approved.json()["final_decision"]["approved_content"]["human_decision"]
    for original in (recorded["actor_attribution"], recorded["demonstration"]):
        assert f"(eredeti, rögzített szöveg: „{original}”)" in appendix
    assert "nem hitelesített beszerzői személyazonosság" in appendix
    assert "Ellenőrzött bemutató; szintetikus ML-bizonyíték" in appendix
    assert "optimális (optimal)" in appendix
    unit = labels.get(base["snapshot"]["request"]["requirement"]["quantity_unit"])
    assert unit == "Units" and " Units" not in " ".join(pages["hu"]) and " db" in proposals[0]
    english = audits["en"]
    assert f"{recorded['actor_attribution']} (original recorded text)" in english
    assert "személyazonosság" not in english and "optimális" not in english


@pytest.mark.parametrize(
    "mutation", ["extra", "bool_quantity", "float_price", "changed_price", "conflict"]
)
def test_invalid_terms_and_key_conflict_save_nothing_new(configured, monkeypatch, mutation):
    _, uow = configured
    with TestClient(app) as client:
        preview = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        ).json()
        payload = {"purchase_group_id": 501, "terms": preview["terms"]}
        key, expected, saved = str(uuid4()), 422, 0
        if mutation == "extra":
            payload["terms"]["model_directory"] = "untrusted"
        if mutation == "bool_quantity":
            payload["terms"]["requirement"]["approved_quantity"] = True
        if mutation == "float_price":
            payload["terms"]["suppliers"][0]["unit_price"] = 10.0
        if mutation == "changed_price":  # caller expectation differs from the Odoo quotation
            payload["terms"]["suppliers"][0]["unit_price"] = "1"
        if mutation == "conflict":
            first = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
            assert first.status_code == 201, first.text
            payload["terms"]["requirement"]["approved_quantity"] += 1
            expected, saved = 409, 1
        monkeypatch.setattr("backend.app.routes.planning_cases.planning_solver_factory", forbidden)
        response = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
    assert response.status_code == expected, response.text
    assert len(uow.rows) == saved


def test_insufficient_supplier_history_saves_nothing(configured, history, monkeypatch):
    _, uow = configured
    lines = tuple(x for x in history["lines"] if x.supplier_id != "odoo:res.partner:306")
    monkeypatch.setitem(history, "lines", lines)
    with TestClient(app) as client:
        response = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "odoo_history_insufficient"
    assert not uow.rows


def test_missing_model_blocks_creation_without_a_saved_case(configured, monkeypatch, tmp_path):
    _, uow = configured
    monkeypatch.setattr(settings, "supplier_history_model_directory", tmp_path)
    with TestClient(app) as client:
        data = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        ).json()
        assert data["model_readiness"] == "model_unavailable"
        response = client.post(
            BASE + "/from-odoo-history",
            json={"purchase_group_id": 501, "terms": data["terms"]},
            headers=headers(),
        )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "odoo_history_model_incompatible"
    assert not uow.rows


def test_model_origin_is_explicit_and_validated(history):
    observed = train(history["split"], database=DATABASE, data_origin="observed")
    assert observed.metadata["data_origin"] == "observed"
    check_manifest_metadata(observed.metadata)
    with pytest.raises(ValueError, match="origin"):
        train(history["split"], database=DATABASE, data_origin="synthetic")
    with pytest.raises(ValueError, match="metadata"):
        check_manifest_metadata(history["model"].metadata | {"data_origin": "synthetic"})


def test_model_of_another_data_origin_cannot_assess_the_database(configured, monkeypatch):
    _, uow = configured
    monkeypatch.setattr(settings, "odoo_history_data_origin", "observed")
    with TestClient(app) as client:
        data = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        ).json()
        assert data["data_origin"] == "observed"
        assert data["model_readiness"] == "model_unavailable"
        response = client.post(
            BASE + "/from-odoo-history",
            json={"purchase_group_id": 501, "terms": data["terms"]},
            headers=headers(),
        )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "odoo_history_model_incompatible"
    assert not uow.rows


def _without_origin(encoded):
    """A capture as stored before the declared origin was recorded."""
    payload = json.loads(encoded)
    old_hash = payload["capture_hash"]
    del payload["evidence"]["data_origin"]
    payload["capture_hash"] = digest(payload["evidence"])
    for feature in payload["features"]:
        feature["source_reference"] = feature["source_reference"].replace(
            old_hash, payload["capture_hash"]
        )
    del payload["payload_hash"]
    payload["payload_hash"] = digest(payload)
    return canonical(payload)


def test_stored_case_requires_model_origin_equal_to_history_origin(configured):
    _, uow = configured
    with TestClient(app) as client:
        data = client.get(
            BASE + "/odoo-history/preview?purchase_group_id=501", headers=headers()
        ).json()
        response = client.post(
            BASE + "/from-odoo-history",
            json={"purchase_group_id": 501, "terms": data["terms"]},
            headers=headers(),
        )
    assert response.status_code == 201, response.text
    (case,) = uow.rows.values()
    stored = json.loads(case.snapshot)
    assert capture_origin(stored["facts"]["history"]) == "generated"
    validate_snapshot(case)
    mismatched = json.loads(case.snapshot)
    mismatched["model_manifest"]["metadata"]["data_origin"] = "observed"
    with pytest.raises(RepositoryError) as error:
        validate_snapshot(replace(case, snapshot=snapshot_json(mismatched)))
    assert "compatibility mismatch" in str(error.value.__cause__)
    legacy = json.loads(case.snapshot)
    legacy["facts"]["history"] = _without_origin(legacy["facts"]["history"])
    assert capture_origin(legacy["facts"]["history"]) == "generated"
    assert len(capture_features(legacy["facts"]["history"])) == 3


# --- Seeding tool guards -------------------------------------------------------------


def test_seed_plan_is_deterministic_tagged_and_in_the_past():
    clock = datetime(2026, 10, 17, tzinfo=UTC)
    plan, again = build_plan(clock), build_plan(clock)
    assert plan_summary(plan) == plan_summary(again) and len(plan.suppliers) == 40
    assert all(o.code.startswith("PDSS-GEN-P1:") for o in plan.orders)
    assert all(s.name.startswith("[GEN] ") for s in plan.suppliers)
    assert all(r.at < clock for o in plan.orders for r in o.receipts)
    assert all(sum(r.quantity for r in o.receipts) <= o.quantity for o in plan.orders)


def test_seed_writer_refuses_any_other_database_or_unmarked_target():
    with pytest.raises(SeedRefused, match="only 'pdss_history_gen'"):
        OdooWriter("http://odoo.test", "procurement_poc", "key")
    with pytest.raises(SeedRefused, match="not set"):
        OdooWriter("http://odoo.test", ALLOWED_DATABASE, "")

    def respond(request):
        if request.url.path.endswith("get_param"):
            return httpx.Response(200, json=False)
        raise AssertionError("No write may happen before the target is verified")

    writer = OdooWriter(
        "http://odoo.test", ALLOWED_DATABASE, "key", transport=httpx.MockTransport(respond)
    )
    with pytest.raises(SeedRefused, match="pdss.seed_target"):
        writer.verify_target()
