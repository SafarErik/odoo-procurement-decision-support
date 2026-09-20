"""Fast tests for the T7-S bounded projection policy and addon boundary."""

import importlib.util
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = PROJECT_ROOT / "infra" / "odoo" / "addons" / "t7s_inventory_history_projection"
POLICY_PATH = ADDON_ROOT / "projection_policy.py"
MODEL_PATH = ADDON_ROOT / "models" / "inventory_history_projection.py"


def _load_policy():
    spec = importlib.util.spec_from_file_location("t7s_projection_policy_for_tests", POLICY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


policy = _load_policy()


def _request():
    return policy.validate_request(
        company_id=1,
        date_from="2026-01-01 00:00:00",
        date_to="2026-01-02 00:00:00",
        purchase_order_line_ids=[10],
        limit=10,
        now=datetime(2026, 1, 3),
    )


def _evidence():
    return {
        "lines": [
            {
                "id": 10,
                "purchase_order_id": 20,
                "product_id": 30,
                "product_uom_id": 1,
                "ordered_quantity": "100.0",
                "expected_arrival_at": "2026-01-01 12:00:00",
                "company_id": 1,
                "qty_received_method": "stock_moves",
            }
        ],
        "orders": [
            {
                "id": 20,
                "supplier_id": 40,
                "company_id": 1,
                "state": "purchase",
            }
        ],
        "partners": [{"id": 40, "commercial_partner_id": 41}],
        "moves": [
            {
                "id": 50,
                "purchase_order_line_id": 10,
                "stock_picking_id": 60,
                "product_id": 30,
                "product_uom_id": 1,
                "completed_quantity": "100.0",
                "state": "done",
                "move_processed_at": "2026-01-01 10:00:00",
                "company_id": 1,
                "source_location_usage": "supplier",
                "destination_location_usage": "internal",
                "return_of_move_id": None,
            }
        ],
        "pickings": [
            {
                "id": 60,
                "state": "done",
                "transfer_processed_at": "2026-01-01 10:00:00",
                "picking_type_code": "incoming",
                "backorder_of_picking_id": None,
                "return_of_picking_id": None,
                "company_id": 1,
            }
        ],
    }


def test_projection_emits_only_the_fixed_sanitized_schema() -> None:
    records = policy.build_projection_records(_request(), **_evidence())

    assert len(records) == 1
    assert tuple(records[0]) == policy.RECORD_FIELDS
    assert records[0] == {
        "company_id": 1,
        "commercial_partner_id": 41,
        "purchase_order_id": 20,
        "purchase_order_line_id": 10,
        "product_id": 30,
        "product_uom_id": 1,
        "expected_arrival_at": "2026-01-01 12:00:00",
        "stock_move_id": 50,
        "stock_picking_id": 60,
        "move_processed_at": "2026-01-01 10:00:00",
        "ordered_quantity": "100.0",
        "completed_quantity": "100.0",
        "state": "done",
        "source_location_usage": "supplier",
        "destination_location_usage": "internal",
        "backorder_of_picking_id": None,
        "return_of_move_id": None,
        "return_of_picking_id": None,
    }
    assert "name" not in records[0]
    assert "display_name" not in records[0]
    assert "api_key" not in records[0]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"company_id": True}, "company_id must be a positive integer"),
        ({"date_from": None}, "date_from must use"),
        ({"date_to": "2026-01-04 00:00:00"}, "date_to must not be in the future"),
        ({"date_to": "2025-12-31 00:00:00"}, "date_from must be earlier"),
        (
            {"date_from": "2024-01-01 00:00:00"},
            "history window must not exceed 366 days",
        ),
        ({"purchase_order_line_ids": []}, "must be a non-empty JSON list"),
        ({"purchase_order_line_ids": [10, 10]}, "must not contain duplicates"),
        ({"limit": policy.MAX_RESULTS + 1}, "limit must not exceed"),
    ],
)
def test_projection_request_rejects_arbitrary_or_unbounded_input(overrides, message) -> None:
    values = {
        "company_id": 1,
        "date_from": "2026-01-01 00:00:00",
        "date_to": "2026-01-02 00:00:00",
        "purchase_order_line_ids": [10],
        "limit": 10,
        "now": datetime(2026, 1, 3),
    }
    values.update(overrides)

    with pytest.raises(policy.ProjectionPolicyError, match=message):
        policy.validate_request(**values)


def test_projection_rejects_cross_company_evidence() -> None:
    evidence = _evidence()
    evidence["moves"][0]["company_id"] = 2

    with pytest.raises(policy.ProjectionPolicyError, match="company boundary"):
        policy.build_projection_records(_request(), **evidence)


def test_projection_rejects_unsupported_move_state_instead_of_dropping_it() -> None:
    evidence = _evidence()
    evidence["moves"][0]["state"] = "assigned"

    with pytest.raises(policy.ProjectionPolicyError, match="move state is unsupported"):
        policy.build_projection_records(_request(), **evidence)


def test_projection_rejects_ambiguous_direction() -> None:
    evidence = _evidence()
    evidence["moves"][0]["destination_location_usage"] = "customer"

    with pytest.raises(policy.ProjectionPolicyError, match="direction"):
        policy.build_projection_records(_request(), **evidence)


def test_projection_rejects_return_whose_origin_is_outside_the_bounded_result() -> None:
    evidence = _evidence()
    evidence["moves"][0].update(
        {
            "source_location_usage": "internal",
            "destination_location_usage": "supplier",
            "return_of_move_id": 999,
        }
    )
    evidence["pickings"][0]["picking_type_code"] = "outgoing"
    evidence["pickings"][0]["return_of_picking_id"] = 998

    with pytest.raises(policy.ProjectionPolicyError, match="return relationship leaves"):
        policy.build_projection_records(_request(), **evidence)


def test_projection_accepts_complete_supplier_return_relationship() -> None:
    evidence = _evidence()
    return_move = deepcopy(evidence["moves"][0])
    return_move.update(
        {
            "id": 51,
            "stock_picking_id": 61,
            "completed_quantity": "20.0",
            "move_processed_at": "2026-01-01 11:00:00",
            "source_location_usage": "internal",
            "destination_location_usage": "supplier",
            "return_of_move_id": 50,
        }
    )
    return_picking = deepcopy(evidence["pickings"][0])
    return_picking.update(
        {
            "id": 61,
            "transfer_processed_at": "2026-01-01 11:00:00",
            "picking_type_code": "outgoing",
            "return_of_picking_id": 60,
        }
    )
    evidence["moves"].append(return_move)
    evidence["pickings"].append(return_picking)

    records = policy.build_projection_records(_request(), **evidence)

    assert len(records) == 2
    assert records[1]["source_location_usage"] == "internal"
    assert records[1]["destination_location_usage"] == "supplier"
    assert records[1]["return_of_move_id"] == 50
    assert records[1]["return_of_picking_id"] == 60


def test_projection_rejects_outgoing_picking_without_supplier_return_direction() -> None:
    evidence = _evidence()
    evidence["pickings"][0]["picking_type_code"] = "outgoing"

    with pytest.raises(policy.ProjectionPolicyError, match="picking type"):
        policy.build_projection_records(_request(), **evidence)


def test_projection_accepts_only_a_complete_backorder_relationship() -> None:
    evidence = _evidence()
    evidence["moves"][0]["completed_quantity"] = "40.0"
    second_move = deepcopy(evidence["moves"][0])
    second_move.update(
        {
            "id": 51,
            "stock_picking_id": 61,
            "completed_quantity": "60.0",
            "move_processed_at": "2026-01-01 11:00:00",
        }
    )
    second_picking = deepcopy(evidence["pickings"][0])
    second_picking.update(
        {
            "id": 61,
            "transfer_processed_at": "2026-01-01 11:00:00",
            "backorder_of_picking_id": 60,
        }
    )
    evidence["moves"].append(second_move)
    evidence["pickings"].append(second_picking)

    records = policy.build_projection_records(_request(), **evidence)

    assert [record["completed_quantity"] for record in records] == ["40.0", "60.0"]
    assert records[1]["backorder_of_picking_id"] == 60


def test_projection_rejects_backorder_relationship_outside_bounded_result() -> None:
    evidence = _evidence()
    evidence["pickings"][0]["backorder_of_picking_id"] = 999

    with pytest.raises(policy.ProjectionPolicyError, match="backorder relationship leaves"):
        policy.build_projection_records(_request(), **evidence)


def test_addon_has_no_sql_or_generic_acl_surface() -> None:
    model_source = MODEL_PATH.read_text(encoding="utf-8")

    assert "env.cr" not in model_source
    assert ".execute(" not in model_source
    assert "_auto = False" not in model_source
    assert not (ADDON_ROOT / "security" / "ir.model.access.csv").exists()
    assert "models.AbstractModel" in model_source
    assert 'self.env["stock.move"]' in model_source
    assert 'self.env["stock.picking"]' in model_source
    assert model_source.count(".sudo()") == 5
    assert model_source.count(".search_fetch(") == 5


def test_addon_group_implies_no_broad_role() -> None:
    security_source = (ADDON_ROOT / "security" / "t7s_security.xml").read_text(encoding="utf-8")

    assert "implied_ids" not in security_source
    assert "group_stock_user" not in security_source
    assert "group_stock_manager" not in security_source
    assert "group_purchase_user" not in security_source
    assert "group_purchase_manager" not in security_source
