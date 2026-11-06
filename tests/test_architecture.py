"""Executable architecture-boundary checks."""

import ast
import tomllib
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


def _import_roots(path: Path) -> set[str]:
    """Top-level package names a module imports."""
    return {name.split(".", 1)[0] for name in _imports(path)}


def test_decision_core_remains_erp_and_provenance_independent() -> None:
    forbidden_roots = {"application", "backend", "odoo_adapter", "persistence", "tools"}
    for path in (PROJECT_ROOT / "decision_core").rglob("*.py"):
        imported_roots = {name.split(".", 1)[0] for name in _imports(path)}
        assert imported_roots.isdisjoint(forbidden_roots), path
        assert "provenance" not in path.read_text(encoding="utf-8").lower(), path


def test_runtime_packages_do_not_import_development_fixture_tooling() -> None:
    for package in ("application", "backend", "decision_core", "odoo_adapter"):
        for path in (PROJECT_ROOT / package).rglob("*.py"):
            assert all(not name.startswith("tools") for name in _imports(path)), path


def test_odoo_infrastructure_does_not_call_decision_core() -> None:
    for path in (PROJECT_ROOT / "odoo_adapter").glob("*.py"):
        assert all(not name.startswith("decision_core") for name in _imports(path)), path


def test_historical_models_and_port_are_erp_neutral() -> None:
    path = PROJECT_ROOT / "application" / "purchase_history.py"
    imports = _imports(path)
    source = path.read_text(encoding="utf-8")

    assert all(not name.startswith("odoo_adapter") for name in imports)
    for odoo_name in (
        "commercial_partner_id",
        "expected_arrival_at",
        "stock_move_id",
        "stock_picking_id",
        "purchase_order_line_id",
    ):
        assert odoo_name not in source


def test_application_history_flow_depends_on_port_not_concrete_odoo_reader() -> None:
    application_imports = set()
    for path in (PROJECT_ROOT / "application").glob("*.py"):
        application_imports.update(_imports(path))

    assert all(not name.startswith("odoo_adapter") for name in application_imports)
    source = (PROJECT_ROOT / "application" / "purchase_history.py").read_text(encoding="utf-8")
    assert "class PurchaseHistoryPort(Protocol)" in source


def test_inventory_projection_addon_is_projection_only() -> None:
    addon = PROJECT_ROOT / "infra" / "odoo" / "addons" / "t7s_inventory_history_projection"
    for path in addon.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "delivery_schedule_adherence" not in source, path
        assert "on_time_rate" not in source, path
        assert all(
            not name.startswith(("application", "backend", "decision_core", "frontend"))
            for name in _imports(path)
        ), path
        assert "env.cr" not in source, path


def test_bounded_projection_is_the_only_inventory_history_transport_route() -> None:
    path = PROJECT_ROOT / "odoo_adapter" / "product_history_reader.py"
    source = path.read_text(encoding="utf-8")

    assert 'METHOD = "read_product_history"' in source
    for forbidden_model in ('"stock.move"', '"stock.move.line"', '"stock.picking"'):
        assert forbidden_model not in source
    for forbidden_method in ('"create"', '"write"', '"unlink"'):
        assert forbidden_method not in source


def test_runtime_history_path_has_no_admin_secret_or_write_call() -> None:
    runtime_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for package in ("application", "odoo_adapter")
        for path in (PROJECT_ROOT / package).glob("*.py")
    )

    assert "ODOO_MASTER_PASSWORD" not in runtime_sources
    history_source = (PROJECT_ROOT / "odoo_adapter" / "product_history_reader.py").read_text(
        encoding="utf-8"
    )
    assert "/json/2/{MODEL}/{METHOD}" in history_source
    assert all(f'"{method}"' not in history_source for method in ("create", "write", "unlink"))


def test_odoo_adapter_calls_only_read_methods() -> None:
    """Every JSON-2 call the runtime adapter can make resolves to a known read method."""
    read_methods = {"search_read", "search_count", "read_product_history"}
    called = set()
    for path in sorted((PROJECT_ROOT / "odoo_adapter").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        constants = {
            target.id: node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                url = "".join(
                    part.value
                    if isinstance(part, ast.Constant)
                    else "{" + ast.unparse(part.value) + "}"
                    for part in node.values
                )
                if "/json/2/" not in url:
                    continue
                method = url.rsplit("/", 1)[1]
                if method == "{method}":  # the generic helper; its callers are checked below
                    continue
                called.add(constants[method.strip("{}")] if method.startswith("{") else method)
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "_post":
                assert isinstance(node.args[2], ast.Constant), (path, node.lineno)
                called.add(node.args[2].value)
    assert called and called <= read_methods, called - read_methods


def test_planning_core_stays_erp_neutral_and_provenance_free() -> None:
    for path in (PROJECT_ROOT / "decision_core").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "provenance" not in source.lower(), path
        assert "source_reference" not in source, path
        assert "source_type" not in source, path


def test_application_depends_only_on_persistence_ports() -> None:
    for path in (PROJECT_ROOT / "application").glob("*.py"):
        imports = _imports(path)
        assert all(not name.startswith("persistence") for name in imports), path
        assert all(not name.startswith(("sqlalchemy", "psycopg", "alembic")) for name in imports), (
            path
        )


def test_postgres_adapter_points_inward_and_domain_objects_are_not_orm_models() -> None:
    for path in (PROJECT_ROOT / "persistence").glob("*.py"):
        imports = _imports(path)
        assert all(not name.startswith(("backend", "frontend", "odoo_adapter")) for name in imports)

    domain_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for package in ("application", "decision_core")
        for path in (PROJECT_ROOT / package).glob("*.py")
    )
    assert "DeclarativeBase" not in domain_sources
    assert "mapped_column" not in domain_sources


def test_orchestration_and_http_boundaries_are_narrow() -> None:
    application_imports = set()
    for path in (PROJECT_ROOT / "application").glob("*.py"):
        application_imports.update(_imports(path))
    assert all(
        not name.startswith(("odoo_adapter", "sqlalchemy", "psycopg", "alembic", "backend"))
        for name in application_imports
    )
    route = PROJECT_ROOT / "backend" / "app" / "routes" / "planning_cases.py"
    route_imports = _imports(route)
    assert all(
        not name.startswith(("odoo_adapter", "decision_core.planning.planner"))
        for name in route_imports
    )
    route_source = route.read_text(encoding="utf-8")
    assert "read_comparison_case" not in route_source
    assert "read_inventory_history" not in route_source
    assert "require_trusted_caller" in route_source
    for path in (PROJECT_ROOT / "persistence").glob("*.py"):
        assert all(
            not name.startswith(("backend", "frontend", "odoo_adapter")) for name in _imports(path)
        )


def test_purchase_history_reader_uses_only_the_bounded_export() -> None:
    source = (PROJECT_ROOT / "odoo_adapter" / "product_history_reader.py").read_text(
        encoding="utf-8"
    )
    assert 'MODEL = "procurement.product.history.export"' in source
    for forbidden in ('"stock.move"', '"stock.picking"', '"create"', '"write"', '"unlink"'):
        assert forbidden not in source


def test_seeding_tool_is_never_reachable_from_runtime_code() -> None:
    for package in ("application", "backend", "odoo_adapter", "supplier_evaluation", "frontend"):
        for path in (PROJECT_ROOT / package).rglob("*.py"):
            if ".web" in path.parts:
                continue
            assert "seed_odoo_history" not in path.read_text(encoding="utf-8"), path
            assert all(not name.startswith("tools") for name in _imports(path)), path


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
    for path in (PROJECT_ROOT / "decision_core/planning").glob("*.py"):
        assert _import_roots(path).isdisjoint(forbidden), path
    assert _import_roots(PROJECT_ROOT / "application/procurement_planning.py").isdisjoint(
        forbidden - {"application"}
    )


def test_solver_adapter_is_not_an_erp_or_application_client():
    for path in (PROJECT_ROOT / "optimization_adapter").glob("*.py"):
        assert _import_roots(path).isdisjoint(
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


def test_solver_is_required_in_python_311_quality_not_an_optional_skip():
    project = (PROJECT_ROOT / "pyproject.toml").read_text()
    required = project.split("[project.optional-dependencies]")[0]
    assert '"pulp==3.3.0"' in required
    quality = (PROJECT_ROOT / ".github/workflows/quality.yml").read_text()
    assert 'python-version: "3.11"' in quality
    assert 'run: pytest -m "not integration and not e2e" -v' in quality
    runtime = ast.parse((PROJECT_ROOT / "tests/test_solver_runtime.py").read_text())
    assert not {"integration", "e2e"} & {
        node.attr for node in ast.walk(runtime) if isinstance(node, ast.Attribute)
    }
    for name in ("test_milp_planning.py", "test_solver_runtime.py", "test_architecture.py"):
        path = PROJECT_ROOT / "tests" / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"importorskip", "skip"}, path


def test_ml_is_external_to_existing_runtime_boundaries():
    for folder in ("decision_core", "optimization_adapter", "backend", "frontend", "persistence"):
        for path in (PROJECT_ROOT / folder).rglob("*.py"):
            # The backend root composes the ML package and config reads its data-origin
            # vocabulary; routes/storage/core stay external.
            if path in {
                PROJECT_ROOT / "backend/app/config.py",
                PROJECT_ROOT / "backend/app/dependencies.py",
                PROJECT_ROOT / "backend/app/planning_case_schemas.py",
            }:
                assert _import_roots(path).isdisjoint({"sklearn", "joblib"}), path
            else:
                assert _import_roots(path).isdisjoint(
                    {"supplier_evaluation", "sklearn", "joblib"}
                ), path
    for filename in ("contracts.py", "purchase_history.py", "history_model.py"):
        assert _import_roots(PROJECT_ROOT / "supplier_evaluation" / filename).isdisjoint(
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


def test_supplier_evaluation_does_not_import_application():
    """The application uses the ML package, never the reverse: no import cycle."""
    for path in (PROJECT_ROOT / "supplier_evaluation").glob("*.py"):
        assert "application" not in _import_roots(path), path


def test_required_ml_dependency_and_python311_ci_cannot_silently_skip():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    assert "scikit-learn==1.8.0" in project["project"]["dependencies"]
    assert "supplier_evaluation*" in project["tool"]["setuptools"]["packages"]["find"]["include"]
    quality = (PROJECT_ROOT / ".github/workflows/quality.yml").read_text()
    assert 'python-version: "3.11"' in quality
    assert 'run: pytest -m "not integration and not e2e" -v' in quality
    assert "supplier_evaluation" in quality
    from supplier_evaluation.history_model import runtime

    assert runtime()["sklearn"] == "1.8.0"
    assert runtime()["numpy"] == "2.3.5"
    assert runtime()["scipy"] == "1.16.3"
    # Actual training runs in the fast gate, unmarked and never skipped.
    training = PROJECT_ROOT / "tests/test_odoo_purchase_history.py"
    assert not {"integration", "e2e"} & {
        node.attr
        for node in ast.walk(ast.parse(training.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute)
    }
    for path in (
        PROJECT_ROOT / "tests/test_risk_bridge.py",
        PROJECT_ROOT / "tests/test_architecture.py",
        training,
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"importorskip", "skip"}, path
