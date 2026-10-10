"""Shared controlled demonstration inputs and transactional fast-test repository."""

import json

from tools.t15_demo import prepare_assets as controlled_assets

__all__ = ["MemoryPlanningUnitOfWork", "controlled_assets", "copy_payload"]


def copy_payload(payload):
    return json.loads(json.dumps(payload))


class MemoryPlanningUnitOfWork:
    """Snapshot row/key rollback, matching the single-row durable mapping contract."""

    def __init__(self):
        self.rows = {}
        self.cases = self
        self.decisions = MemoryPlanningDecisions()

    def __enter__(self):
        self.before = self.rows.copy()
        self.before_decisions = self.decisions.rows.copy()
        self.committed = False
        return self

    def __exit__(self, *args):
        if not self.committed:
            self.rows = self.before
            self.decisions.rows = self.before_decisions

    def commit(self):
        self.committed = True

    def lock(self, key):
        pass

    def get(self, case_id):
        return self.rows.get(case_id)

    def by_key(self, key):
        return next((case for case in self.rows.values() if case.idempotency_key == key), None)

    def add(self, case):
        assert self.by_key(case.idempotency_key) is None
        self.rows[case.case_id] = case


class MemoryPlanningDecisions:
    def __init__(self):
        self.rows = {}

    def lock(self, key):
        pass

    def get(self, case_id):
        return self.rows.get(case_id)

    def by_key(self, key):
        return next((d for d in self.rows.values() if d.idempotency_key == key), None)

    def add(self, decision):
        assert decision.case_id not in self.rows and self.by_key(decision.idempotency_key) is None
        self.rows[decision.case_id] = decision
