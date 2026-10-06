"""Composition root for backend dependencies."""

from functools import lru_cache

from application.decision_case_orchestration import ComparisonCaseReader
from application.historical_performance import HistoricalPerformancePort
from application.rfqs import RfqReader
from backend.app.config import settings
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.historical_performance_reader import OdooHistoricalPerformanceReader
from odoo_adapter.rfq_reader import OdooRfqReader
from persistence.postgres import SqlAlchemyUnitOfWork, create_session_factory


def get_rfq_reader() -> RfqReader:
    """Build the configured read-only procurement adapter."""

    return OdooRfqReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_api_key.get_secret_value(),
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )


def get_comparison_case_reader() -> ComparisonCaseReader:
    return OdooComparisonCaseReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_api_key.get_secret_value(),
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )


def get_historical_performance_reader() -> HistoricalPerformancePort:
    return OdooHistoricalPerformanceReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_t7s_api_key.get_secret_value(),
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )


@lru_cache(maxsize=1)
def _session_factory():
    database_url = settings.decision_database_url.get_secret_value()
    if not database_url:
        return None
    _, factory = create_session_factory(database_url)
    return factory


def get_decision_unit_of_work() -> SqlAlchemyUnitOfWork:
    factory = _session_factory()
    if factory is None:
        from application.decision_cases import RepositoryError

        raise RepositoryError(
            "invalid_database_configuration", "Decision persistence is unavailable."
        )
    return SqlAlchemyUnitOfWork(factory)


def get_planning_unit_of_work():
    from application.decision_cases import RepositoryError
    from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork

    factory = _session_factory()
    if factory is None:
        raise RepositoryError(
            "invalid_database_configuration", "Planning persistence is unavailable."
        )
    return SqlAlchemyPlanningUnitOfWork(factory)


def infer_planning_features(features):
    """Load only the owner-configured, locally generated artifact on new base creation."""
    import hashlib
    import json

    from application.decision_cases import RepositoryError
    from supplier_evaluation.artifacts import load_model

    directory = settings.t15_trusted_model_directory
    try:
        if directory is None:
            raise ValueError("No trusted model configured.")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        model = load_model(directory, trusted_local=True)
        if (
            manifest["metadata"] != model.metadata
            or manifest["artifact_sha256"]
            != hashlib.sha256((directory / "tree.joblib").read_bytes()).hexdigest()
        ):
            raise ValueError("Artifact changed during loading.")
    except Exception as error:
        raise RepositoryError(
            "model_unavailable", "The configured trusted model is unavailable or incompatible."
        ) from error
    return tuple(model.infer(snapshot, quantities) for snapshot, quantities in features), manifest


def planning_solver_factory():
    """Concrete solver/runtime construction stays at composition, after replay lookup."""
    from dataclasses import asdict

    from application.decision_cases import RepositoryError
    from optimization_adapter.pulp_cbc import PulpCbcSolver

    try:
        solver = PulpCbcSolver()
        evidence = {
            "adapter": "t13-pulp-cbc",
            "runtime": solver.runtime_info(),
            "configuration": asdict(solver.configuration),
            "time_limit_seconds": 30.0,
        }
    except Exception as error:
        raise RepositoryError(
            "solver_unavailable", "The configured solver runtime is unavailable."
        ) from error
    return solver, evidence
