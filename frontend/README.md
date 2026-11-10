# frontend

The Reflex web UI for the buyer: Home, Cases, the four-step New procurement wizard and
the case page (tabs Overview, Suppliers, Plans, What if…?, Decision & PDF, and the Audit view). Hungarian by
default with an English switch. It reaches the system only through the backend HTTP
API and keeps the service token server-side.

## Entry points

| Path | Content |
| --- | --- |
| [app.py](app.py), [rxconfig.py](rxconfig.py), [config.py](config.py) | App root and page registration, Reflex build settings, backend URL and token |
| [api/](api/__init__.py) | The one HTTP-client layer: [http.py](api/http.py) (URL, token, timeouts, error texts), one module per backend resource, [case_view.py](api/case_view.py) (stored case → display rows) |
| [i18n/](i18n/__init__.py) | Every UI text in [texts.py](i18n/texts.py) (English key → HU, EN); formatting in [format.py](i18n/format.py) |
| [planning/](planning/__init__.py) | One module per page or tab; `PlanningState` in [state.py](planning/state.py) composed from `state_*.py` mixins; wizard rules in [creation_rules.py](planning/creation_rules.py) |
| [theme.py](theme.py), [ui.py](ui.py), [workspace.py](workspace.py), [components/](components/__init__.py) | Visual tokens, shared building blocks, the page frame, wizard step bar |

Supplier KPI labels and tree-path sentences come from the API
(`application/supplier_overview.py`), not from `i18n/`. Design intent and token names:
[DESIGN.md](../DESIGN.md). Running the UI: [docs/RUNBOOK.md §4](../docs/RUNBOOK.md#4-planning-database-api-and-ui).

## Imports

- May import: Reflex, httpx, pydantic.
- Must not import: `backend`, `application`, `odoo_adapter`, `persistence`,
  `decision_core`, `optimization_adapter`, `supplier_evaluation`, `tools`; no Odoo,
  database, ML or solver logic.

## Tests

`tests/test_frontend_*.py`, `tests/test_creation_review.py`, `tests/test_guided_workspace.py`,
`tests/test_plan_comparison.py`, `tests/test_workspace_navigation.py` and others without a
browser; browser flows in `tests/e2e/`. Patching helpers: `tests/helpers/frontend_patching.py`.
See [docs/TESTING.md](../docs/TESTING.md).
