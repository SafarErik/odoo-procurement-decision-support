"""Composition root for backend dependencies."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from application.odoo_planning_input import bind_controlled_odoo_input
from application.odoo_quotations import ComparisonCaseReader
from application.planning_cases import PlanningCaseError
from application.planning_history import (
    HistoryCaptureError,
    build_capture,
    capture_features,
    capture_origin,
    history_query,
)
from application.planning_serialization import json_value
from application.rfqs import RfqReader
from backend.app.config import settings
from odoo_adapter.comparison_case_reader import OdooComparisonCaseReader
from odoo_adapter.product_history_reader import OdooProductHistoryReader
from odoo_adapter.rfq_reader import OdooRfqReader
from persistence.session import create_session_factory
from supplier_evaluation.contracts import Context


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


@lru_cache(maxsize=1)
def _session_factory():
    database_url = settings.decision_database_url.get_secret_value()
    if not database_url:
        return None
    _, factory = create_session_factory(database_url)
    return factory


def get_planning_unit_of_work():
    from application.errors import RepositoryError
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

    from application.errors import RepositoryError
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


def render_approved_document(content, language):
    from document_adapter.approved_pdf import render_approved_pdf

    return render_approved_pdf(content, language)


def get_purchase_history_reader():
    return OdooProductHistoryReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_t7s_api_key.get_secret_value(),
        timeout_seconds=max(15.0, settings.odoo_request_timeout_seconds),
    )


def capture_odoo_history(group_id):
    """Read one quotation group and its product's bounded history; never on replay."""
    from application.rfqs import ProcurementDataResponseError, ProcurementDataUnavailable

    async def read():
        reader = get_comparison_case_reader()
        case = await reader.read_comparison_case(group_id)
        if not case.offers or any(len(o.lines) != 1 for o in case.offers):
            raise ValueError("A one-line quotation group is required.")
        code, observed = await reader.read_currency_code(case.offers[0].currency_id)
        line, company = case.offers[0].lines[0], case.offers[0].company_id
        query = history_query(company, line.product_id, datetime.now(UTC).replace(microsecond=0))
        snapshot = await get_purchase_history_reader().read_purchase_history(query)
        contexts = tuple(
            Context(o.supplier_id, company, line.product_id, line.uom_id) for o in case.offers
        )
        return (
            case,
            code,
            observed,
            build_capture(
                snapshot, contexts, settings.odoo_database, settings.odoo_history_data_origin
            ),
        )

    try:
        return asyncio.run(read())
    except HistoryCaptureError as error:
        raise PlanningCaseError("odoo_history_insufficient", str(error)) from error
    except (ProcurementDataUnavailable, ProcurementDataResponseError) as error:
        raise PlanningCaseError(
            "odoo_history_unavailable", "The Odoo quotation group or its history is unavailable."
        ) from error


def resolve_odoo_history_input(group_id, facts):
    case, code, observed, capture = capture_odoo_history(group_id)
    references = {f.context.supplier_id: f.source_reference for f in capture_features(capture)}
    facts = replace(
        facts,
        history=capture,
        labels=case.labels,
        suppliers=tuple(
            replace(s, history_reference=references.get(s.terms.supplier_id, s.history_reference))
            for s in facts.suppliers
        ),
    )
    return bind_controlled_odoo_input(case, facts, code, observed)


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
    """Read-only preview with suggested buyer terms; nothing is stored."""
    case, code, observed, capture = capture_odoo_history(group_id)
    features = capture_features(capture)
    readiness, origin = "ready", capture_origin(capture)
    try:
        model, _ = load_history_model()
        if model.metadata["company_id"] != case.offers[0].company_id:
            raise ValueError("Model company mismatch.")
    except Exception:
        readiness = "model_unavailable"
    now = datetime.now(UTC)
    line = case.offers[0].lines[0]
    demand = int(line.quantity)
    deadline = (now + timedelta(days=7)).date().isoformat()
    source = {
        "source_type": "buyer_default_terms",
        "source_reference": "odoo-history-preview-defaults-v2",
        "observed_at": now.isoformat(),
    }
    suppliers = [
        {
            "supplier_id": offer.supplier_id,
            "offer_id": offer.offer_id,
            "unit_price": str(offer.lines[0].unit_price),
            "capacity": max(1, -(-demand * 6 // 10)),
            "available": True,
            "minimum_order_quantity": None,
            "price_quantities": {"minimum": 1, "maximum": 1000},
            "delivery_quantities": {"minimum": 1, "maximum": 1000},
            "promised_date": deadline,
            "source": source,
        }
        for offer in sorted(case.offers, key=lambda o: o.supplier_id)
    ]
    terms = {
        "company_id": case.offers[0].company_id,
        "as_of": now.isoformat(),
        "approval_reference": f"odoo-history-demand-{demand}-v2",
        "requirement": {
            "product_id": line.product_id,
            "approved_quantity": demand,
            "quantity_unit": line.uom_id,
            "currency": code,
            "required_date": deadline,
        },
        "requirement_source": source,
        "policy_source": source,
        "policy": {
            "max_suppliers": 2,
            "concentration_limit": "0.8",
            "epsilons": ["0.05", "0.1", "0.2"],
            "diversification_epsilon": "0.2",
        },
        "suppliers": suppliers,
    }
    parsed = json.loads(capture)
    return {
        "purchase_group_id": group_id,
        "database": settings.odoo_database,
        "data_origin": origin,
        "model_readiness": readiness,
        "captured_at": parsed["evidence"]["cutoff"],
        "capture_hash": parsed["capture_hash"],
        "features": json_value(features),
        "history": [
            {"supplier_id": f.context.supplier_id}
            | dict(zip(f.feature_names, f.values, strict=True))
            for f in features
        ],
        "terms": terms,
    }
