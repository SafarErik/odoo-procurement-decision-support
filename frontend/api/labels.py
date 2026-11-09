"""Readable names for Odoo identities the API returns (``odoo:<model>:<id>``)."""

from frontend.i18n import tr


def supplier_label(identity: str, lang: str = "en", names: dict | None = None) -> str:
    """Odoo display name when stored, otherwise a readable label for the identity."""
    if names and names.get(identity):
        return names[identity]
    if identity.startswith("odoo:res.partner:"):
        return tr("supplier_n", lang, n=identity.removeprefix("odoo:res.partner:"))
    return identity


def product_label(identity: str, lang: str = "en", names: dict | None = None) -> str:
    """Odoo display name when stored, otherwise a readable label for the identity."""
    if names and names.get(identity):
        return names[identity]
    if identity.startswith("odoo:product.product:"):
        return tr("product_n", lang, n=identity.removeprefix("odoo:product.product:"))
    return identity
