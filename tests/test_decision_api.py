"""Contract tests for the versioned procurement decision endpoint."""

from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

ENDPOINT = "/api/v1/procurement/decisions/evaluate"

REFERENCE_REQUEST: dict[str, Any] = {
    "requirement": {
        "requirement_id": "REQ-100",
        "requested_quantity": "100",
    },
    "offers": [
        {
            "offer_id": "Offer A",
            "supplier_id": "Supplier A",
            "unit_price": "10",
            "lead_time_days": "10",
            "minimum_order_quantity": "50",
        },
        {
            "offer_id": "Offer B",
            "supplier_id": "Supplier B",
            "unit_price": "12",
            "lead_time_days": "5",
            "minimum_order_quantity": "100",
        },
        {
            "offer_id": "Offer C",
            "supplier_id": "Supplier C",
            "unit_price": "9",
            "lead_time_days": "8",
            "minimum_order_quantity": "150",
        },
    ],
    "profile": {
        "name": "cost-focused",
        "unit_price_weight": "0.7",
        "lead_time_weight": "0.3",
    },
}


def _post(payload: dict[str, Any]):
    return TestClient(app).post(ENDPOINT, json=payload)


def _reference_payload() -> dict[str, Any]:
    return deepcopy(REFERENCE_REQUEST)


def test_reference_request_returns_complete_explained_result() -> None:
    """The public contract exposes ranking, contributions, and exclusions."""

    response = _post(_reference_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["requirement"] == {
        "requirement_id": "REQ-100",
        "requested_quantity": "100",
    }
    assert payload["profile"] == {
        "name": "cost-focused",
        "unit_price_weight": "0.7",
        "lead_time_weight": "0.3",
    }
    assert payload["recommended_offer"] == {
        "offer_id": "Offer A",
        "supplier_id": "Supplier A",
    }
    assert [item["offer_id"] for item in payload["ranked_offers"]] == [
        "Offer A",
        "Offer B",
    ]
    assert [item["total_score"] for item in payload["ranked_offers"]] == ["0.7", "0.3"]

    offer_a, offer_b = payload["ranked_offers"]
    assert offer_a == {
        "rank": 1,
        "offer_id": "Offer A",
        "supplier_id": "Supplier A",
        "unit_price": "10",
        "lead_time_days": "10",
        "minimum_order_quantity": "50",
        "total_score": "0.7",
        "contributions": [
            {
                "criterion": "unit_price",
                "direction": "cost",
                "raw_value": "10",
                "normalized_value": "1",
                "weight": "0.7",
                "weighted_contribution": "0.7",
            },
            {
                "criterion": "lead_time_days",
                "direction": "cost",
                "raw_value": "10",
                "normalized_value": "0",
                "weight": "0.3",
                "weighted_contribution": "0.0",
            },
        ],
    }
    assert offer_b["contributions"] == [
        {
            "criterion": "unit_price",
            "direction": "cost",
            "raw_value": "12",
            "normalized_value": "0",
            "weight": "0.7",
            "weighted_contribution": "0.0",
        },
        {
            "criterion": "lead_time_days",
            "direction": "cost",
            "raw_value": "5",
            "normalized_value": "1",
            "weight": "0.3",
            "weighted_contribution": "0.3",
        },
    ]
    assert payload["excluded_offers"] == [
        {
            "offer_id": "Offer C",
            "supplier_id": "Supplier C",
            "failed_constraint": "minimum_order_quantity",
            "explanation": (
                "Offer Offer C was excluded because the requested quantity of 100 is lower "
                "than the supplier's minimum order quantity of 150."
            ),
            "requested_quantity": "100",
            "minimum_order_quantity": "150",
        }
    ]
    assert "Offer C" not in [item["offer_id"] for item in payload["ranked_offers"]]


@pytest.mark.parametrize(
    ("name", "unit_price_weight", "lead_time_weight", "expected_order"),
    [
        ("balanced", "0.5", "0.5", ["Offer A", "Offer B"]),
        ("urgent", "0.3", "0.7", ["Offer B", "Offer A"]),
    ],
)
def test_profile_weights_control_deterministic_ranking(
    name: str,
    unit_price_weight: str,
    lead_time_weight: str,
    expected_order: list[str],
) -> None:
    payload = _reference_payload()
    payload["profile"] = {
        "name": name,
        "unit_price_weight": unit_price_weight,
        "lead_time_weight": lead_time_weight,
    }

    response = _post(payload)

    assert response.status_code == 200
    assert [item["offer_id"] for item in response.json()["ranked_offers"]] == expected_order


def test_input_offer_order_does_not_change_response_ranking() -> None:
    payload = _reference_payload()
    payload["offers"].reverse()

    response = _post(payload)

    assert response.status_code == 200
    assert [item["offer_id"] for item in response.json()["ranked_offers"]] == [
        "Offer A",
        "Offer B",
    ]


def test_all_excluded_is_successful_without_a_recommendation() -> None:
    payload = _reference_payload()
    payload["requirement"]["requested_quantity"] = "1"

    response = _post(payload)

    assert response.status_code == 200
    assert response.json()["recommended_offer"] is None
    assert response.json()["ranked_offers"] == []
    assert [item["offer_id"] for item in response.json()["excluded_offers"]] == [
        "Offer A",
        "Offer B",
        "Offer C",
    ]


def test_empty_offers_uses_stable_domain_error() -> None:
    payload = _reference_payload()
    payload["offers"] = []

    response = _post(payload)

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "invalid_decision_input",
        "message": "At least one supplier offer is required.",
    }


def test_duplicate_offer_identifiers_use_stable_domain_error() -> None:
    payload = _reference_payload()
    payload["offers"][1]["offer_id"] = "Offer A"

    response = _post(payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_decision_input"
    assert "duplicates: Offer A" in response.json()["detail"]["message"]


@pytest.mark.parametrize(
    ("path", "invalid_value"),
    [
        (("requirement", "requested_quantity"), "0"),
        (("offers", 0, "unit_price"), "0"),
        (("offers", 0, "lead_time_days"), "-1"),
        (("offers", 0, "minimum_order_quantity"), "0"),
        (("profile", "unit_price_weight"), "-0.1"),
        (("profile", "unit_price_weight"), "0.8"),
    ],
)
def test_invalid_domain_values_use_stable_safe_error(
    path: tuple[str | int, ...], invalid_value: str
) -> None:
    payload = _reference_payload()
    target: Any = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = invalid_value

    response = _post(payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_decision_input"
    assert response.json()["detail"]["message"]
    assert "traceback" not in response.text.lower()


@pytest.mark.parametrize("malformed_value", ["not-a-decimal", "1e2", "NaN", 10])
def test_malformed_decimal_strings_use_request_validation(malformed_value: Any) -> None:
    payload = _reference_payload()
    payload["offers"][0]["unit_price"] = malformed_value

    response = _post(payload)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert "traceback" not in response.text.lower()


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"json": {"offers": [], "profile": {}}},
        {"json": []},
        {"content": "{not-json", "headers": {"content-type": "application/json"}},
    ],
)
def test_structurally_invalid_requests_use_request_validation(
    request_kwargs: dict[str, Any],
) -> None:
    response = TestClient(app).post(ENDPOINT, **request_kwargs)

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert "traceback" not in response.text.lower()


def test_openapi_registers_decision_contract() -> None:
    document = TestClient(app).get("/openapi.json").json()
    operation = document["paths"][ENDPOINT]["post"]

    assert operation["responses"]["200"]
    assert operation["responses"]["422"]
    assert (
        operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/DecisionEvaluationRequest"
    )
    assert (
        operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/DecisionEvaluationResponse"
    )
    assert "DecisionEvaluationRequest" in document["components"]["schemas"]
    assert "DecisionEvaluationResponse" in document["components"]["schemas"]
    assert (
        document["components"]["schemas"]["DecisionEvaluationRequest"]["example"]
        == REFERENCE_REQUEST
    )
    assert "decimal strings" in operation["description"]
    assert "does not" in operation["description"]
