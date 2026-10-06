"""The supported demo uses matched fixtures and the real controlled API composition."""

import argparse
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.config import settings
from backend.app.main import app
from tests.t15_helpers import MemoryPlanningUnitOfWork
from tools.t15_demo import local_url, prepare_demo, run_demo


def test_demo_prepares_matched_assets_and_exercises_http_without_training(tmp_path, monkeypatch):
    payload = prepare_demo(tmp_path)
    assert json.loads((tmp_path / "create-request.json").read_text()) == payload
    uow = MemoryPlanningUnitOfWork()
    monkeypatch.setattr("backend.app.routes.planning_cases.get_planning_unit_of_work", lambda: uow)
    monkeypatch.setattr(settings, "t15_trusted_model_directory", tmp_path / "model")
    monkeypatch.setattr(settings, "t12_trusted_caller_token", SecretStr("demo-test-token"))

    def no_training(*args, **kwargs):
        raise AssertionError("The HTTP demonstration attempted training.")

    monkeypatch.setattr("sklearn.tree.DecisionTreeClassifier.fit", no_training)
    with TestClient(app, headers={"Authorization": "Bearer demo-test-token"}) as client:
        report = run_demo(tmp_path, client)
    base, scenario = report["base"], report["scenario"]
    assert base["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] == "102"
    assert base["snapshot"]["result"]["alternatives"][0]["total_cost"] == "109"
    assert scenario["snapshot"]["result"]["minimum_cost_plan"]["total_cost"] == "106"
    excluded = payload["suppliers"][0]["supplier_id"]
    assert (
        next(
            a["quantity"]
            for a in scenario["snapshot"]["result"]["minimum_cost_plan"]["allocations"]
            if a["supplier_id"] == excluded
        )
        == 0
    )
    assert len(uow.rows) == 2 and report["stored_retrieval_and_replay_verified"]
    assert json.loads((tmp_path / f"run-{report['base_key']}.json").read_text()) == report


@pytest.mark.parametrize(
    "value",
    ["https://example.com", "http://user:password@localhost:8000", "http://localhost:8000/path"],
)
def test_demo_rejects_nonlocal_or_credentialed_origins(value):
    with pytest.raises(argparse.ArgumentTypeError):
        local_url(value)
