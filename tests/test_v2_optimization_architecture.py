"""Boundary checks run even when the optional experimental solver is absent."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v2_spike_imports_only_standard_library_solver_and_own_package():
    allowed = {
        "dataclasses",
        "decimal",
        "enum",
        "fractions",
        "json",
        "platform",
        "statistics",
        "subprocess",
        "time",
        "unittest",
        "pulp",
        "tools",
    }
    for path in (ROOT / "tools" / "v2_optimization").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert all(name.split(".")[0] in allowed for name in imports), path
        assert all(
            not name.startswith("tools.") or name.startswith("tools.v2_optimization")
            for name in imports
        ), path


def test_existing_runtime_does_not_import_the_spike():
    for package in (
        "application",
        "backend",
        "decision_core",
        "odoo_adapter",
        "persistence",
        "frontend",
    ):
        for path in (ROOT / package).rglob("*.py"):
            assert "v2_optimization" not in path.read_text(encoding="utf-8"), path
