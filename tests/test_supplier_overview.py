"""Readable HU/EN supplier texts derived from stored values only."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from application.supplier_overview import format_number, money_text, path_steps
from supplier_evaluation.contracts import PathStep


def test_numbers_use_the_language_decimal_separator_and_grouping():
    assert format_number(0.8234, "pct", "hu") == "82,3%"
    assert format_number(0.8234, "pct", "en") == "82.3%"
    assert format_number(3.25, "days", "hu", 2) == "3,25 nap"
    assert format_number(12, "int", "en") == "12"
    assert money_text(Decimal("1234.5"), "hu") == "1 234,50"
    assert money_text(Decimal("1234.5"), "en") == "1,234.50"
    assert money_text(Decimal("10.125"), "en") == "10.125"  # stored digits are never rounded
    with pytest.raises(ValueError):
        format_number(1, "pct", "de")


def test_path_adds_decimals_until_the_threshold_side_is_visible():
    steps = (
        PathStep(0, "lateness_spread_days", 0.68, "<=", 0.72),
        PathStep(1, "order_count", 6.0, "<=", 6.5),
        PathStep(2, "on_time_rate", 0.9, ">", 0.75),
    )
    hu = path_steps(SimpleNamespace(path=steps), "hu")
    en = path_steps(SimpleNamespace(path=steps), "en")
    assert hu[0]["text"] == "Késés szórása: 0,68 nap – legfeljebb 0,72 nap."
    assert hu[1]["text"] == "Lezárt rendelési sorok száma: 6,0 – legfeljebb 6,5."
    assert hu[2]["text"] == "Határidőre teljesített szállítások aránya: 90,0% – 75,0% felett."
    assert en[0]["text"] == "Lateness spread: 0.68 days, at most 0.72 days."
    assert en[2]["text"] == "On-time delivery rate: 90.0%, above 75.0%."
    assert [s["value"] for s in hu] == [s.value_float32 for s in steps]
