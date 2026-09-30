"""Production packages and mathematical core remain independent of ML machinery."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imports(path):
    result = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.append(node.module)
    return result


def test_ml_layers_and_optimizer_have_separate_dependencies():
    for file in ("dataset.py", "model.py"):
        names = imports(ROOT / "tools/v2_ml_risk" / file)
        assert not any(
            name.startswith(
                ("odoo", "application", "backend", "persistence", "tools.v2_optimization")
            )
            for name in names
        )
        if file == "dataset.py":
            assert not any(name.startswith(("sklearn", "numpy")) for name in names)
    for path in (ROOT / "tools/v2_optimization").glob("*.py"):
        assert not any(
            name.startswith(("sklearn", "numpy", "tools.v2_ml_risk")) for name in imports(path)
        )


def test_runtime_has_no_ml_spike_imports():
    for package in (
        "application",
        "backend",
        "decision_core",
        "odoo_adapter",
        "persistence",
        "frontend",
    ):
        for path in (ROOT / package).rglob("*.py"):
            assert not any(
                name.startswith(("sklearn", "tools.v2_ml_risk")) for name in imports(path)
            )
