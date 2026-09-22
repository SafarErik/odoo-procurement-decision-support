"""Fast T12 orchestration and replay contracts with deterministic upstream fakes."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from application.decision_case_orchestration import (
    CreateDecisionCaseCommand,
    HistorySelection,
    OrchestrationError,
    SupplierHistorySelection,
    create_decision_case,
    request_fingerprint,
    resolve_policy,
)
from application.decision_cases import DecisionCaseState
from application.decision_input_assembly import DecisionInputAssemblyError
from application.rfqs import ProcurementDataUnavailable
from decision_core import HistoricalScoringProfile, HistoricalScoringResult
from tests.test_decision_input_assembly import OBSERVED_AT, _case, _history, _supplements


class FakeCases:
    def __init__(self):
        self.items = {}

    def add(self, case):
        self.items[case.decision_case_id] = case

    def get(self, case_id, *, for_update=False):
        return self.items.get(case_id)

    def finalize(self, case):
        self.items[case.decision_case_id] = case


class FakeCreations:
    def __init__(self):
        self.items = {}
        self.locks = []

    def lock(self, key):
        self.locks.append(key)

    def get(self, key):
        return self.items.get(key)

    def add(self, key, fingerprint, case_id):
        self.items[key] = (fingerprint, case_id)


class FakeUnitOfWork:
    def __init__(self):
        self.cases = FakeCases()
        self.creations = FakeCreations()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def commit(self):
        self.commits += 1


class FakeComparisonReader:
    def __init__(self, facts=None):
        self.facts = facts or _case()
        self.calls = 0

    async def read_comparison_case(self, group_id):
        self.calls += 1
        assert group_id == 501
        return self.facts


class FakeHistoryReader:
    def __init__(self):
        self.calls = 0

    async def read_inventory_history(self, query):
        self.calls += 1
        raise AssertionError("Unexpected history read")


def _command(policy="cost-focused", history=None, terms=None, key=None):
    return CreateDecisionCaseCommand(
        501, terms if terms is not None else _supplements(), policy, history, key or str(uuid4())
    )


def _create(command, uow, comparison, history):
    return asyncio.run(
        create_decision_case(
            command,
            comparison_reader=comparison,
            history_reader=history,
            unit_of_work=uow,
            clock=lambda: OBSERVED_AT,
            new_id=lambda: str(uuid4()),
        )
    )


def test_all_supported_policies_resolve_to_existing_factories():
    for name in (
        "cost-focused",
        "urgent",
        "balanced",
        "cost_focused_history_v1",
        "urgent_history_v1",
        "risk_averse_history_v1",
    ):
        assert resolve_policy(name).name == name
    with pytest.raises(OrchestrationError, match="unsupported"):
        resolve_policy("unapproved")


def test_create_and_exact_replay_skip_upstream_calls():
    uow, comparison, history = FakeUnitOfWork(), FakeComparisonReader(), FakeHistoryReader()
    command = _command()
    first = _create(command, uow, comparison, history)
    second = _create(command, uow, comparison, history)
    assert first.decision_case == second.decision_case
    assert not first.replayed and second.replayed
    assert comparison.calls == 1 and history.calls == 0
    assert uow.commits == 1 and len(uow.cases.items) == 1
    assert first.decision_case.state is DecisionCaseState.EVALUATED
    assert (
        first.decision_case.assembled_input.canonical.offers[0].offer_id
        == "odoo:purchase.order:10A"
    )


def test_conflicting_replay_fails_before_odoo():
    uow, comparison, history = FakeUnitOfWork(), FakeComparisonReader(), FakeHistoryReader()
    command = _command()
    _create(command, uow, comparison, history)
    changed = replace(command, scoring_policy_id="urgent")
    with pytest.raises(OrchestrationError) as error:
        _create(changed, uow, comparison, history)
    assert error.value.code == "creation_idempotency_conflict"
    assert comparison.calls == 1 and uow.commits == 1


@pytest.mark.parametrize("terms", [(), _supplements()[:2], (*_supplements(), _supplements()[0])])
def test_missing_or_duplicate_supplemental_mapping_fails_closed(terms):
    command = _command(terms=terms)
    with pytest.raises((OrchestrationError, DecisionInputAssemblyError)):
        _create(command, FakeUnitOfWork(), FakeComparisonReader(), FakeHistoryReader())


def test_history_selection_queries_and_accepted_fallback(monkeypatch):
    facts = replace(
        _case(),
        offers=tuple(
            replace(offer, supplier_id=f"odoo:res.partner:{301 + index}")
            for index, offer in enumerate(_case().offers)
        ),
    )
    selected = HistorySelection(
        OBSERVED_AT,
        tuple(
            SupplierHistorySelection(
                offer.supplier_id,
                (f"odoo:purchase.order.line:{201 + index}",),
            )
            for index, offer in enumerate(facts.offers)
        ),
    )
    received = []

    async def acquire(reader, queries):
        received.extend(queries)
        return tuple(
            replace(
                history,
                performance=replace(
                    history.performance, supplier_id=f"odoo:res.partner:{301 + index}"
                ),
            )
            for index, history in enumerate(
                (_history("A"), _history("B", value=None, sample_size=2), _history("C"))
            )
        )

    monkeypatch.setattr(
        "application.decision_case_orchestration.acquire_historical_performance", acquire
    )
    result = _create(
        _command("cost_focused_history_v1", selected),
        FakeUnitOfWork(),
        FakeComparisonReader(facts),
        FakeHistoryReader(),
    )
    assert isinstance(result.decision_case.scoring_policy, HistoricalScoringProfile)
    assert isinstance(result.decision_case.evaluation, HistoricalScoringResult)
    assert not result.decision_case.evaluation.historical_criterion_active
    assert len(received) == 3
    assert all(
        query.observation_window_end - query.observation_window_start == timedelta(days=365)
        for query in received
    )


def test_historical_policy_without_history_uses_exact_fallback():
    case = _create(
        _command("cost_focused_history_v1"),
        FakeUnitOfWork(),
        FakeComparisonReader(),
        FakeHistoryReader(),
    ).decision_case
    assert isinstance(case.evaluation, HistoricalScoringResult)
    assert not case.evaluation.historical_criterion_active
    assert case.decision_result.profile == case.scoring_policy.fallback_profile


def test_historical_policy_activates_with_complete_usable_history(monkeypatch):
    # Reuse a numeric supplier fixture and return an accepted usable value for each supplier.
    facts = replace(
        _case(),
        offers=tuple(
            replace(offer, supplier_id=f"odoo:res.partner:{301 + index}")
            for index, offer in enumerate(_case().offers)
        ),
    )
    selection = HistorySelection(
        OBSERVED_AT,
        tuple(
            SupplierHistorySelection(
                offer.supplier_id, (f"odoo:purchase.order.line:{201 + index}",)
            )
            for index, offer in enumerate(facts.offers)
        ),
    )

    async def acquire(reader, queries):
        return tuple(
            replace(
                _history(suffix),
                performance=replace(
                    _history(suffix).performance, supplier_id=f"odoo:res.partner:{301 + index}"
                ),
            )
            for index, suffix in enumerate("ABC")
        )

    monkeypatch.setattr(
        "application.decision_case_orchestration.acquire_historical_performance", acquire
    )
    case = _create(
        _command("cost_focused_history_v1", selection),
        FakeUnitOfWork(),
        FakeComparisonReader(facts),
        FakeHistoryReader(),
    ).decision_case
    assert case.evaluation.historical_criterion_active
    assert case.decision_result.profile == case.scoring_policy


def test_all_excluded_and_failed_first_attempt_does_not_poison_key():
    terms = tuple(
        replace(
            item,
            hard_minimum_order_quantity=replace(
                item.hard_minimum_order_quantity, value=Decimal("101")
            ),
        )
        for item in _supplements()
    )
    command = _command(terms=terms)
    uow = FakeUnitOfWork()

    class FailingOnce(FakeComparisonReader):
        async def read_comparison_case(self, group_id):
            if self.calls == 0:
                self.calls += 1
                raise ProcurementDataUnavailable("temporary")
            return await super().read_comparison_case(group_id)

    reader = FailingOnce()
    with pytest.raises(OrchestrationError) as failure:
        _create(command, uow, reader, FakeHistoryReader())
    assert failure.value.code == "odoo_unavailable"
    assert not uow.creations.items and not uow.cases.items
    created = _create(command, uow, reader, FakeHistoryReader()).decision_case
    assert created.recommended_offer_id is None
    assert len(created.decision_result.excluded_offers) == 3


def test_fingerprint_normalizes_order_and_utc_offsets():
    command = _command()
    reordered = replace(command, supplemental_terms=tuple(reversed(command.supplemental_terms)))
    assert request_fingerprint(command) == request_fingerprint(reordered)


def test_unknown_supplemental_offer_and_history_supplier_fail_closed():
    unknown = replace(_supplements()[0], offer_id="odoo:purchase.order:999")
    with pytest.raises(OrchestrationError) as error:
        _create(
            _command(terms=(unknown, *_supplements()[1:])),
            FakeUnitOfWork(),
            FakeComparisonReader(),
            FakeHistoryReader(),
        )
    assert error.value.code == "unknown_supplemental_offer_identity"

    selection = HistorySelection(
        OBSERVED_AT,
        (SupplierHistorySelection("odoo:res.partner:999", ("odoo:purchase.order.line:201",)),),
    )
    with pytest.raises(OrchestrationError) as error:
        _create(
            _command(history=selection),
            FakeUnitOfWork(),
            FakeComparisonReader(),
            FakeHistoryReader(),
        )
    assert error.value.code == "invalid_history_selection"


def test_duplicate_or_invalid_history_selection_fails_before_upstream():
    selected = SupplierHistorySelection("odoo:res.partner:301", ("odoo:purchase.order.line:201",))
    for selection in (
        HistorySelection(OBSERVED_AT, (selected, selected)),
        HistorySelection(
            OBSERVED_AT,
            (
                selected,
                SupplierHistorySelection("odoo:res.partner:302", ("odoo:purchase.order.line:201",)),
            ),
        ),
        HistorySelection(
            OBSERVED_AT,
            (SupplierHistorySelection("odoo:res.partner:301", ("line-201",)),),
        ),
    ):
        reader = FakeComparisonReader()
        with pytest.raises(OrchestrationError) as error:
            _create(_command(history=selection), FakeUnitOfWork(), reader, FakeHistoryReader())
        assert error.value.code == "invalid_history_selection"
        assert reader.calls == 0
