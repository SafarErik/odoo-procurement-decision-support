"""Readable HU/EN supplier texts derived from stored values only."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from application.supplier_overview import (
    class_label,
    class_name,
    format_number,
    leaf_text,
    money_text,
    path_steps,
)
from supplier_evaluation.contracts import HISTORY_SOURCE, SYNTHETIC, PathStep


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


def test_path_falls_back_to_stored_values_when_rounding_cannot_separate_them():
    step = PathStep(0, "mean_lateness_days", 0.5000000001, ">", 0.5)
    (en,) = path_steps(SimpleNamespace(path=(step,)), "en")
    (hu,) = path_steps(SimpleNamespace(path=(step,)), "hu")
    assert en["text"] == "Average lateness: 0.5000000001, above 0.5."
    assert hu["text"] == "Átlagos késés: 0,5000000001 – 0,5 felett."


@pytest.mark.parametrize(
    ("source", "names", "hu", "en"),
    [
        (HISTORY_SOURCE, ("regular", "problematic"), "problémás", "problematic"),
        (SYNTHETIC, ("schedule_regular", "schedule_watch"), "figyelendő", "watch"),
    ],
)
def test_class_and_leaf_text_follow_the_assessment_source(source, names, hu, en):
    assessment = SimpleNamespace(
        snapshot=SimpleNamespace(source_type=source),
        predicted_class=1,
        leaf_counts=(3, 7),
        score=Decimal("0.7"),
    )
    assert class_name(assessment) == names[1]
    assert (class_label(assessment, "hu"), class_label(assessment, "en")) == (hu, en)
    assert class_name(SimpleNamespace(snapshot=assessment.snapshot, predicted_class=0)) == names[0]
    if source == SYNTHETIC:
        assert "7 of 10 were labelled schedule_watch" in leaf_text(assessment, "en")
        assert "generált tanítópéldák" in leaf_text(assessment, "hu")
    else:
        assert "7 of 10 became problematic" in leaf_text(assessment, "en")
        assert "10 esetből 7 lett problémás" in leaf_text(assessment, "hu")
