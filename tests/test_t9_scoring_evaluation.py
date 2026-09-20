"""Deterministic tests for the isolated T9 scoring evaluation."""

import ast
from dataclasses import fields
from decimal import Decimal
from pathlib import Path

import pytest

from decision_core import DecisionResult
from tools.t9_scoring_evaluation import (
    MINIMUM_HISTORY_SAMPLE,
    PROFILE_PROPOSALS,
    CandidateWeights,
    HistoryNormalization,
    HistoryValue,
    MissingHistoryPolicy,
    alternative_set_sensitivity,
    evaluate_scenario,
    history_weight_flip_threshold,
    normalize_history,
    required_scenarios,
    sensitivity_sweep,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _scenario(scenario_id: str):
    return next(item for item in required_scenarios() if item.scenario_id == scenario_id)


def test_candidate_profile_weights_sum_exactly_to_one() -> None:
    assert set(PROFILE_PROPOSALS) == {"cost-focused", "urgent", "risk-averse"}
    for profile in PROFILE_PROPOSALS.values():
        assert (
            profile.candidate.unit_price
            + profile.candidate.lead_time
            + profile.candidate.historical_performance
            == Decimal("1")
        )


def test_candidate_weights_reject_non_unit_sum() -> None:
    with pytest.raises(ValueError, match="sum exactly"):
        CandidateWeights(Decimal("0.5"), Decimal("0.3"), Decimal("0.1"))


@pytest.mark.parametrize(
    ("normalization", "expected"),
    [
        (
            HistoryNormalization.ABSOLUTE,
            (Decimal("0"), Decimal("0.3333"), Decimal("1")),
        ),
        (
            HistoryNormalization.MIN_MAX,
            (Decimal("0"), Decimal("0.3333"), Decimal("1")),
        ),
        (
            HistoryNormalization.BANDS,
            (Decimal("0"), Decimal("0"), Decimal("1")),
        ),
    ],
)
def test_normalization_endpoints_and_controlled_value(
    normalization: HistoryNormalization, expected: tuple[Decimal, ...]
) -> None:
    assert (
        normalize_history((Decimal("0"), Decimal("33.33"), Decimal("100")), normalization)
        == expected
    )


def test_equal_value_and_small_difference_behaviour_is_explicit() -> None:
    equal = (Decimal("80"), Decimal("80"), Decimal("80"))
    close = (Decimal("79.99"), Decimal("80.00"), Decimal("80.01"))

    assert normalize_history(equal, HistoryNormalization.ABSOLUTE) == (
        Decimal("0.8"),
        Decimal("0.8"),
        Decimal("0.8"),
    )
    assert normalize_history(equal, HistoryNormalization.MIN_MAX) == (
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    )
    assert normalize_history(close, HistoryNormalization.MIN_MAX) == (
        Decimal("0"),
        Decimal("0.5"),
        Decimal("1"),
    )
    assert normalize_history(close, HistoryNormalization.BANDS) == (
        Decimal("0.75"),
        Decimal("0.75"),
        Decimal("0.75"),
    )


def test_withheld_history_is_not_zero_and_minimum_three_is_usable() -> None:
    for sample_size in range(MINIMUM_HISTORY_SAMPLE):
        history = HistoryValue("A", None, sample_size)
        assert not history.usable
        assert history.value is None
    assert HistoryValue("A", Decimal("0"), 3).usable
    with pytest.raises(ValueError, match="must be withheld"):
        HistoryValue("A", Decimal("0"), 2)


def test_complete_case_policy_preserves_baseline_if_any_eligible_history_is_missing() -> None:
    result = evaluate_scenario(_scenario("S07"))

    assert not result.history_criterion_active
    assert result.candidate_ranking == result.baseline_ranking
    assert (
        tuple((item.offer_id, item.total_score) for item in result.candidate_ranked_offers)
        == result.baseline_scores
    )
    assert all(len(item.contributions) == 2 for item in result.candidate_ranked_offers)


def test_missing_history_alternatives_have_distinct_reproducible_effects() -> None:
    scenario = _scenario("S07")
    results = {
        policy: evaluate_scenario(scenario, missing_history_policy=policy)
        for policy in MissingHistoryPolicy
    }

    assert not results[MissingHistoryPolicy.COMPLETE_CASE].history_criterion_active
    assert results[MissingHistoryPolicy.RENORMALIZE_AVAILABLE].history_criterion_active
    assert results[MissingHistoryPolicy.NEUTRAL].history_criterion_active
    assert results[MissingHistoryPolicy.CONSERVATIVE].history_criterion_active
    assert results[MissingHistoryPolicy.EXCLUDE].policy_excluded_offer_ids == ("B",)
    assert "B" not in results[MissingHistoryPolicy.EXCLUDE].candidate_ranking
    assert results[MissingHistoryPolicy.NEUTRAL].candidate_ranking == ("A", "B", "C")
    assert results[MissingHistoryPolicy.CONSERVATIVE].candidate_ranking == ("A", "C", "B")
    assert results[MissingHistoryPolicy.RENORMALIZE_AVAILABLE].candidate_ranking == (
        "A",
        "C",
        "B",
    )

    missing_renormalized = next(
        item
        for item in results[MissingHistoryPolicy.RENORMALIZE_AVAILABLE].candidate_ranked_offers
        if item.offer_id == "B"
    )
    history_contribution = missing_renormalized.contributions[-1]
    assert history_contribution.raw_value is None
    assert history_contribution.normalized_value is None
    assert history_contribution.weight == Decimal("0")


def test_all_missing_history_falls_back_to_unchanged_baseline() -> None:
    result = evaluate_scenario(_scenario("S08"))
    assert not result.history_criterion_active
    assert result.candidate_ranking == result.baseline_ranking
    assert not result.ranking_changed


def test_moq_constraint_runs_before_history_and_excellent_history_cannot_rescue_offer() -> None:
    for normalization in HistoryNormalization:
        for policy in MissingHistoryPolicy:
            result = evaluate_scenario(
                _scenario("S11"),
                normalization=normalization,
                missing_history_policy=policy,
            )
            assert result.moq_excluded_offer_ids == ("C",)
            assert "C" not in result.candidate_ranking


def test_required_scenario_matrix_is_complete_and_deterministic() -> None:
    scenarios = required_scenarios()
    assert tuple(item.scenario_id for item in scenarios) == tuple(
        f"S{index:02d}" for index in range(1, 16)
    )
    first = tuple(evaluate_scenario(item) for item in scenarios)
    second = tuple(evaluate_scenario(item) for item in scenarios)
    assert first == second


def test_risk_averse_candidate_can_prefer_more_reliable_expensive_supplier() -> None:
    result = evaluate_scenario(_scenario("S04"))
    assert result.baseline_ranking[0] == "A"
    assert result.candidate_ranking[0] == "B"
    assert result.ranking_changed


def test_ties_use_offer_id_ascending_after_score() -> None:
    result = evaluate_scenario(_scenario("S14"))
    assert result.baseline_ranking == ("A", "B", "C")
    assert result.candidate_ranking == ("A", "B", "C")


def test_history_weight_sweep_and_exact_flip_threshold() -> None:
    scenario = _scenario("S02")
    results = sensitivity_sweep(
        scenario,
        (Decimal("0"), Decimal("0.50"), Decimal("0.80")),
    )
    assert [result.candidate_ranking[0] for result in results] == ["A", "A", "C"]

    threshold = history_weight_flip_threshold(
        Decimal("1"), Decimal("0.5"), Decimal("0.4"), Decimal("0.8")
    )
    assert threshold == Decimal("0.5555555555555555555555555556")


def test_min_max_normalization_is_alternative_set_sensitive() -> None:
    scenario = _scenario("S12")
    without_third = type(scenario)(
        scenario_id=scenario.scenario_id,
        description=scenario.description,
        profile_name=scenario.profile_name,
        requirement=scenario.requirement,
        offers=scenario.offers[:2],
        history=scenario.history[:2],
    )
    with_third_values = {
        item.offer_id: item.contributions[-1].normalized_value
        for item in evaluate_scenario(
            scenario, normalization=HistoryNormalization.MIN_MAX
        ).candidate_ranked_offers
    }
    without_third_values = {
        item.offer_id: item.contributions[-1].normalized_value
        for item in evaluate_scenario(
            without_third, normalization=HistoryNormalization.MIN_MAX
        ).candidate_ranked_offers
    }

    assert without_third_values == {"A": Decimal("0"), "B": Decimal("1")}
    assert with_third_values["A"] == Decimal("0.875")
    assert with_third_values["B"] == Decimal("1")

    direct_without, direct_with, minmax_without, minmax_with = alternative_set_sensitivity()
    assert (
        direct_without.candidate_ranking[:2]
        == direct_with.candidate_ranking[:2]
        == (
            "A",
            "B",
        )
    )
    assert minmax_without.candidate_ranking[:2] == ("B", "A")
    assert minmax_with.candidate_ranking[:2] == ("A", "B")


def test_runtime_packages_do_not_import_t9_analysis_and_result_contract_is_unchanged() -> None:
    assert tuple(field.name for field in fields(DecisionResult)) == (
        "requirement",
        "profile",
        "ranked_offers",
        "excluded_offers",
    )
    for package in ("application", "backend", "decision_core", "odoo_adapter"):
        for path in (PROJECT_ROOT / package).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            imported.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            assert all(not name.startswith("tools.t9_scoring_evaluation") for name in imported)
