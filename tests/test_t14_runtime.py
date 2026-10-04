"""Mandatory installed ML, actual offline train/reload/infer and genuine CBC execution."""

import sys
from decimal import Decimal
from fractions import Fraction

from supplier_evaluation.artifacts import load_model, save_model
from supplier_evaluation.cli import main
from supplier_evaluation.contracts import QuantityValidity
from supplier_evaluation.dataset import generate_dataset, load_dataset, save_dataset
from supplier_evaluation.evaluation import demonstrate_planning
from supplier_evaluation.model import runtime, train


def test_required_training_reload_inference_and_actual_cbc(tmp_path):
    assert sys.version_info[:2] >= (3, 11)
    assert runtime()["sklearn"] == "1.8.0"
    assert runtime()["numpy"] == "2.3.5"
    assert runtime()["scipy"] == "1.16.3"
    path = tmp_path / "dataset.json"
    save_dataset(path, generate_dataset())
    split = load_dataset(path)
    model = train(split)
    save_model(model, tmp_path / "model")
    loaded = load_model(tmp_path / "model", trusted_local=True)
    assert loaded.infer(split.test[0].snapshot, QuantityValidity(1, 1000, "controlled-v1")) == (
        model.infer(split.test[0].snapshot, QuantityValidity(1, 1000, "controlled-v1"))
    )
    demo = demonstrate_planning(loaded, split)
    assert demo["status"] == "optimal"
    assert demo["minimum_cost"]["total_cost"] == "102"
    assert demo["alternatives"]
    for plan in (demo["minimum_cost"], *demo["alternatives"]):
        assert sum(a["quantity"] for a in plan["allocations"]) == 10
        assert sum(a["quantity"] > 0 for a in plan["allocations"]) == 2
        assert all(a["quantity"] <= 8 for a in plan["allocations"])
    assert Decimal(demo["alternatives"][0]["total_cost"]) <= Decimal("102") * Decimal("1.1")
    assert Fraction(demo["alternatives"][0]["risk_exposure"]) < Fraction(
        demo["minimum_cost"]["risk_exposure"]
    )
    assert demo["context"]["controlled_fixture"]


def test_documented_cli_steps_generate_train_reload_evaluate_infer_and_demo(
    tmp_path, monkeypatch, capsys
):
    for command in ("generate", "train", "evaluate", "infer", "demo", "reproduce"):
        monkeypatch.setattr(sys, "argv", ["t14", command, "--directory", str(tmp_path)])
        main()
        capsys.readouterr()
    assert (tmp_path / "evaluate.json").exists()
    assert (tmp_path / "infer.json").exists()
    assert (tmp_path / "demo.json").exists()
    assert (tmp_path / "reproduce.json").exists()
