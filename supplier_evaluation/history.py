"""Reuse the bounded T8 neutral KPI policy; no live source access."""

from datetime import timedelta
from decimal import Decimal

from application.historical_performance import (
    HistoricalPerformanceAvailability,
    HistoricalPerformanceQuery,
    InventoryHistoryObservation,
    InventoryHistorySnapshot,
    ReceiptDirection,
    ReceiptEventState,
    SourcedSupplierHistoricalPerformance,
    calculate_delivery_schedule_adherence,
)
from supplier_evaluation.contracts import SYNTHETIC, Context, FeatureSnapshot, LineEvidence, utc


def from_sourced_history(
    history: SourcedSupplierHistoricalPerformance, context: Context, cutoff
) -> FeatureSnapshot:
    """Caller must establish the exact selected product/unit and historical as-of evidence.

    A current T8 response cannot establish what was known at an earlier cutoff.
    This conversion does not authorize inference from observed data with a synthetic model.
    """
    utc(cutoff)
    if not isinstance(history, SourcedSupplierHistoricalPerformance) or not isinstance(
        context, Context
    ):
        raise ValueError("Typed bounded history and context required.")
    p = history.performance
    if (
        p.supplier_id != context.supplier_id
        or p.availability is not HistoricalPerformanceAvailability.USABLE
        or p.value is None
    ):
        raise ValueError("Missing, withheld or mismatched bounded history.")
    return FeatureSnapshot(
        context,
        cutoff,
        p.observation_window_start,
        p.observation_window_end,
        p.observed_at,
        (float(p.value), float(p.sample_size)),
        history.source_type,
        history.source_reference,
    )


def prepare_history(
    context: Context, cutoff, lines: tuple[LineEvidence, ...], source_type: str, reference: str
) -> FeatureSnapshot:
    utc(cutoff)
    if source_type != SYNTHETIC:
        raise ValueError("Unit-complete receipt construction is restricted to synthetic evidence.")
    if not isinstance(context, Context) or any(
        not isinstance(line, LineEvidence) for line in lines
    ):
        raise ValueError("Typed receipt evidence and context required.")
    if not isinstance(lines, tuple) or not 3 <= len(lines) <= 50:
        raise ValueError("Bounded prior support must be between 3 and 50 lines.")
    if len({line.line_id for line in lines}) != len(lines):
        raise ValueError("Duplicate history line.")
    start = cutoff - timedelta(days=365)
    if any(
        line.context != context
        or not start <= line.completed_at < cutoff
        or line.available_at > cutoff
        for line in lines
    ):
        raise ValueError("History context or prediction cutoff violation.")
    query = HistoricalPerformanceQuery(
        context.supplier_id,
        context.company_id,
        tuple(line.line_id for line in lines),
        start,
        cutoff,
        200,
    )
    observations = tuple(
        InventoryHistoryObservation(
            context.company_id,
            context.supplier_id,
            f"order:{line.line_id}",
            line.line_id,
            context.product_id,
            context.quantity_unit,
            line.expected_arrival,
            f"event:{line.line_id}",
            f"transfer:{line.line_id}",
            line.completed_at,
            Decimal(1),
            Decimal(1),
            ReceiptEventState.COMPLETED,
            ReceiptDirection.SUPPLIER_TO_INTERNAL,
        )
        for line in lines
    )
    snapshot = InventoryHistorySnapshot(query, observations, cutoff, source_type, reference)
    sourced = SourcedSupplierHistoricalPerformance(
        calculate_delivery_schedule_adherence(snapshot),
        source_type,
        reference,
    )
    return from_sourced_history(sourced, context, cutoff)
