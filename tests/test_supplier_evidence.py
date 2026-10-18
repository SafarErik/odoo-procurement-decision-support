"""Stored evidence presentation preserves exact records and constraint distinctions."""

import asyncio
import json
from copy import deepcopy

import httpx
import pytest

from frontend.i18n import day
from frontend.planning_client import _map_case, fetch_planning_case
from tests.test_t16_stored_planning import TOKEN
from tests.test_t16_stored_planning import stored_cases as stored_cases


def test_exact_evidence_and_reference_time_survive_readable_projection(stored_cases):
    for payload in stored_cases[1:]:
        before = deepcopy(payload)
        display = _map_case(payload, payload["case_id"])
        assert json.loads(display.details["snapshot_json"]) == payload["snapshot"]
        for row, assessment in zip(
            display.assessments, payload["snapshot"]["assessments"], strict=True
        ):
            assert row["reference_time"] == assessment["snapshot"]["cutoff"].replace("Z", "+00:00")
            assert row["score"] == assessment["score"]
            assert row["model"] == assessment["model_id"]
            assert row["history_window"].endswith(day(assessment["snapshot"]["history_end"], "en"))
            assert "future receipts" in row["class_meaning"]
            assert row["name"]  # Canonical supplier identity supplies missing business labels.
        assert payload == before


def test_zero_allocation_is_distinct_from_real_saved_exclusion(stored_cases):
    base, outage, infeasible = stored_cases[1:]
    original = _map_case(base, base["case_id"])
    assert "this is not an exclusion" in original.plans[0]["buyer_notes"]
    assert "all of its capacity" in original.plans[0]["buyer_notes"]
    assert "allowed number of suppliers" in original.plans[0]["buyer_notes"]
    changed = _map_case(outage, outage["case_id"])
    assert "Excluded: unavailable" in changed.plans[0]["buyer_notes"]
    failed = _map_case(infeasible, infeasible["case_id"])
    assert failed.plans == [] and "cannot cover demand" in failed.details["buyer_diagnostics"]
    assert failed.assessments == original.assessments  # An outage does not reclassify suppliers.


@pytest.mark.parametrize("fault", ["missing_identity", "observed_source", "nonfinite_path"])
def test_invalid_evidence_remains_unavailable_without_retry_or_source_promotion(
    stored_cases, fault
):
    payload = deepcopy(stored_cases[1])
    assessment = payload["snapshot"]["assessments"][0]
    if fault == "missing_identity":
        assessment["snapshot"]["context"]["supplier_id"] = ""
    elif fault == "observed_source":
        assessment["snapshot"]["source_type"] = "observed_odoo"
    else:
        assessment["path"][0]["threshold"] = float("nan")
    calls = []

    def respond(request):
        calls.append(request)
        assert request.method == "GET"
        return httpx.Response(200, text=json.dumps(payload))

    display, error = asyncio.run(
        fetch_planning_case(
            "http://test/cases", payload["case_id"], TOKEN, transport=httpx.MockTransport(respond)
        )
    )
    assert display is None and "incomplete or unsupported" in error and len(calls) == 1
