"""How the approved PDFs write numbers, dates, money and recorded values.

Hungarian output uses a decimal comma and a space as thousands separator ("1 250",
"92,5%", "2026.11.07."); English uses the dot and ISO dates. One ``Formatter`` is made
per rendered document, so the language, currency, unit and saved display names are
fixed for the whole document.
"""

from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction

from application.supplier_overview import money_text, saved_labels
from document_adapter.texts import RECORDED_TEXT_HU, SOLVER_OUTCOME_HU, TEXT

# Odoo unit names as the buyer reads them, (Hungarian, English). The frontend keeps its
# own copy for the screens (frontend/i18n/format.py ``_UNITS``).
UNITS = {
    "Units": ("db", "pcs"),
    "Unit": ("db", "pcs"),
    "piece": ("db", "pcs"),
    "kg": ("kg", "kg"),
}


class Formatter:
    """Value-to-text rules for one document of one approved content in one language."""

    def __init__(self, content: dict, language: str):
        snapshot = content["planning_snapshot"]
        demand = snapshot["request"]["requirement"]
        self.language = language
        self.t = TEXT[language]
        self.names = saved_labels(snapshot)
        self.currency = demand["currency"]
        unit = self.short(demand["quantity_unit"])
        self.unit = UNITS.get(unit, (unit, unit))[language != "hu"]

    def _local(self, text: str) -> str:
        """Hungarian decimal comma; English text unchanged."""
        return text.replace(".", ",") if self.language == "hu" else text

    def short(self, identity: str) -> str:
        """The saved Odoo display name of an identity, or the identity itself."""
        return self.names.get(identity, identity)

    def number(self, value: int) -> str:
        text = f"{value:,}"
        return text.replace(",", " ") if self.language == "hu" else text

    def money(self, value) -> str:
        return f"{money_text(Decimal(value), self.language)} {self.currency}"

    def percent(self, value: Fraction) -> str:
        return self._local(f"{float(value) * 100:.1f}%")

    def decimal(self, value) -> str:
        return self._local(str(value))

    def ratio(self, value: Fraction) -> str:
        return self._local(f"{float(value):.4f}")

    def day(self, value: str) -> str:
        parsed = date.fromisoformat(value)
        return parsed.strftime("%Y.%m.%d.") if self.language == "hu" else parsed.isoformat()

    def moment(self, value: str) -> str:
        stamp = "%Y.%m.%d. %H:%M" if self.language == "hu" else "%Y-%m-%d %H:%M"
        return datetime.fromisoformat(value).strftime(stamp) + " UTC"

    def quantity(self, value: int) -> str:
        return f"{self.number(value)} {self.unit}"

    def quantity_range(self, value: dict) -> str:
        return f"{self.number(value['minimum'])}–{self.number(value['maximum'])} {self.unit}"

    def recorded(self, value: str) -> str:
        """A sentence stored verbatim in English: Hungarian shows a translation and quotes it."""
        if self.language == "hu" and value in RECORDED_TEXT_HU:
            return f"{RECORDED_TEXT_HU[value]} {self.t['original_quoted'].format(text=value)}"
        return f"{value} {self.t['original_text']}"

    def outcome(self, value: str) -> str:
        """A solver status code, with its Hungarian name in front when there is one."""
        label = SOLVER_OUTCOME_HU.get(value) if self.language == "hu" else None
        return value if label is None else f"{label} ({value})"

    def yes_no(self, value: bool) -> str:
        return self.t["yes"] if value else self.t["no"]
