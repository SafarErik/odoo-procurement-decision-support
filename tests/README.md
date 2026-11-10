# tests

Fast tests (unmarked, `tests/test_*.py`, one module per capability), `integration/`
(PostgreSQL test database, opt-in live Odoo) and `e2e/` (real browser). Shared fixtures
are in `conftest.py`; shared non-fixture code is in [helpers/](helpers/__init__.py), and
test modules import shared code only from there.

Markers, commands, CI scope and which file covers which capability:
[docs/TESTING.md](../docs/TESTING.md). Services for integration and e2e runs:
[docs/RUNBOOK.md §6](../docs/RUNBOOK.md#6-database-integration-tests).
Package boundaries are themselves tested in [test_architecture.py](test_architecture.py).
