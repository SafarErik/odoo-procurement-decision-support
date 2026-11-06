"""Fixtures shared by the fast and integration tests."""

from datetime import UTC, datetime

import pytest

# Generated history, training split and saved cases all end here, so exact expected
# values do not depend on the day the suite runs (see ``t15_helpers.odoo_case_api``).
REFERENCE_NOW = datetime(2026, 11, 5, 18, tzinfo=UTC)


@pytest.fixture(scope="session")
def odoo_history(tmp_path_factory):
    """Generated Odoo-shaped purchase history and a tree trained on it, once per session."""
    from tests.test_odoo_purchase_history import build_history

    return build_history(tmp_path_factory.mktemp("odoo-history"), REFERENCE_NOW)
