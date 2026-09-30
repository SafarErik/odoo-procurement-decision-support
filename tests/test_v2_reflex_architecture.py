"""The opt-in frontend remains a presentation/client layer without domain dependencies."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_spike_has_no_erp_database_ml_or_solver_imports():
    forbidden = {
        "application",
        "backend",
        "odoo_adapter",
        "decision_core",
        "persistence",
        "sqlalchemy",
        "psycopg",
        "sklearn",
        "pulp",
        "tools",
    }
    for path in (ROOT / "frontend/v2_spike").glob("*.py"):
        names = []
        for node in ast.walk(ast.parse(path.read_text(), feature_version=(3, 11))):
            if isinstance(node, ast.Import):
                names.extend(n.name for n in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
        assert not forbidden.intersection(name.split(".")[0] for name in names), path


def test_unsafe_transport_and_mock_calls_stay_out_of_components():
    for name in ("page.py", "state.py", "presentation.py"):
        source = (ROOT / "frontend/v2_spike" / name).read_text()
        assert "read_text(" not in source
        assert "httpx" not in source
        assert "optimize(" not in source and "predict(" not in source
    source = (ROOT / "frontend/app.py").read_text()
    assert 'os.environ.get("ENABLE_V2_FRONTEND_SPIKE") == "1"' in source
