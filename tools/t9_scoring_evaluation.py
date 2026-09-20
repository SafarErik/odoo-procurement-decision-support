"""Isolated, deterministic T9 evaluation of historical-performance scoring policies.

This module is analysis tooling. Runtime packages must not import it, and none of
the policies represented here are active Decision Core behaviour.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, is_dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import Any

from decision_core import PurchaseRequirement, StrategicProfile, SupplierOffer, evaluate_decision
from decision_core.constraints import evaluate_hard_constraints
from decision_core.models import CriterionDirection
from decision_core.normalization import normalize_values

HISTORY_CRITERION = "delivery_schedule_adherence"
MINIMUM_HISTORY_SAMPLE = 3
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


class HistoryNormalization(StrEnum):
    """Historical-performance normalization alternatives considered by T9."""

    ABSOLUTE = "absolute_percentage"
    MIN_MAX = "comparison_set_min_max"
    BANDS = "policy_bands"


class MissingHistoryPolicy(StrEnum):
    """Missing-history alternatives considered by T9."""

    COMPLETE_CASE = "complete_case_activation"
    RENORMALIZE_AVAILABLE = "per_offer_weight_renormalization"
    NEUTRAL = "neutral_imputation"
    CONSERVATIVE = "conservative_imputation"
    EXCLUDE = "exclude_missing_history"


@dataclass(frozen=True, slots=True)
class HistoryValue:
    """Analysis-only value with the accepted T8 availability threshold."""

    offer_id: str
    value: Decimal | None
    sample_size: int

    def __post_init__(self) -> None:
        if not self.offer_id.strip():
            raise ValueError("offer_id must not be empty")
        if isinstance(self.sample_size, bool) or self.sample_size < 0:
            raise ValueError("sample_size must be a non-negative integer")
        if self.value is not None:
            if not self.value.is_finite() or not ZERO <= self.value <= HUNDRED:
                raise ValueError("history value must be a finite percentage from 0 to 100")
            if self.sample_size < MINIMUM_HISTORY_SAMPLE:
                raise ValueError("history below sample size 3 must be withheld, not scored")

    @property
    def usable(self) -> bool:
        return self.value is not None and self.sample_size >= MINIMUM_HISTORY_SAMPLE


@dataclass(frozen=True, slots=True)
class CandidateWeights:
    """Analysis-only three-criterion weights."""

    unit_price: Decimal
    lead_time: Decimal
    historical_performance: Decimal

    def __post_init__(self) -> None:
        values = (self.unit_price, self.lead_time, self.historical_performance)
        if any(not value.is_finite() or value < ZERO for value in values):
            raise ValueError("candidate weights must be finite and non-negative")
        if sum(values, start=ZERO) != ONE:
            raise ValueError("candidate weights must sum exactly to 1")


@dataclass(frozen=True, slots=True)
class ProfileProposal:
    """A baseline comparator and a PoC three-criterion policy candidate."""

    name: str
    baseline_unit_price: Decimal
    baseline_lead_time: Decimal
    candidate: CandidateWeights

    def baseline_profile(self) -> StrategicProfile:
        return StrategicProfile(
            name=f"{self.name}-baseline",
            unit_price_weight=self.baseline_unit_price,
            lead_time_weight=self.baseline_lead_time,
        )


PROFILE_PROPOSALS = {
    "cost-focused": ProfileProposal(
        name="cost-focused",
        baseline_unit_price=Decimal("0.70"),
        baseline_lead_time=Decimal("0.30"),
        candidate=CandidateWeights(Decimal("0.60"), Decimal("0.25"), Decimal("0.15")),
    ),
    "urgent": ProfileProposal(
        name="urgent",
        baseline_unit_price=Decimal("0.30"),
        baseline_lead_time=Decimal("0.70"),
        candidate=CandidateWeights(Decimal("0.25"), Decimal("0.60"), Decimal("0.15")),
    ),
    "risk-averse": ProfileProposal(
        name="risk-averse",
        baseline_unit_price=Decimal("0.50"),
        baseline_lead_time=Decimal("0.50"),
        candidate=CandidateWeights(Decimal("0.30"), Decimal("0.30"), Decimal("0.40")),
    ),
}


@dataclass(frozen=True, slots=True)
class EvaluationScenario:
    """One deterministic scenario independent of Odoo or external services."""

    scenario_id: str
    description: str
    profile_name: str
    requirement: PurchaseRequirement
    offers: tuple[SupplierOffer, ...]
    history: tuple[HistoryValue, ...]


@dataclass(frozen=True, slots=True)
class EvaluationContribution:
    """Analysis trace for one criterion."""

    criterion: str
    raw_value: Decimal | None
    normalized_value: Decimal | None
    weight: Decimal
    weighted_contribution: Decimal
    note: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationRankedOffer:
    """Analysis-only ranked offer and complete contribution trace."""

    rank: int
    offer_id: str
    total_score: Decimal
    contributions: tuple[EvaluationContribution, ...]


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Baseline and candidate results for one scenario/policy combination."""

    scenario_id: str
    normalization: HistoryNormalization
    missing_history_policy: MissingHistoryPolicy
    history_criterion_active: bool
    baseline_ranking: tuple[str, ...]
    candidate_ranking: tuple[str, ...]
    baseline_scores: tuple[tuple[str, Decimal], ...]
    candidate_ranked_offers: tuple[EvaluationRankedOffer, ...]
    moq_excluded_offer_ids: tuple[str, ...]
    policy_excluded_offer_ids: tuple[str, ...]
    ranking_changed: bool


def normalize_history(
    values: tuple[Decimal, ...], normalization: HistoryNormalization
) -> tuple[Decimal, ...]:
    """Normalize usable percentages using one of the three T9 alternatives."""

    if not values:
        return ()
    if any(not value.is_finite() or not ZERO <= value <= HUNDRED for value in values):
        raise ValueError("historical percentages must be finite and between 0 and 100")
    if normalization is HistoryNormalization.ABSOLUTE:
        return tuple(value / HUNDRED for value in values)
    if normalization is HistoryNormalization.MIN_MAX:
        return normalize_values(values, CriterionDirection.BENEFIT)
    if normalization is HistoryNormalization.BANDS:
        return tuple(_band_value(value) for value in values)
    raise ValueError(f"unsupported normalization: {normalization!r}")


def _band_value(value: Decimal) -> Decimal:
    if value < Decimal("50"):
        return ZERO
    if value < Decimal("75"):
        return Decimal("0.50")
    if value < Decimal("90"):
        return Decimal("0.75")
    return ONE


def evaluate_scenario(
    scenario: EvaluationScenario,
    *,
    normalization: HistoryNormalization = HistoryNormalization.ABSOLUTE,
    missing_history_policy: MissingHistoryPolicy = MissingHistoryPolicy.COMPLETE_CASE,
    profile: ProfileProposal | None = None,
) -> EvaluationResult:
    """Compare a candidate policy with the unchanged two-criterion runtime baseline."""

    selected_profile = profile or PROFILE_PROPOSALS[scenario.profile_name]
    history_by_offer = _history_map(scenario)

    baseline = evaluate_decision(
        scenario.requirement,
        scenario.offers,
        selected_profile.baseline_profile(),
    )
    baseline_ranking = tuple(item.offer.offer_id for item in baseline.ranked_offers)
    baseline_scores = tuple(
        (item.offer.offer_id, item.total_score) for item in baseline.ranked_offers
    )

    # This explicit partition is deliberately first: no history policy can rescue
    # or score an offer that fails the existing MOQ hard constraint.
    constraint_result = evaluate_hard_constraints(
        scenario.requirement, tuple(sorted(scenario.offers, key=lambda item: item.offer_id))
    )
    eligible = constraint_result.eligible_offers
    moq_excluded = tuple(item.offer.offer_id for item in constraint_result.excluded_offers)
    all_usable = bool(eligible) and all(history_by_offer[item.offer_id].usable for item in eligible)

    policy_excluded: tuple[str, ...] = ()
    scored_offers = eligible
    if missing_history_policy is MissingHistoryPolicy.EXCLUDE:
        policy_excluded = tuple(
            item.offer_id for item in eligible if not history_by_offer[item.offer_id].usable
        )
        scored_offers = tuple(item for item in eligible if history_by_offer[item.offer_id].usable)

    history_active = not (
        missing_history_policy is MissingHistoryPolicy.COMPLETE_CASE and not all_usable
    )
    ranked = _score_candidate(
        scored_offers,
        history_by_offer,
        selected_profile,
        normalization,
        missing_history_policy,
        history_active,
    )
    candidate_ranking = tuple(item.offer_id for item in ranked)
    return EvaluationResult(
        scenario_id=scenario.scenario_id,
        normalization=normalization,
        missing_history_policy=missing_history_policy,
        history_criterion_active=history_active,
        baseline_ranking=baseline_ranking,
        candidate_ranking=candidate_ranking,
        baseline_scores=baseline_scores,
        candidate_ranked_offers=ranked,
        moq_excluded_offer_ids=moq_excluded,
        policy_excluded_offer_ids=policy_excluded,
        ranking_changed=candidate_ranking != baseline_ranking,
    )


def _history_map(scenario: EvaluationScenario) -> dict[str, HistoryValue]:
    provided = {item.offer_id: item for item in scenario.history}
    if len(provided) != len(scenario.history):
        raise ValueError("history offer identifiers must be unique")
    known_ids = {offer.offer_id for offer in scenario.offers}
    unknown = sorted(set(provided) - known_ids)
    if unknown:
        raise ValueError(f"history references unknown offers: {', '.join(unknown)}")
    return {
        offer.offer_id: provided.get(offer.offer_id, HistoryValue(offer.offer_id, None, 0))
        for offer in scenario.offers
    }


def _score_candidate(
    offers: tuple[SupplierOffer, ...],
    history_by_offer: dict[str, HistoryValue],
    profile: ProfileProposal,
    normalization: HistoryNormalization,
    missing_history_policy: MissingHistoryPolicy,
    history_active: bool,
) -> tuple[EvaluationRankedOffer, ...]:
    if not offers:
        return ()

    price_normalized = normalize_values(
        tuple(item.unit_price for item in offers), CriterionDirection.COST
    )
    lead_normalized = normalize_values(
        tuple(item.lead_time_days for item in offers), CriterionDirection.COST
    )
    usable_values = tuple(
        history_by_offer[item.offer_id].value
        for item in offers
        if history_by_offer[item.offer_id].usable
    )
    normalized_usable = normalize_history(
        tuple(value for value in usable_values if value is not None), normalization
    )
    normalized_history = dict(
        zip(
            (item.offer_id for item in offers if history_by_offer[item.offer_id].usable),
            normalized_usable,
            strict=True,
        )
    )

    scored: list[tuple[str, Decimal, tuple[EvaluationContribution, ...]]] = []
    for index, offer in enumerate(offers):
        history = history_by_offer[offer.offer_id]
        price_weight, lead_weight, history_weight = _effective_weights(
            profile, missing_history_policy, history, history_active
        )
        contributions = [
            EvaluationContribution(
                criterion="unit_price",
                raw_value=offer.unit_price,
                normalized_value=price_normalized[index],
                weight=price_weight,
                weighted_contribution=price_normalized[index] * price_weight,
            ),
            EvaluationContribution(
                criterion="lead_time_days",
                raw_value=offer.lead_time_days,
                normalized_value=lead_normalized[index],
                weight=lead_weight,
                weighted_contribution=lead_normalized[index] * lead_weight,
            ),
        ]
        if history_active:
            normalized_value, note = _history_for_offer(
                history, normalized_history, missing_history_policy
            )
            contributions.append(
                EvaluationContribution(
                    criterion=HISTORY_CRITERION,
                    raw_value=history.value,
                    normalized_value=normalized_value,
                    weight=history_weight,
                    weighted_contribution=(normalized_value or ZERO) * history_weight,
                    note=note,
                )
            )
        contribution_tuple = tuple(contributions)
        score = sum((item.weighted_contribution for item in contribution_tuple), start=ZERO)
        scored.append((offer.offer_id, score, contribution_tuple))

    scored.sort(key=lambda item: (-item[1], item[0]))
    return tuple(
        EvaluationRankedOffer(rank, offer_id, score, contributions)
        for rank, (offer_id, score, contributions) in enumerate(scored, start=1)
    )


def _effective_weights(
    profile: ProfileProposal,
    policy: MissingHistoryPolicy,
    history: HistoryValue,
    history_active: bool,
) -> tuple[Decimal, Decimal, Decimal]:
    if not history_active:
        return profile.baseline_unit_price, profile.baseline_lead_time, ZERO
    if policy is MissingHistoryPolicy.RENORMALIZE_AVAILABLE and not history.usable:
        subtotal = profile.candidate.unit_price + profile.candidate.lead_time
        return (
            profile.candidate.unit_price / subtotal,
            profile.candidate.lead_time / subtotal,
            ZERO,
        )
    return (
        profile.candidate.unit_price,
        profile.candidate.lead_time,
        profile.candidate.historical_performance,
    )


def _history_for_offer(
    history: HistoryValue,
    normalized_history: dict[str, Decimal],
    policy: MissingHistoryPolicy,
) -> tuple[Decimal | None, str | None]:
    if history.usable:
        return normalized_history[history.offer_id], None
    if policy is MissingHistoryPolicy.NEUTRAL:
        return Decimal("0.50"), "missing history imputed as neutral"
    if policy is MissingHistoryPolicy.CONSERVATIVE:
        return ZERO, "missing history imputed as conservative"
    if policy is MissingHistoryPolicy.RENORMALIZE_AVAILABLE:
        return None, "history weight redistributed to this offer's available criteria"
    return None, "history unavailable"


def proposal_for_history_weight(
    profile: ProfileProposal, history_weight: Decimal
) -> ProfileProposal:
    """Allocate the remaining weight in the profile's current price/lead ratio."""

    if not ZERO <= history_weight <= ONE:
        raise ValueError("history weight must be between 0 and 1")
    remaining = ONE - history_weight
    baseline_total = profile.baseline_unit_price + profile.baseline_lead_time
    candidate = CandidateWeights(
        unit_price=remaining * profile.baseline_unit_price / baseline_total,
        lead_time=remaining * profile.baseline_lead_time / baseline_total,
        historical_performance=history_weight,
    )
    return replace(profile, candidate=candidate)


def history_weight_flip_threshold(
    baseline_score_a: Decimal,
    baseline_score_b: Decimal,
    normalized_history_a: Decimal,
    normalized_history_b: Decimal,
) -> Decimal | None:
    """Return the exact ratio-preserving history weight at which A and B tie."""

    baseline_difference = baseline_score_a - baseline_score_b
    history_difference = normalized_history_a - normalized_history_b
    denominator = baseline_difference - history_difference
    if denominator == ZERO:
        return None
    threshold = baseline_difference / denominator
    return threshold if ZERO <= threshold <= ONE else None


def sensitivity_sweep(
    scenario: EvaluationScenario,
    history_weights: tuple[Decimal, ...],
    *,
    normalization: HistoryNormalization = HistoryNormalization.ABSOLUTE,
    missing_history_policy: MissingHistoryPolicy = MissingHistoryPolicy.COMPLETE_CASE,
) -> tuple[EvaluationResult, ...]:
    """Evaluate deterministic ranking changes over supplied history weights."""

    base = PROFILE_PROPOSALS[scenario.profile_name]
    return tuple(
        evaluate_scenario(
            scenario,
            normalization=normalization,
            missing_history_policy=missing_history_policy,
            profile=proposal_for_history_weight(base, weight),
        )
        for weight in history_weights
    )


def required_scenarios() -> tuple[EvaluationScenario, ...]:
    """Return the fixed T9 acceptance scenario matrix."""

    requirement = PurchaseRequirement("T9", Decimal("100"))
    return (
        _scenario(
            "S01",
            "cheapest supplier also has best history",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "5"), "95", 10),
                (_offer("B", "100", "7"), "70", 10),
                (_offer("C", "110", "9"), "50", 10),
            ),
        ),
        _scenario(
            "S02",
            "cheapest supplier has worst history",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "6"), "40", 10),
                (_offer("B", "100", "7"), "80", 10),
                (_offer("C", "110", "8"), "95", 10),
            ),
        ),
        _scenario(
            "S03",
            "fastest supplier has weak history",
            "urgent",
            requirement,
            (
                (_offer("A", "100", "3"), "40", 10),
                (_offer("B", "95", "6"), "90", 10),
                (_offer("C", "90", "9"), "80", 10),
            ),
        ),
        _scenario(
            "S04",
            "risk-averse prefers reliable expensive supplier",
            "risk-averse",
            requirement,
            (
                (_offer("A", "90", "7"), "45", 10),
                (_offer("B", "110", "5"), "100", 10),
                (_offer("C", "120", "10"), "75", 10),
            ),
        ),
        _scenario(
            "S05",
            "all historical values are equal",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "8"), "75", 10),
                (_offer("B", "100", "6"), "75", 10),
                (_offer("C", "110", "4"), "75", 10),
            ),
        ),
        _scenario(
            "S06",
            "only one supplier has usable history",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "8"), "90", 10),
                (_offer("B", "100", "6"), None, 0),
                (_offer("C", "110", "4"), None, 0),
            ),
        ),
        _scenario(
            "S07",
            "one supplier is below sample size three",
            "urgent",
            requirement,
            (
                (_offer("A", "100", "3"), "80", 10),
                (_offer("B", "95", "6.4"), None, 2),
                (_offer("C", "90", "8"), "90", 10),
            ),
        ),
        _scenario(
            "S08",
            "all suppliers have withheld history",
            "risk-averse",
            requirement,
            (
                (_offer("A", "90", "8"), None, 0),
                (_offer("B", "100", "6"), None, 1),
                (_offer("C", "110", "4"), None, 2),
            ),
        ),
        _scenario(
            "S09",
            "small history differences near ranking boundary",
            "cost-focused",
            requirement,
            (
                (_offer("A", "96", "7"), "79.99", 20),
                (_offer("B", "100", "6"), "80.01", 20),
                (_offer("C", "104", "5"), "80.00", 20),
            ),
        ),
        _scenario(
            "S10",
            "extreme history values zero and one hundred",
            "risk-averse",
            requirement,
            (
                (_offer("A", "90", "8"), "0", 10),
                (_offer("B", "100", "6"), "50", 10),
                (_offer("C", "110", "4"), "100", 10),
            ),
        ),
        _scenario(
            "S11",
            "MOQ-ineligible offer has excellent history",
            "risk-averse",
            requirement,
            (
                (_offer("A", "90", "8"), "50", 10),
                (_offer("B", "100", "6"), "70", 10),
                (_offer("C", "80", "2", "150"), "100", 10),
            ),
        ),
        _scenario(
            "S12",
            "third alternative exposes comparison-set sensitivity",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "6"), "70", 10),
                (_offer("B", "100", "5"), "80", 10),
                (_offer("C", "95", "5.5"), "0", 10),
            ),
        ),
        _scenario(
            "S13",
            "controlled T8 value 33.33 with sample size three",
            "cost-focused",
            requirement,
            (
                (_offer("A", "90", "8"), "33.33", 3),
                (_offer("B", "100", "6"), "66.67", 6),
                (_offer("C", "110", "4"), "100", 9),
            ),
        ),
        _scenario(
            "S14",
            "ties use deterministic offer-id ordering",
            "cost-focused",
            requirement,
            (
                (_offer("B", "100", "5"), "80", 10),
                (_offer("A", "100", "5"), "80", 10),
                (_offer("C", "100", "5"), "80", 10),
            ),
        ),
        _scenario(
            "S15",
            "price lead-time and history signals conflict",
            "risk-averse",
            requirement,
            (
                (_offer("A", "85", "10"), "40", 20),
                (_offer("B", "100", "5"), "70", 20),
                (_offer("C", "115", "8"), "98", 20),
            ),
        ),
    )


def _scenario(
    scenario_id: str,
    description: str,
    profile_name: str,
    requirement: PurchaseRequirement,
    rows: tuple[tuple[SupplierOffer, str | None, int], ...],
) -> EvaluationScenario:
    return EvaluationScenario(
        scenario_id=scenario_id,
        description=description,
        profile_name=profile_name,
        requirement=requirement,
        offers=tuple(row[0] for row in rows),
        history=tuple(
            HistoryValue(row[0].offer_id, Decimal(row[1]) if row[1] is not None else None, row[2])
            for row in rows
        ),
    )


def _offer(offer_id: str, price: str, lead_time: str, moq: str = "1") -> SupplierOffer:
    return SupplierOffer(
        offer_id=offer_id,
        supplier_id=f"supplier-{offer_id}",
        unit_price=Decimal(price),
        lead_time_days=Decimal(lead_time),
        minimum_order_quantity=Decimal(moq),
    )


def alternative_set_sensitivity() -> tuple[EvaluationResult, ...]:
    """Show an existing-offer rank reversal caused by min-max set dependence."""

    scenario = next(item for item in required_scenarios() if item.scenario_id == "S12")
    without_third = replace(
        scenario,
        scenario_id="S12-without-third",
        offers=scenario.offers[:2],
        history=scenario.history[:2],
    )
    sensitivity_profile = ProfileProposal(
        name="alternative-set-sensitivity",
        baseline_unit_price=Decimal("0.70"),
        baseline_lead_time=Decimal("0.30"),
        candidate=CandidateWeights(Decimal("0.45"), Decimal("0.20"), Decimal("0.35")),
    )
    return tuple(
        evaluate_scenario(
            case,
            normalization=normalization,
            profile=sensitivity_profile,
        )
        for normalization in (
            HistoryNormalization.ABSOLUTE,
            HistoryNormalization.MIN_MAX,
        )
        for case in (without_third, scenario)
    )


def evaluation_report() -> dict[str, Any]:
    """Build the reproducible default T9 evidence payload."""

    scenarios = required_scenarios()
    recommended = tuple(evaluate_scenario(scenario) for scenario in scenarios)
    missing_case = next(item for item in scenarios if item.scenario_id == "S07")
    missing_policy_results = tuple(
        evaluate_scenario(missing_case, missing_history_policy=policy)
        for policy in MissingHistoryPolicy
    )
    normalization_case = next(item for item in scenarios if item.scenario_id == "S09")
    normalization_results = tuple(
        evaluate_scenario(normalization_case, normalization=normalization)
        for normalization in HistoryNormalization
    )
    weight_case = next(item for item in scenarios if item.scenario_id == "S02")
    weight_results = sensitivity_sweep(
        weight_case,
        tuple(Decimal(index) / Decimal("100") for index in range(0, 55, 5)),
    )
    return {
        "status": "analysis_only_not_runtime_policy",
        "profiles": PROFILE_PROPOSALS,
        "scenario_matrix": recommended,
        "normalization_comparison": normalization_results,
        "missing_policy_comparison": missing_policy_results,
        "history_weight_sweep": weight_results,
        "alternative_set_sensitivity": alternative_set_sensitivity(),
        "exact_weight_thresholds_s02": {
            "A_equals_B": history_weight_flip_threshold(
                Decimal("1"), Decimal("0.5"), Decimal("0.4"), Decimal("0.8")
            ),
            "A_equals_C": history_weight_flip_threshold(
                Decimal("1"), Decimal("0"), Decimal("0.4"), Decimal("0.95")
            ),
            "B_equals_C": history_weight_flip_threshold(
                Decimal("0.5"), Decimal("0"), Decimal("0.8"), Decimal("0.95")
            ),
        },
    }


def _json_compatible(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_compatible(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_compatible(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    indent = None if args.compact else 2
    print(json.dumps(_json_compatible(evaluation_report()), indent=indent, sort_keys=True))


if __name__ == "__main__":
    main()
