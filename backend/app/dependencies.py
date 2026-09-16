"""Composition root for backend dependencies."""

from application.rfqs import RfqReader
from backend.app.config import settings
from odoo_adapter.rfq_reader import OdooRfqReader


def get_rfq_reader() -> RfqReader:
    """Build the configured read-only procurement adapter."""

    return OdooRfqReader(
        base_url=settings.odoo_base_url,
        database=settings.odoo_database,
        api_key=settings.odoo_api_key.get_secret_value(),
        timeout_seconds=settings.odoo_request_timeout_seconds,
    )
