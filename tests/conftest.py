"""Fixtures shared by the fast and integration tests."""

import pytest


@pytest.fixture(scope="session")
def odoo_history(tmp_path_factory):
    """Generated Odoo-shaped purchase history and a tree trained on it, once per session."""
    from tests.test_odoo_purchase_history import build_history

    return build_history(tmp_path_factory.mktemp("odoo-history"))
