"""Composition root for backend dependencies."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from application.decision_case_orchestration import ComparisonCaseReader
from application.historical_performance import HistoricalPerformancePort
from application.odoo_planning_input import bind_controlled_odoo_input
from application.planning_cases import PlanningCaseError
from application.planning_history import capture_features
from application.planning_serialization import json_value
from application.rfqs import RfqReader
from backend.app.config import settings
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.historical_performance_reader import OdooHistoricalPerformanceReader
from odoo_adapter.planning_history_reader import OdooPlanningHistoryReader, local_profile
from odoo_adapter.rfq_reader import OdooRfqReader
from persistence.postgres import SqlAlchemyUnitOfWork, create_session_factory
from supplier_evaluation.contracts import digest
from supplier_evaluation.qualified_odoo import load_qualified_model


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


def render_approved_document(content):
    from document_adapter.approved_pdf import render_approved_pdf

    return render_approved_pdf(content)


def resolve_odoo_planning_input(group_id, facts):
    """Read through adapters inside the locked new-case computation, never on replay."""
    import asyncio

    from application.decision_cases import RepositoryError
    from application.odoo_planning_input import bind_controlled_odoo_input
    from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable

    async def read():
        reader = get_comparison_case_reader()
        case = await reader.read_comparison_case(group_id)
        if not case.offers:
            raise ValueError("An explicit comparison case is required.")
        code, observed_at = await reader.read_currency_code(case.offers[0].currency_id)
        return bind_controlled_odoo_input(case, facts, code, observed_at)

    try:
        return asyncio.run(read())
    except (ProcurementDataUnavailable, ProcurementDataResponseError) as error:
        raise RepositoryError(
            "odoo_unavailable", "The selected Odoo input is unavailable."
        ) from error


def capture_local_history(revision):
    if revision != digest(local_profile()):
        raise PlanningCaseError("history_profile_changed", "Reload the changed history profile.")
    if not settings.odoo_history_database or not settings.odoo_history_api_key.get_secret_value():
        raise PlanningCaseError(
            "odoo_history_unavailable", "The dedicated history reader is not configured."
        )
    reader = OdooPlanningHistoryReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_history_database,
        api_key=settings.odoo_api_key.get_secret_value(),
        history_key=settings.odoo_history_api_key.get_secret_value(),
    )
    try:
        return asyncio.run(reader.capture(revision))
    except Exception as error:
        raise PlanningCaseError(
            "odoo_history_unavailable", "The bounded Odoo history could not be verified."
        ) from error


def resolve_odoo_history_input(revision, facts):
    case, code, observed, capture = capture_local_history(revision)
    features = capture_features(capture)
    facts = replace(
        facts,
        history=capture,
        suppliers=tuple(
            replace(
                s,
                history_reference=next(
                    f.source_reference
                    for f in features
                    if f.context.supplier_id == s.terms.supplier_id
                ),
            )
            for s in facts.suppliers
        ),
    )
    return bind_controlled_odoo_input(case, facts, code, observed)


def infer_odoo_history_features(features):
    try:
        path = settings.odoo_history_model_directory
        if path is None:
            raise ValueError("No qualified model configured.")
        model, manifest = load_qualified_model(path)
        return tuple(
            model.infer(snapshot, quantities) for snapshot, quantities in features
        ), manifest
    except Exception as error:
        raise PlanningCaseError(
            "odoo_history_model_incompatible",
            "Qualified Odoo-history model unavailable or incompatible.",
        ) from error


def preview_local_history():
    profile = local_profile()
    revision = digest(profile)
    case, code, observed, capture = capture_local_history(revision)
    parsed = json.loads(capture)
    features = capture_features(capture)
    readiness = "ready"
    try:
        if settings.odoo_history_model_directory is None:
            raise ValueError("Unconfigured model.")
        model, _ = load_qualified_model(settings.odoo_history_model_directory)
        if model.metadata["compatibility"]["database"] != profile["database"]:
            raise ValueError("Model database mismatch.")
    except Exception:
        readiness = "model_unavailable"
    now = datetime.now(UTC)
    deadline = (now + timedelta(days=7)).date().isoformat()
    source = {
        "source_type": "controlled_business_terms",
        "source_reference": "local-odoo-history-business-terms-v1",
        "observed_at": now.isoformat(),
    }
    suppliers = []
    for offer, capacity, moq in zip(
        sorted(case.offers, key=lambda o: o.supplier_id),
        (120, 100, 160),
        (50, 100, 150),
        strict=True,
    ):
        line = offer.lines[0]
        suppliers.append(
            {
                "supplier_id": offer.supplier_id,
                "offer_id": offer.offer_id,
                "unit_price": str(line.unit_price),
                "capacity": capacity,
                "available": True,
                "minimum_order_quantity": moq,
                "price_quantities": {"minimum": 1, "maximum": 1000},
                "delivery_quantities": {"minimum": 1, "maximum": 1000},
                "promised_date": deadline,
                "source": source,
            }
        )
    terms = {
        "company_id": case.offers[0].company_id,
        "as_of": now.isoformat(),
        "approval_reference": "local-odoo-history-demand-200-v1",
        "requirement": {
            "product_id": case.offers[0].lines[0].product_id,
            "approved_quantity": 200,
            "quantity_unit": case.offers[0].lines[0].uom_id,
            "currency": code,
            "required_date": deadline,
        },
        "requirement_source": source,
        "policy_source": source,
        "policy": {"max_suppliers": 2, "concentration_limit": "0.8", "epsilons": ["0.2"]},
        "suppliers": suppliers,
    }
    return {
        "profile_id": profile["id"],
        "profile_revision": revision,
        "database": profile["database"],
        "origin": profile["origin"],
        "model_readiness": readiness,
        "captured_at": parsed["evidence"]["cutoff"],
        "capture_hash": parsed["capture_hash"],
        "history": json_value(parsed["performance"]),
        "features": json_value(features),
        "terms": terms,
    }
