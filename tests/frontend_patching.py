"""Patch HTTP-client names where the planning state mixins resolve them."""

MODULES = {
    "submit_planning_request": ("frontend.planning.state_base",),
    "fetch_planning_case": ("frontend.planning.state_case", "frontend.planning.state_decision"),
    "fetch_planning_pdf": ("frontend.planning.state_decision",),
    "fetch_quotation_groups": ("frontend.planning.state_creation",),
    "fetch_odoo_history": ("frontend.planning.state_creation",),
    "fetch_supplier_overview": ("frontend.planning.state_case",),
    "fetch_library": ("frontend.planning.state_library",),
}


def patch_client(monkeypatch, name, replacement):
    for module in MODULES[name]:
        monkeypatch.setattr(f"{module}.{name}", replacement)
