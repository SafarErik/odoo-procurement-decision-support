"""UI texts (English keys, Hungarian default) and locale-aware formatting; no Reflex imports."""

from frontend.i18n.format import (
    DEFAULT_LANGUAGE,
    LANGUAGES,
    day,
    language,
    moment,
    money,
    number,
    percent,
    unit,
)
from frontend.i18n.texts import TEXT

__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGES",
    "TEXT",
    "day",
    "language",
    "moment",
    "money",
    "number",
    "percent",
    "tr",
    "unit",
]


def tr(key: str, lang: str, **values) -> str:
    hu, en = TEXT[key]
    text = hu if language(lang) == "hu" else en
    return text.format(**values) if values else text
