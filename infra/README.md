# infra

Local container setup (Podman or Docker Compose) and the two Odoo addons. Nothing here
is imported by the Python runtime.

| Path | Content |
| --- | --- |
| [app/compose.yaml](app/compose.yaml) | Planning PostgreSQL (named volume), started by `tools.dev db-up` |
| [odoo/compose.yaml](odoo/compose.yaml) | Odoo 19 and its own database, started by `tools.dev odoo-up` |
| [persistence/compose.test.yaml](persistence/compose.test.yaml) | Disposable test PostgreSQL for integration tests |
| [odoo/addons/t7s_inventory_history_projection/](odoo/addons/t7s_inventory_history_projection/__manifest__.py) | Bounded, company-scoped, read-only purchase-history export (and an older, unused projection method); why the name is historical: [odoo_adapter/README.md](../odoo_adapter/README.md) |
| [odoo/addons/pdss_quotation_reader/](odoo/addons/pdss_quotation_reader/__manifest__.py) | Read-only access group for the quotation integration user |

Commands, environment variables and the manual Odoo setup:
[docs/RUNBOOK.md](../docs/RUNBOOK.md). The addons' policies are tested in
`tests/test_odoo_inventory_projection_policy.py`, `tests/test_odoo_purchase_history.py`
and `tests/test_architecture.py`.
