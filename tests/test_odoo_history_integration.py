"""Bounded acquisition, one offline compatibility gate, and immutable V2 lifecycle."""

import asyncio
import json
import shutil
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from application.planning_history import capture_features
from application.rfqs import ProcurementDataResponseError
from backend.app.config import settings
from backend.app.main import app
from frontend.planning_client import _map_case, submit_planning_request
from odoo_adapter.planning_history_reader import OdooPlanningHistoryReader, local_profile
from supplier_evaluation.artifacts import load_model, save_model
from supplier_evaluation.contracts import QuantityValidity, canonical, digest
from supplier_evaluation.dataset import BOUNDARY, EXTRACTED_AT, generate_dataset, prepare_dataset
from supplier_evaluation.model import train
from supplier_evaluation.odoo_compatibility import evaluate_candidate
from supplier_evaluation.qualified_odoo import load_qualified_model, qualify
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tests.test_odoo_comparison_case_adapter import _payloads

BASE = "/api/v2/procurement/planning-cases"


def forbidden(*args, **kwargs):
    raise AssertionError("Stored operation acquired data, trained, loaded a model or solved")


@pytest.fixture(scope="module")
def qualified(tmp_path_factory):
    root = tmp_path_factory.mktemp("qualified-history")
    rows = generate_dataset(
        domain=("odoo:res.company:1", "odoo:product.product:54", "odoo:uom.uom:1")
    )
    save_model(
        train(prepare_dataset(rows, boundary=BOUNDARY, extracted_at=EXTRACTED_AT)),
        root / "original",
    )
    report = evaluate_candidate(root / "original")
    assert report["decision"] == "GO"
    (root / "report.json").write_text(canonical(report), encoding="utf-8")
    qualify(root / "original", root / "report.json", root / "qualified")
    return root


def source_fixture(profile, calls, mutate=None):
    now = datetime.now(UTC)
    for r in profile["records"]:
        day = (
            now + timedelta(days=1)
            if r["code"] in {"A01", "A02", "A03", "B01", "B02", "C01"}
            else now - timedelta(days=1)
        )
        r["deadline"] = day.replace(hour=0, minute=0, second=0, microsecond=0).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    history_orders, history_lines = [], []
    for r in profile["records"]:
        history_orders.append(
            {
                "id": r["order"],
                "origin": "V2-SYNTH-HIST-v1-" + r["code"],
                "state": "purchase",
                "company_id": [1, "Company"],
                "partner_id": [r["supplier"], "Supplier"],
                "currency_id": [1, "USD"],
                "purchase_group_id": False,
                "order_line": [r["line"]],
            }
        )
        history_lines.append(
            {
                "id": r["line"],
                "order_id": [r["order"], "PO"],
                "product_id": [54, "Product"],
                "company_id": [1, "Company"],
                "product_uom_id": [1, "Units"],
                "product_qty": 100,
                "qty_received": 100,
                "qty_received_method": "stock_moves",
                "price_unit": r["price"],
                "discount": 0,
                "tax_ids": [],
                "date_planned": r["deadline"],
            }
        )
    quotes = _payloads()
    for i, (order, line, partner) in enumerate(
        zip(quotes["orders"], quotes["lines"], quotes["partners"], strict=True)
    ):
        order.update(
            id=16 + i,
            partner_id=[51 + i, "Supplier"],
            currency_id=[1, "USD"],
            purchase_group_id=[2, "Group"],
            order_line=[28 + i],
        )
        line.update(
            id=28 + i, order_id=[16 + i, "RFQ"], product_id=[54, "Product"], currency_id=[1, "USD"]
        )
        partner.update(id=51 + i, commercial_partner_id=[51 + i, "Supplier"])

    def respond(request):
        data = json.loads(request.content)
        path = request.url.path
        calls.append((path, data, request.headers["X-Odoo-Database"]))
        assert request.headers["X-Odoo-Database"] == profile["database"]
        if path.endswith("read_bounded_history"):
            assert request.headers["Authorization"] == "Bearer history-only"
            assert data["limit"] == 10 and len(data["purchase_order_line_ids"]) == 3
            records = []
            for r in profile["records"]:
                if r["line"] not in data["purchase_order_line_ids"]:
                    continue
                for j, (move, picking, qty, previous) in enumerate(r["events"]):
                    records.append(
                        {
                            "company_id": 1,
                            "commercial_partner_id": r["supplier"],
                            "purchase_order_id": r["order"],
                            "purchase_order_line_id": r["line"],
                            "product_id": 54,
                            "product_uom_id": 1,
                            "expected_arrival_at": r["deadline"],
                            "stock_move_id": move,
                            "stock_picking_id": picking,
                            "move_processed_at": (
                                now - timedelta(hours=1) + timedelta(seconds=j)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "ordered_quantity": "100.0",
                            "completed_quantity": str(float(qty)),
                            "state": "done",
                            "source_location_usage": "supplier",
                            "destination_location_usage": "internal",
                            "backorder_of_picking_id": previous,
                            "return_of_move_id": None,
                            "return_of_picking_id": None,
                        }
                    )
            if mutate:
                mutate(records)
            return httpx.Response(
                200,
                json={
                    "schema_version": "t7s.inventory_history.v1",
                    "company_id": 1,
                    "date_from": data["date_from"],
                    "date_to": data["date_to"],
                    "result_count": len(records),
                    "records": records,
                },
            )
        assert request.headers["Authorization"] == "Bearer rfq-only"
        if path.endswith("purchase.order/search_count"):
            return httpx.Response(200, json=3)
        if path.endswith("purchase.order/search_read"):
            return httpx.Response(
                200,
                json=quotes["orders"]
                if data["domain"][0][0] == "purchase_group_id"
                else history_orders,
            )
        if path.endswith("purchase.order.line/search_read"):
            return httpx.Response(
                200, json=quotes["lines"] if data["domain"][0][2][0] == 28 else history_lines
            )
        if path.endswith("res.partner/search_read"):
            return httpx.Response(200, json=quotes["partners"])
        if path.endswith("res.currency/search_read"):
            return httpx.Response(200, json=[{"id": 1, "name": "USD"}])
        raise AssertionError(path)

    return respond


@pytest.fixture
def configured(qualified, monkeypatch):
    profile, calls = local_profile(), []
    respond = source_fixture(profile, calls)
    monkeypatch.setattr("odoo_adapter.planning_history_reader.local_profile", lambda: profile)
    monkeypatch.setattr("backend.app.dependencies.local_profile", lambda: profile)
    reader = OdooPlanningHistoryReader(
        base_url="http://odoo.test",
        database=profile["database"],
        api_key="rfq-only",
        history_key="history-only",
        transport=httpx.MockTransport(respond),
    )
    monkeypatch.setattr(
        "backend.app.dependencies.capture_local_history",
        lambda revision: asyncio.run(reader.capture(revision)),
    )
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(settings, "odoo_history_model_directory", qualified / "qualified")
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("history-test-token"))
    return profile, calls, uow, reader


def headers(key=None):
    return {"Authorization": "Bearer history-test-token", "Idempotency-Key": key or str(uuid4())}


def test_live_style_acquisition_saved_lifecycle_and_offline_replay(configured, monkeypatch):
    profile, calls, uow, _ = configured
    with TestClient(app) as client:
        preview = client.get(BASE + "/odoo-history/local-v1", headers=headers())
        assert preview.status_code == 200, preview.text
        data = preview.json()
        assert [p["value"] for p in data["history"]] == ["100.00", "66.67", "33.33"]
        payload = {k: data[k] for k in ("profile_id", "profile_revision", "terms")}
        payload["catalog_context"] = {"workspace": "controlled"}
        key = str(uuid4())
        response = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
        assert response.status_code == 201, response.text
        base = response.json()
        mapped = _map_case(base, base["case_id"])
        assert len(mapped.assessments) == 3
        assert base["snapshot"]["facts"]["source_type"] == "odoo_projection"
        assert (
            base["snapshot"]["model_manifest"]["metadata"]["training_source_type"]
            == "t14_synthetic"
        )
        assert all(not s["receipts"] for s in base["snapshot"]["facts"]["suppliers"])
        provenance = {p["canonical_path"]: p for p in base["snapshot"]["provenance"]["entries"]}
        for assessment in base["snapshot"]["assessments"]:
            feature = assessment["snapshot"]
            supplier = feature["context"]["supplier_id"]
            assert (
                provenance[f"facts.suppliers[{supplier}].receipts"]["observed_at"]
                == (feature["evidence_available_at"])
            )
        oldcalls = len(calls)
        monkeypatch.setattr(
            "backend.app.routes.planning_cases.resolve_odoo_history_input", forbidden
        )
        monkeypatch.setattr(
            "backend.app.routes.planning_cases.infer_odoo_history_features", forbidden
        )
        replay = client.post(BASE + "/from-odoo-history", json=payload, headers=headers(key))
        assert replay.status_code == 200 and replay.json()["snapshot_hash"] == base["snapshot_hash"]
        assert len(calls) == oldcalls and len(uow.rows) == 1
        scenario = {
            "kind": "supplier_outage",
            "source": payload["terms"]["policy_source"],
            "suppliers": [{"supplier_id": "odoo:res.partner:53", "available": False}],
        }
        child = client.post(
            BASE + f"/{base['case_id']}/scenarios", json=scenario, headers=headers()
        )
        assert child.status_code == 201, child.text
        assert child.json()["snapshot"]["snapshot_version"] == base["snapshot"]["snapshot_version"]
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
        saved = approved.json()
        _map_case(saved, base["case_id"])
        content_hash = saved["final_decision"]["approved_content_hash"]
        pdf = client.get(
            BASE + f"/{base['case_id']}/approved-pdf/{content_hash}", headers=headers()
        )
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
        assert client.get(BASE + f"/{base['case_id']}", headers=headers()).status_code == 200
        assert len(calls) == oldcalls


@pytest.mark.parametrize(
    "field,value", [("database", "procurement_poc"), ("profile_revision", "0" * 64)]
)
def test_wrong_database_or_profile_fails_before_acquisition(configured, field, value):
    profile, calls, _, reader = configured
    revision = digest(profile)
    if field == "database":
        reader.database = value
    else:
        revision = value
    with pytest.raises(ValueError, match="database or profile"):
        asyncio.run(reader.capture(revision))
    assert not calls


def test_no_partial_saved_case_on_missing_model_and_no_browser_history(configured, monkeypatch):
    _, _, uow, _ = configured
    with TestClient(app) as client:
        data = client.get(BASE + "/odoo-history/local-v1", headers=headers()).json()
        payload = {k: data[k] for k in ("profile_id", "profile_revision", "terms")}
        payload["terms"]["suppliers"][0]["receipts"] = []
        assert (
            client.post(BASE + "/from-odoo-history", json=payload, headers=headers()).status_code
            == 422
        )
        del payload["terms"]["suppliers"][0]["receipts"]
        monkeypatch.setattr(settings, "odoo_history_model_directory", None)
        assert (
            client.post(BASE + "/from-odoo-history", json=payload, headers=headers()).status_code
            == 503
        )
        assert not uow.rows


def test_capture_tampering_and_legacy_model_source_guard(configured, qualified):
    profile, _, _, reader = configured
    capture = asyncio.run(reader.capture(digest(profile)))[3]
    features = capture_features(capture)
    original = load_model(qualified / "original", trusted_local=True)
    with pytest.raises(ValueError, match="context"):
        original.infer(features[0], QuantityValidity(1, 1000, "controlled-proxy-v1"))
    model, _ = load_qualified_model(qualified / "qualified")
    for invalid in (
        replace(features[0], source_reference="fake"),
        replace(features[0], values=(100.0, 31.0)),
    ):
        with pytest.raises(ValueError, match="compatibility"):
            model.infer(invalid, QuantityValidity(1, 1000, "controlled-proxy-v1"))
    changed = json.loads(capture)
    changed["evidence"]["origin"] = "observed"
    with pytest.raises(ValueError, match="provenance"):
        capture_features(canonical(changed))


def test_failed_qualification_never_publishes(qualified, tmp_path):
    report = json.loads((qualified / "report.json").read_text())
    report["decision"] = "NO-GO"
    report["report_hash"] = digest({k: v for k, v in report.items() if k != "report_hash"})
    path = tmp_path / "report.json"
    path.write_text(canonical(report))
    with pytest.raises(ValueError, match="GO"):
        qualify(qualified / "original", path, tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("company_id", 2),
        ("commercial_partner_id", 55),
        ("product_id", 57),
        ("product_uom_id", 2),
        ("purchase_order_line_id", 999),
        ("expected_arrival_at", "2020-01-01 00:00:00"),
        ("move_processed_at", "2020-01-01 00:00:00"),
        ("completed_quantity", "99"),
        ("backorder_of_picking_id", 999),
        ("return_of_move_id", 99),
        ("state", "assigned"),
    ],
)
def test_raw_receipt_context_fails_closed(configured, field, value):
    profile, calls, _, _ = configured
    respond = source_fixture(profile, calls, lambda rows: rows[0].update({field: value}))
    reader = OdooPlanningHistoryReader(
        base_url="http://odoo.test",
        database=profile["database"],
        api_key="rfq-only",
        history_key="history-only",
        transport=httpx.MockTransport(respond),
    )
    with pytest.raises((ValueError, ProcurementDataResponseError)):
        asyncio.run(reader.capture(digest(profile)))


def test_raw_backorder_validation_precedes_kpi_aggregation(configured, monkeypatch):
    profile, calls, _, _ = configured
    respond = source_fixture(
        profile, calls, lambda rows: rows[0].update(backorder_of_picking_id=999)
    )
    reader = OdooPlanningHistoryReader(
        base_url="http://odoo.test",
        database=profile["database"],
        api_key="rfq-only",
        history_key="history-only",
        transport=httpx.MockTransport(respond),
    )
    monkeypatch.setattr(
        "application.planning_history.calculate_delivery_schedule_adherence", forbidden
    )
    with pytest.raises(ValueError, match="backorder"):
        asyncio.run(reader.capture(digest(profile)))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "early_cutoff", "payload"])
def test_support_temporal_and_integrity_gates(configured, mutation):
    profile, _, _, reader = configured
    captured = json.loads(asyncio.run(reader.capture(digest(profile)))[3])
    if mutation == "payload":
        captured["features"][0]["values"][0] = 0
    else:
        evidence = captured["evidence"]
        if mutation == "missing":
            evidence["snapshots"][0]["observations"].pop()
        elif mutation == "duplicate":
            evidence["snapshots"][0]["observations"].append(
                evidence["snapshots"][0]["observations"][0]
            )
        else:
            evidence["cutoff"] = "2020-01-01T00:00:00+00:00"
        captured["capture_hash"] = digest(evidence)
        captured["payload_hash"] = digest(
            {k: v for k, v in captured.items() if k != "payload_hash"}
        )
    with pytest.raises(ValueError):
        capture_features(canonical(captured))


def test_qualified_package_corruption_rejected_before_loading(qualified, tmp_path, monkeypatch):
    package = tmp_path / "package"
    shutil.copytree(qualified / "qualified", package)
    manifest = json.loads((package / "manifest.json").read_text())
    manifest["metadata"]["training_source_type"] = "observed"
    (package / "manifest.json").write_text(canonical(manifest))
    monkeypatch.setattr("supplier_evaluation.qualified_odoo.load_model", forbidden)
    with pytest.raises(ValueError, match="identity"):
        load_qualified_model(package)


@pytest.mark.parametrize(
    "code,status,expected",
    [
        ("history_profile_changed", 409, "profile changed"),
        ("odoo_history_unavailable", 503, "No case was saved"),
        ("odoo_history_model_incompatible", 503, "incompatible"),
    ],
)
def test_history_errors_are_definitive_and_actionable(code, status, expected):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, json={"detail": {"code": code}})
    )
    display, message, uncertain = asyncio.run(
        submit_planning_request(
            "http://api.test" + BASE + "/from-odoo-history",
            {},
            str(uuid4()),
            "token",
            transport=transport,
        )
    )
    assert display is None and not uncertain and expected in message
