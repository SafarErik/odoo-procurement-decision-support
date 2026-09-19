"""Executable architecture-boundary checks for implemented and spike increments."""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_decision_core_remains_erp_and_provenance_independent() -> None:
    forbidden_roots = {"application", "backend", "odoo_adapter", "tools"}
    for path in (PROJECT_ROOT / "decision_core").glob("*.py"):
        imported_roots = {name.split(".", 1)[0] for name in _imports(path)}
        assert imported_roots.isdisjoint(forbidden_roots), path
        assert "provenance" not in path.read_text(encoding="utf-8").lower(), path


def test_runtime_packages_do_not_import_development_fixture_tooling() -> None:
    for package in ("application", "backend", "decision_core", "odoo_adapter"):
        for path in (PROJECT_ROOT / package).rglob("*.py"):
            assert all(not name.startswith("tools") for name in _imports(path)), path


def test_assembler_does_not_implement_scoring_or_constraints() -> None:
    path = PROJECT_ROOT / "application" / "decision_input_assembly.py"
    imports = _imports(path)

    assert "decision_core.decision" not in imports
    assert "decision_core.constraints" not in imports
    assert "decision_core.normalization" not in imports
    source = path.read_text(encoding="utf-8")
    assert "evaluate_decision" not in source
    assert "total_score" not in source
    assert "normalized_value" not in source


def test_odoo_infrastructure_does_not_call_decision_core() -> None:
    for path in (PROJECT_ROOT / "odoo_adapter").glob("*.py"):
        assert all(not name.startswith("decision_core") for name in _imports(path)), path


def test_t7_spike_does_not_add_historical_kpi_runtime_code() -> None:
    for package in ("application", "backend", "decision_core", "frontend", "odoo_adapter"):
        for path in (PROJECT_ROOT / package).rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "delivery_schedule_adherence" not in source, path
            assert "on_time_rate" not in source, path
