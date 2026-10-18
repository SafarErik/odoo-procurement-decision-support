"""FastAPI for the browser suite: real routes and PostgreSQL, fixture Odoo and model.

The P1/P2 fast tests' fake Odoo (open quotation group 501 with three quotations and
generated purchase history) answers every Odoo read, and a tree trained on that history
is the supplier model. Nothing here talks to a real Odoo. Run as
``python -m tests.e2e.odoo_fixture_api PORT MODEL_DIRECTORY``.
"""

import os
import sys
from pathlib import Path

import pytest
import uvicorn
from pydantic import SecretStr


def main(port: int, model_directory: Path) -> None:
    from tests.test_odoo_purchase_history import COMPANY, build_history, install_fake_odoo

    model_directory.mkdir(parents=True, exist_ok=True)
    patch = pytest.MonkeyPatch()
    install_fake_odoo(build_history(model_directory), patch)
    from backend.app.config import settings
    from backend.app.main import app

    # The fake installs a fixed test token; the harness owns a generated one.
    settings.api_service_token = SecretStr(os.environ["API_SERVICE_TOKEN"])
    settings.planning_library_company_id = COMPANY
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
