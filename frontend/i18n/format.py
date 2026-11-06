"""Locale-aware formatting of numbers, money, dates and units; no Reflex imports."""

from datetime import date, datetime
from decimal import Decimal

LANGUAGES = ("hu", "en")
DEFAULT_LANGUAGE = "hu"

_MONTHS = {
    "hu": (
        "jan.",
        "febr.",
        "márc.",
        "ápr.",
        "máj.",
        "jún.",
        "júl.",
        "aug.",
        "szept.",
        "okt.",
        "nov.",
        "dec.",
    ),
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
}
_SYMBOLS = {"HUF": "Ft", "EUR": "€", "USD": "$", "GBP": "£"}
# Odoo unit names the buyer reads every day; anything else is shown as Odoo names it.
_UNITS = {
    "Units": ("db", "pcs"),
    "Unit": ("db", "pcs"),
    "piece": ("db", "pcs"),
    "kg": ("kg", "kg"),
}


def language(value) -> str:
    return value if value in LANGUAGES else DEFAULT_LANGUAGE


def _group(text: str, lang: str) -> str:
    sign = "-" if text.startswith("-") else ""
    whole, _, fraction = text.lstrip("+-").partition(".")
    separator = " " if lang == "hu" else ","
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    grouped = separator.join([whole, *groups])
    if fraction:
        grouped += ("," if lang == "hu" else ".") + fraction
    return sign + grouped


def number(value, lang: str, digits: int | None = None) -> str:
    """Grouped number; ``digits`` rounds for display, otherwise stored digits are kept."""
    amount = Decimal(str(value))
    text = f"{amount:.{digits}f}" if digits is not None else f"{amount:f}"
    return _group(text, language(lang))


def money(value, currency: str, lang: str, *, signed: bool = False) -> str:
    """Amount with at least two decimals and never fewer than the stored digits."""
    lang = language(lang)
    amount = Decimal(str(value))
    # Pad to two decimals but never round stored digits (no quantize: it fails on long values).
    # Read the stored exponent: normalize() rounds to the context precision first.
    exponent = amount.as_tuple().exponent
    text = f"{amount:.2f}" if isinstance(exponent, int) and exponent >= -2 else f"{amount:f}"
    grouped = _group(text, lang)
    sign = ""
    if signed and amount > 0:
        sign = "+"
    if grouped.startswith("-"):
        sign, grouped = "−", grouped[1:]
    symbol = _SYMBOLS.get(currency, currency)
    if lang == "en":
        # English: €/$/£ before the amount, otherwise the ISO code after it (1,545.70 HUF).
        if symbol in ("€", "$", "£"):
            return f"{sign}{symbol}{grouped}"
        return f"{sign}{grouped} {currency}"
    return f"{sign}{grouped} {symbol}"


def percent(ratio, lang: str, digits: int = 1) -> str:
    text = number(Decimal(str(ratio)) * 100, lang, digits)
    return text + (" %" if language(lang) == "hu" else "%")


def day(value, lang: str) -> str:
    """ISO date or datetime as a buyer-readable date."""
    parsed = value if isinstance(value, date) else datetime.fromisoformat(str(value)[:10]).date()
    month = _MONTHS[language(lang)][parsed.month - 1]
    if language(lang) == "hu":
        return f"{parsed.year}. {month} {parsed.day}."
    return f"{parsed.day} {month} {parsed.year}"


def moment(value, lang: str) -> str:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return f"{day(parsed.date(), lang)} {parsed.hour:02d}:{parsed.minute:02d} UTC"


def unit(name: str, lang: str) -> str:
    pair = _UNITS.get(name)
    return name if pair is None else pair[0 if language(lang) == "hu" else 1]
