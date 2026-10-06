"""ML infrastructure remains external to planning, HTTP, stored retrieval and ERP access."""

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))
    return {
        n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
    } | {
        alias.name.split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.Import)
        for alias in n.names
    }


def test_ml_is_external_to_existing_runtime_boundaries():
    for folder in ("decision_core", "optimization_adapter", "backend", "frontend", "persistence"):
        for path in (ROOT / folder).rglob("*.py"):
            # T15 composes T14 at the existing backend root; routes/storage/core stay external.
            if path in {
                ROOT / "backend/app/dependencies.py",
                ROOT / "backend/app/planning_case_schemas.py",
            }:
                assert imports(path).isdisjoint({"sklearn", "joblib"}), path
            else:
                assert imports(path).isdisjoint({"supplier_evaluation", "sklearn", "joblib"}), path
    for filename in ("contracts.py", "history.py", "dataset.py", "model.py", "artifacts.py"):
        assert imports(ROOT / "supplier_evaluation" / filename).isdisjoint(
            {
                "optimization_adapter",
                "decision_core",
                "backend",
                "odoo_adapter",
                "persistence",
                "reflex",
                "httpx",
                "pulp",
                "tools",
            }
        ), filename
    assert imports(ROOT / "supplier_evaluation/planning_bridge.py").isdisjoint(
        {"sklearn", "joblib"}
    )


def test_required_ml_dependency_and_python311_ci_cannot_silently_skip():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "scikit-learn==1.8.0" in project["project"]["dependencies"]
    assert "supplier_evaluation*" in project["tool"]["setuptools"]["packages"]["find"]["include"]
    quality = (ROOT / ".github/workflows/quality.yml").read_text()
    assert 'python-version: "3.11"' in quality
    assert "test_t14_runtime.py" in quality and "supplier_evaluation" in quality
    for path in (ROOT / "tests").glob("test_t14*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"importorskip", "skip"}, path
