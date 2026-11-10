# persistence

PostgreSQL adapters for the application's repository ports. Every stored case,
decision and PDF is immutable: database triggers reject UPDATE and DELETE.

## Entry points

- [planning_cases.py](planning_cases.py) — case and scenario repositories and the
  per-use-case transaction (unit of work).
- [planning_decisions.py](planning_decisions.py) — the one final decision per base case.
- [planning_documents.py](planning_documents.py) — approved PDF bytes per case, language
  and kind.
- [schema.py](schema.py) — SQLAlchemy table mapping, used by the repositories and by
  Alembic in [../migrations/](../migrations/).
- [session.py](session.py) — engine and session construction; never changes the schema.

Tables: [docs/ARCHITECTURE.md §5](../docs/ARCHITECTURE.md#5-persistence). Starting and
migrating the database: [docs/RUNBOOK.md §4](../docs/RUNBOOK.md#4-planning-database-api-and-ui).

## Imports

- May import: `application` (contracts, errors, serialization), SQLAlchemy.
- Must not import: `backend`, `frontend`, `odoo_adapter`. The application never imports
  this package. Enforced by [tests/test_architecture.py](../tests/test_architecture.py).

## Tests

`tests/integration/test_planning_postgres.py`, `test_decisions_postgres.py`,
`test_documents_postgres.py`, `test_documents_migration_postgres.py`,
`test_saved_library_postgres.py` (disposable test database only); fast tests use
`tests/helpers/in_memory_uow.py`. See [docs/TESTING.md](../docs/TESTING.md).
