"""V2's replaceable solver boundary and V1 stored snapshot regressions stay separate."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))
    return {
        n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
    } | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}


def test_domain_and_orchestration_do_not_import_infrastructure_or_spikes():
    forbidden = {
        "pulp",
        "optimization_adapter",
        "application",
        "backend",
        "odoo_adapter",
        "persistence",
        "sqlalchemy",
        "psycopg",
        "reflex",
        "sklearn",
        "tools",
        "httpx",
    }
    for path in (ROOT / "decision_core/planning").glob("*.py"):
        assert imports(path).isdisjoint(forbidden), path
    assert imports(ROOT / "application/procurement_planning.py").isdisjoint(
        forbidden - {"application"}
    )


def test_solver_adapter_is_not_an_erp_or_application_client():
    for path in (ROOT / "optimization_adapter").glob("*.py"):
        assert imports(path).isdisjoint(
            {
                "application",
                "backend",
                "odoo_adapter",
                "persistence",
                "sklearn",
                "tools",
                "reflex",
                "httpx",
            }
        ), path


def test_t13_is_required_in_python_311_quality_not_an_optional_skip():
    project = (ROOT / "pyproject.toml").read_text()
    required = project.split("[project.optional-dependencies]")[0]
    assert '"pulp==3.3.0"' in required
    quality = (ROOT / ".github/workflows/quality.yml").read_text()
    assert 'python-version: "3.11"' in quality and "test_t13_solver_runtime.py" in quality
    for path in (ROOT / "tests").glob("test_t13*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"importorskip", "skip"}, path
