"""Versioned JSON-safe serialization for immutable decision-case snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from application.decision_cases import SNAPSHOT_VERSION, DecisionCaseError, EvaluationSnapshot
from application.decision_input_assembly import (
    CanonicalDecisionInput,
    FieldProvenance,
    ProvenanceManifest,
)
from application.historical_performance import (
    HistoricalDataWarning,
    HistoricalMetric,
    HistoricalPerformanceAvailability,
    HistoricalWarningCode,
    SupplierHistoricalPerformance,
)
from decision_core import (
    Constraint,
    Criterion,
    CriterionContribution,
    CriterionDirection,
    DecisionResult,
    ExcludedOffer,
    HistoricalCriterionContribution,
    HistoricalScoringProfile,
    HistoricalScoringResult,
    PurchaseRequirement,
    RankedOffer,
    StrategicProfile,
    SupplierOffer,
)

JsonObject = dict[str, Any]


def serialize_canonical_input(value: CanonicalDecisionInput) -> JsonObject:
    """Serialize canonical inputs without mixing in provenance."""

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "requirement": _requirement_to_dict(value.requirement),
        "offers": [_offer_to_dict(item) for item in value.offers],
        "profile": _profile_to_dict(value.profile),
        "historical_performance": [_history_to_dict(item) for item in value.historical_performance],
    }


def deserialize_canonical_input(payload: Mapping[str, Any]) -> CanonicalDecisionInput:
    """Reconstruct a supported canonical input snapshot without evaluation."""

    data = _snapshot(payload)
    try:
        return CanonicalDecisionInput(
            requirement=_requirement_from_dict(_mapping(data["requirement"])),
            offers=tuple(_offer_from_dict(_mapping(item)) for item in _list(data["offers"])),
            profile=_strategic_profile_from_dict(_mapping(data["profile"])),
            historical_performance=tuple(
                _history_from_dict(_mapping(item)) for item in _list(data["historical_performance"])
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        _invalid("The canonical-input snapshot is malformed.", error)


def serialize_scoring_policy(value: StrategicProfile | HistoricalScoringProfile) -> JsonObject:
    """Serialize the explicitly selected policy, including historical fallback weights."""

    return {"snapshot_version": SNAPSHOT_VERSION, "policy": _profile_to_dict(value)}


def deserialize_scoring_policy(
    payload: Mapping[str, Any],
) -> StrategicProfile | HistoricalScoringProfile:
    data = _snapshot(payload)
    try:
        return _profile_from_dict(_mapping(data["policy"]))
    except (KeyError, TypeError, ValueError) as error:
        _invalid("The scoring-policy snapshot is malformed.", error)


def serialize_evaluation(value: EvaluationSnapshot) -> JsonObject:
    """Serialize either the legacy result or the historical activation wrapper."""

    if isinstance(value, HistoricalScoringResult):
        return {
            "snapshot_version": SNAPSHOT_VERSION,
            "result_type": "historical",
            "decision_result": _decision_result_to_dict(value.decision_result),
            "historical_criterion_active": value.historical_criterion_active,
            "explanation": value.explanation,
            "affected_offer_ids": list(value.affected_offer_ids),
            "affected_supplier_ids": list(value.affected_supplier_ids),
        }
    if isinstance(value, DecisionResult):
        return {
            "snapshot_version": SNAPSHOT_VERSION,
            "result_type": "legacy",
            "decision_result": _decision_result_to_dict(value),
        }
    raise DecisionCaseError("invalid_snapshot", "The evaluation result is unsupported.")


def deserialize_evaluation(payload: Mapping[str, Any]) -> EvaluationSnapshot:
    """Reconstruct a result snapshot exactly; never invoke a scorer."""

    data = _snapshot(payload)
    try:
        result_type = data["result_type"]
        decision_result = _decision_result_from_dict(_mapping(data["decision_result"]))
        if result_type == "legacy":
            return decision_result
        if result_type == "historical":
            return HistoricalScoringResult(
                decision_result=decision_result,
                historical_criterion_active=_bool(data["historical_criterion_active"]),
                explanation=_text(data["explanation"]),
                affected_offer_ids=tuple(_text(item) for item in _list(data["affected_offer_ids"])),
                affected_supplier_ids=tuple(
                    _text(item) for item in _list(data["affected_supplier_ids"])
                ),
            )
        raise DecisionCaseError(
            "invalid_snapshot", f"Unsupported evaluation result type: {result_type!r}."
        )
    except DecisionCaseError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        _invalid("The evaluation snapshot is malformed.", error)


def serialize_provenance(value: ProvenanceManifest) -> JsonObject:
    """Serialize provenance in a document separate from canonical/core data."""

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "entries": [
            {
                "canonical_path": item.canonical_path,
                "field_name": item.field_name,
                "source_type": item.source_type,
                "source_reference": item.source_reference,
                "observed_at": _time_to_text(item.observed_at),
            }
            for item in value.entries
        ],
    }


def deserialize_provenance(payload: Mapping[str, Any]) -> ProvenanceManifest:
    data = _snapshot(payload)
    try:
        return ProvenanceManifest(
            entries=tuple(
                FieldProvenance(
                    canonical_path=_text(item["canonical_path"]),
                    field_name=_text(item["field_name"]),
                    source_type=_text(item["source_type"]),
                    source_reference=_text(item["source_reference"]),
                    observed_at=_time_from_text(item["observed_at"]),
                )
                for raw in _list(data["entries"])
                for item in (_mapping(raw),)
            )
        )
    except (KeyError, TypeError, ValueError) as error:
        _invalid("The provenance snapshot is malformed.", error)


def _decision_result_to_dict(value: DecisionResult) -> JsonObject:
    return {
        "requirement": _requirement_to_dict(value.requirement),
        "profile": _profile_to_dict(value.profile),
        "ranked_offers": [_ranked_offer_to_dict(item) for item in value.ranked_offers],
        "excluded_offers": [_excluded_offer_to_dict(item) for item in value.excluded_offers],
    }


def _decision_result_from_dict(data: Mapping[str, Any]) -> DecisionResult:
    return DecisionResult(
        requirement=_requirement_from_dict(_mapping(data["requirement"])),
        profile=_profile_from_dict(_mapping(data["profile"])),
        ranked_offers=tuple(
            _ranked_offer_from_dict(_mapping(item)) for item in _list(data["ranked_offers"])
        ),
        excluded_offers=tuple(
            _excluded_offer_from_dict(_mapping(item)) for item in _list(data["excluded_offers"])
        ),
    )


def _requirement_to_dict(value: PurchaseRequirement) -> JsonObject:
    return {
        "requirement_id": value.requirement_id,
        "requested_quantity": _decimal_to_text(value.requested_quantity),
    }


def _requirement_from_dict(data: Mapping[str, Any]) -> PurchaseRequirement:
    return PurchaseRequirement(
        requirement_id=_text(data["requirement_id"]),
        requested_quantity=_decimal_from_text(data["requested_quantity"]),
    )


def _offer_to_dict(value: SupplierOffer) -> JsonObject:
    return {
        "offer_id": value.offer_id,
        "supplier_id": value.supplier_id,
        "unit_price": _decimal_to_text(value.unit_price),
        "lead_time_days": _decimal_to_text(value.lead_time_days),
        "minimum_order_quantity": _decimal_to_text(value.minimum_order_quantity),
    }


def _offer_from_dict(data: Mapping[str, Any]) -> SupplierOffer:
    return SupplierOffer(
        offer_id=_text(data["offer_id"]),
        supplier_id=_text(data["supplier_id"]),
        unit_price=_decimal_from_text(data["unit_price"]),
        lead_time_days=_decimal_from_text(data["lead_time_days"]),
        minimum_order_quantity=_decimal_from_text(data["minimum_order_quantity"]),
    )


def _profile_to_dict(value: StrategicProfile | HistoricalScoringProfile) -> JsonObject:
    common = {
        "name": value.name,
        "unit_price_weight": _decimal_to_text(value.unit_price_weight),
        "lead_time_weight": _decimal_to_text(value.lead_time_weight),
    }
    if isinstance(value, HistoricalScoringProfile):
        return {
            "profile_type": "historical",
            **common,
            "delivery_schedule_adherence_weight": _decimal_to_text(
                value.delivery_schedule_adherence_weight
            ),
            "fallback_profile": _profile_to_dict(value.fallback_profile),
        }
    return {"profile_type": "strategic", **common}


def _profile_from_dict(data: Mapping[str, Any]) -> StrategicProfile | HistoricalScoringProfile:
    profile_type = data["profile_type"]
    if profile_type == "strategic":
        return StrategicProfile(
            name=_text(data["name"]),
            unit_price_weight=_decimal_from_text(data["unit_price_weight"]),
            lead_time_weight=_decimal_from_text(data["lead_time_weight"]),
        )
    if profile_type == "historical":
        fallback = _profile_from_dict(_mapping(data["fallback_profile"]))
        if not isinstance(fallback, StrategicProfile):
            raise ValueError("A historical fallback must be a strategic profile.")
        return HistoricalScoringProfile(
            name=_text(data["name"]),
            unit_price_weight=_decimal_from_text(data["unit_price_weight"]),
            lead_time_weight=_decimal_from_text(data["lead_time_weight"]),
            delivery_schedule_adherence_weight=_decimal_from_text(
                data["delivery_schedule_adherence_weight"]
            ),
            fallback_profile=fallback,
        )
    raise ValueError("Unsupported profile type.")


def _strategic_profile_from_dict(data: Mapping[str, Any]) -> StrategicProfile:
    profile = _profile_from_dict(data)
    if not isinstance(profile, StrategicProfile):
        raise ValueError("The canonical profile must be strategic.")
    return profile


def _ranked_offer_to_dict(value: RankedOffer) -> JsonObject:
    return {
        "rank": value.rank,
        "offer": _offer_to_dict(value.offer),
        "total_score": _decimal_to_text(value.total_score),
        "contributions": [_contribution_to_dict(item) for item in value.contributions],
    }


def _ranked_offer_from_dict(data: Mapping[str, Any]) -> RankedOffer:
    rank = data["rank"]
    if isinstance(rank, bool) or not isinstance(rank, int):
        raise ValueError("Rank must be an integer.")
    return RankedOffer(
        rank=rank,
        offer=_offer_from_dict(_mapping(data["offer"])),
        total_score=_decimal_from_text(data["total_score"]),
        contributions=tuple(
            _contribution_from_dict(_mapping(item)) for item in _list(data["contributions"])
        ),
    )


def _contribution_to_dict(value: CriterionContribution) -> JsonObject:
    data: JsonObject = {
        "contribution_type": (
            "historical" if isinstance(value, HistoricalCriterionContribution) else "standard"
        ),
        "criterion": value.criterion.value,
        "direction": value.direction.value,
        "raw_value": _decimal_to_text(value.raw_value),
        "normalized_value": _decimal_to_text(value.normalized_value),
        "weight": _decimal_to_text(value.weight),
        "weighted_contribution": _decimal_to_text(value.weighted_contribution),
    }
    if isinstance(value, HistoricalCriterionContribution):
        data["sample_size"] = value.sample_size
        data["explanation"] = value.explanation
    return data


def _contribution_from_dict(data: Mapping[str, Any]) -> CriterionContribution:
    common = {
        "criterion": Criterion(_text(data["criterion"])),
        "direction": CriterionDirection(_text(data["direction"])),
        "raw_value": _decimal_from_text(data["raw_value"]),
        "normalized_value": _decimal_from_text(data["normalized_value"]),
        "weight": _decimal_from_text(data["weight"]),
        "weighted_contribution": _decimal_from_text(data["weighted_contribution"]),
    }
    contribution_type = data["contribution_type"]
    if contribution_type == "standard":
        return CriterionContribution(**common)
    if contribution_type == "historical":
        sample_size = data["sample_size"]
        if isinstance(sample_size, bool) or not isinstance(sample_size, int):
            raise ValueError("Historical sample size must be an integer.")
        return HistoricalCriterionContribution(
            **common,
            sample_size=sample_size,
            explanation=_text(data["explanation"]),
        )
    raise ValueError("Unsupported contribution type.")


def _excluded_offer_to_dict(value: ExcludedOffer) -> JsonObject:
    return {
        "offer": _offer_to_dict(value.offer),
        "failed_constraint": value.failed_constraint.value,
        "explanation": value.explanation,
        "requested_quantity": _decimal_to_text(value.requested_quantity),
        "minimum_order_quantity": _decimal_to_text(value.minimum_order_quantity),
    }


def _excluded_offer_from_dict(data: Mapping[str, Any]) -> ExcludedOffer:
    return ExcludedOffer(
        offer=_offer_from_dict(_mapping(data["offer"])),
        failed_constraint=Constraint(_text(data["failed_constraint"])),
        explanation=_text(data["explanation"]),
        requested_quantity=_decimal_from_text(data["requested_quantity"]),
        minimum_order_quantity=_decimal_from_text(data["minimum_order_quantity"]),
    )


def _history_to_dict(value: SupplierHistoricalPerformance) -> JsonObject:
    return {
        "metric_id": value.metric_id.value,
        "value": _decimal_to_text(value.value) if value.value is not None else None,
        "sample_size": value.sample_size,
        "observation_window_start": _time_to_text(value.observation_window_start),
        "observation_window_end": _time_to_text(value.observation_window_end),
        "observed_at": _time_to_text(value.observed_at),
        "supplier_id": value.supplier_id,
        "availability": value.availability.value,
        "warnings": [
            {
                "code": item.code.value,
                "message": item.message,
                "affected_line_ids": list(item.affected_line_ids),
            }
            for item in value.warnings
        ],
    }


def _history_from_dict(data: Mapping[str, Any]) -> SupplierHistoricalPerformance:
    sample_size = data["sample_size"]
    if isinstance(sample_size, bool) or not isinstance(sample_size, int):
        raise ValueError("Historical sample size must be an integer.")
    raw_value = data["value"]
    return SupplierHistoricalPerformance(
        metric_id=HistoricalMetric(_text(data["metric_id"])),
        value=None if raw_value is None else _decimal_from_text(raw_value),
        sample_size=sample_size,
        observation_window_start=_time_from_text(data["observation_window_start"]),
        observation_window_end=_time_from_text(data["observation_window_end"]),
        observed_at=_time_from_text(data["observed_at"]),
        supplier_id=_text(data["supplier_id"]),
        availability=HistoricalPerformanceAvailability(_text(data["availability"])),
        warnings=tuple(
            HistoricalDataWarning(
                code=HistoricalWarningCode(_text(item["code"])),
                message=_text(item["message"]),
                affected_line_ids=tuple(
                    _text(line_id) for line_id in _list(item["affected_line_ids"])
                ),
            )
            for raw in _list(data["warnings"])
            for item in (_mapping(raw),)
        ),
    )


def _snapshot(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _mapping(payload)
    version = data.get("snapshot_version")
    if version != SNAPSHOT_VERSION:
        raise DecisionCaseError(
            "unsupported_snapshot_version", f"Unsupported snapshot version: {version!r}."
        )
    return data


def _decimal_to_text(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise DecisionCaseError("invalid_snapshot", "Snapshot decimals must be finite.")
    return format(value, "f")


def _decimal_from_text(value: Any) -> Decimal:
    if not isinstance(value, str) or not value or "e" in value.lower():
        raise ValueError("Decimal values must be plain strings.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Decimal value is malformed.") from error
    if not parsed.is_finite():
        raise ValueError("Decimal value must be finite.")
    return parsed


def _time_to_text(value: datetime) -> str:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise DecisionCaseError("invalid_snapshot", "Snapshot timestamps must be UTC.")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _time_from_text(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("Timestamps must use explicit UTC Z notation.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("Timestamp is malformed.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("Timestamp must be UTC.")
    return parsed


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("A JSON object is required.")
    return value


def _list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError("A JSON array is required.")
    return value


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A non-empty string is required.")
    return value


def _bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError("A boolean is required.")
    return value


def _invalid(message: str, error: Exception) -> None:
    raise DecisionCaseError("invalid_snapshot", message) from error
