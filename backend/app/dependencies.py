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
