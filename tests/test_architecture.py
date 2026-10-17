"""Executable architecture-boundary checks."""

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
    path = PROJECT_ROOT / "application" / "historical_performance.py"
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
    source = (PROJECT_ROOT / "application" / "historical_performance.py").read_text(
        encoding="utf-8"
    )
    assert "class HistoricalPerformancePort(Protocol)" in source


def test_t7s_addon_is_projection_only() -> None:
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
    path = PROJECT_ROOT / "odoo_adapter" / "historical_performance_reader.py"
    source = path.read_text(encoding="utf-8")

    assert '"procurement.inventory.history.projection"' in source
    assert '"read_bounded_history"' in source
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
    history_source = (PROJECT_ROOT / "odoo_adapter" / "historical_performance_reader.py").read_text(
        encoding="utf-8"
    )
    assert all(
        f"/json/2/{{_MODEL}}/{method}" not in history_source
        for method in ("create", "write", "unlink")
    )


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
