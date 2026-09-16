# Development guidance

## T0 scope

T0 establishes the local development foundation, a minimal FastAPI health API, a
minimal separate Reflex frontend, Odoo Compose configuration, automated checks,
and an evidence-based Odoo capability spike. It does not implement procurement
decision logic, rankings, constraints, KPIs, persistence schemas, or a final
domain model.

## Architectural boundaries

- Keep the Decision Core independent of Odoo, FastAPI, Reflex, and database frameworks.
- Keep Odoo communication and mapping behind `odoo_adapter/`; never access the Odoo database directly.
- The frontend communicates only with the documented backend HTTP API. It must not access Odoo or a database.
- Keep FastAPI route handlers thin and keep business logic out of Reflex components and route handlers.
- The future application layer orchestrates use cases; it must not own infrastructure-specific logic.
- Do not invent or rely on unvalidated Odoo models, fields, authentication details, or API capabilities.
- Never commit secrets. Keep local values in the ignored `.env` file.

## Language and documentation

Use English for all repository software-engineering artifacts, including source,
tests, logs, UI strings, documentation, branches, and commits. Preserve official
external names where appropriate. Update `README.md`, `docs/IMPLEMENTATION_LOG.md`,
and relevant spike documentation when implementation or verified facts change.
Google Drive thesis documents must not be changed unless the user explicitly asks.

## Commands

After creating and activating a Python 3.11+ virtual environment:

```powershell
python -m pip install -e ".[frontend,dev]"
ruff format --check .
ruff check .
pytest
podman compose --env-file .env -f infra/odoo/compose.yaml config
```

Run the backend with `uvicorn backend.app.main:app --reload` and the frontend
from `frontend/` with `reflex run`.
