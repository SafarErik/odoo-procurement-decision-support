"""Composition root for backend dependencies."""

import asyncio
from functools import lru_cache

from application import planning_history
from application.errors import PlanningCaseError, RepositoryError
from application.odoo_planning_input import bind_odoo_history_input
from application.odoo_quotations import ComparisonCaseReader
from backend.app.config import settings
from decision_core.planning.planner import SOLVER_TIME_LIMIT_SECONDS
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.product_history_reader import OdooProductHistoryReader
from persistence.session import create_session_factory


def get_comparison_case_reader() -> ComparisonCaseReader:
    return OdooComparisonCaseReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_api_key.get_secret_value(),
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )


@lru_cache(maxsize=1)
def _session_factory():
    database_url = settings.decision_database_url.get_secret_value()
    if not database_url:
        return None
    _, factory = create_session_factory(database_url)
    return factory


def get_planning_unit_of_work():
    from persistence.planning_cases import SqlAlchemyPlanningUnitOfWork

    factory = _session_factory()
    if factory is None:
        raise RepositoryError(
            "invalid_database_configuration", "Planning persistence is unavailable."
        )
    return SqlAlchemyPlanningUnitOfWork(factory)


def planning_solver_factory():
    """Concrete solver/runtime construction stays at composition, after replay lookup."""
    from dataclasses import asdict

    from optimization_adapter.pulp_cbc import PulpCbcSolver

    try:
        solver = PulpCbcSolver()
        evidence = {
            "adapter": "t13-pulp-cbc",
            "runtime": solver.runtime_info(),
            "configuration": asdict(solver.configuration),
            "time_limit_seconds": SOLVER_TIME_LIMIT_SECONDS,
        }
    except Exception as error:
        raise RepositoryError(
            "solver_unavailable", "The configured solver runtime is unavailable."
        ) from error
    return solver, evidence


def render_approved_document(content, language, kind):
    from document_adapter.approved_pdf import render_audit_pdf, render_plan_pdf

    return (render_audit_pdf if kind == "audit" else render_plan_pdf)(content, language)


def get_purchase_history_reader():
    return OdooProductHistoryReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_t7s_api_key.get_secret_value(),
        timeout_seconds=max(15.0, settings.odoo_request_timeout_seconds),
    )


def capture_odoo_history(group_id):
    """Run the async Odoo capture from the sync route handlers (no event loop runs there)."""
    return asyncio.run(
        planning_history.capture_odoo_history(
            get_comparison_case_reader(),
            get_purchase_history_reader(),
            group_id,
            database=settings.odoo_database,
            data_origin=settings.odoo_history_data_origin,
        )
    )


def resolve_odoo_history_input(group_id, facts):
    return bind_odoo_history_input(capture_odoo_history(group_id), facts)


def load_history_model():
    from supplier_evaluation.history_model import load_model

    directory = settings.supplier_history_model_directory
    if directory is None:
        raise ValueError("No history model configured.")
    model, manifest = load_model(directory, trusted_local=True)
    if model.metadata["database"] != settings.odoo_database:
        raise ValueError("The history model was trained on another Odoo database.")
    if model.metadata["data_origin"] != settings.odoo_history_data_origin:
        raise ValueError("The history model was trained on history of another data origin.")
    return model, manifest


def infer_odoo_history_features(features):
    try:
        model, manifest = load_history_model()
        return tuple(
            model.infer(snapshot, quantities) for snapshot, quantities in features
        ), manifest
    except Exception as error:
        raise PlanningCaseError(
            "odoo_history_model_incompatible",
            "The Odoo-history supplier model is unavailable or incompatible.",
        ) from error


def preview_odoo_history(group_id):
    captured = capture_odoo_history(group_id)
    try:
        model_company = load_history_model()[0].metadata["company_id"]
    except Exception:  # any unusable model: the preview reports model_unavailable
        model_company = None
    return planning_history.odoo_history_preview(
        group_id, captured, database=settings.odoo_database, model_company=model_company
    )
