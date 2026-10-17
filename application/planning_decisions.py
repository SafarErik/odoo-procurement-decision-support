"""One-time human decisions over stored V2 evidence; no acquisition or computation."""

import json
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Protocol

from application.errors import RepositoryError
from application.planning_cases import (
    PlanningCase,
    PlanningCaseError,
    canonical_uuid,
    fingerprint,
    validate_snapshot,
)
from application.planning_history import HISTORY_INPUT_KIND
from application.planning_serialization import (
    json_value,
    read_assessments,
    read_request,
    read_result,
    snapshot_json,
)
from decision_core.planning.models import PlanningStatus
from decision_core.planning.rules import checked_plan
from supplier_evaluation.contracts import (
    ARTIFACT_VERSION,
    CLASSES,
    DATASET_VERSION,
    FEATURE_VERSION,
    FEATURES,
    LABEL_VERSION,
    MAPPING_VERSION,
    ODOO_HISTORY,
    ODOO_MAPPING_VERSION,
    SYNTHETIC,
    text_identity,
    utc,
)
from supplier_evaluation.planning_bridge import risk_inputs
from supplier_evaluation.qualified_odoo import PACKAGE_VERSION

DECISION_VERSION = "t17-final-decision-v1"
CONTENT_VERSION = "t17-approved-planning-v1"


@dataclass(frozen=True, slots=True)
class FinalizePlanningCommand:
    snapshot_hash: str
    outcome: str
    plan_index: int | None
    actor_reference: str
    rationale: str | None
    demonstration_acknowledged: bool

    def normalized(self):
        if (
            not isinstance(self.snapshot_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.snapshot_hash) is None
            or self.outcome not in {"approve", "no_award"}
            or not isinstance(self.actor_reference, str)
            or not 1 <= len(self.actor_reference.strip()) <= 255
            or (self.rationale is not None and not isinstance(self.rationale, str))
            or (self.rationale is not None and len(self.rationale) > 2000)
            or self.demonstration_acknowledged is not True
        ):
            raise PlanningCaseError(
                "invalid_final_decision", "Review the decision and demo acknowledgement."
            )
        actor = self.actor_reference.strip()
        reason = (self.rationale or "").strip() or None
        if any(ord(c) < 32 or ord(c) == 127 for c in actor):
            raise PlanningCaseError(
                "invalid_final_decision", "Actor attribution must be audit text."
            )
        if self.outcome == "approve":
            if type(self.plan_index) is not int or self.plan_index < 0:
                raise PlanningCaseError("invalid_final_decision", "Explicitly select a saved plan.")
        elif self.plan_index is not None:
            raise PlanningCaseError("invalid_final_decision", "No-award cannot select a plan.")
        if (self.outcome == "no_award" or self.plan_index != 0) and reason is None:
            raise PlanningCaseError("invalid_final_decision", "This decision requires a reason.")
        return replace(self, actor_reference=actor, rationale=reason)


@dataclass(frozen=True, slots=True)
class PlanningFinalDecision:
    case_id: str
    idempotency_key: str
    fingerprint: str
    record: str

    @property
    def record_hash(self):
        return fingerprint(json.loads(self.record))


class PlanningDecisionRepository(Protocol):
    def lock(self, key: str) -> None: ...
    def get(self, case_id: str) -> PlanningFinalDecision | None: ...
    def by_key(self, key: str) -> PlanningFinalDecision | None: ...
    def add(self, decision: PlanningFinalDecision) -> None: ...


def _saved_evidence(case: PlanningCase) -> dict:
    """Recheck saved proof, joins and exact constraints without searching for a plan."""
    value = validate_snapshot(case)
    try:
        facts = value["facts"]
        request = read_request(value["request"])
        assessments = read_assessments(value["assessments"])
        result = read_result(value["result"])
        metadata = value["model_manifest"]["metadata"]
        history = value["facts"].get("input_kind") == HISTORY_INPUT_KIND
        source_type = ODOO_HISTORY if history else SYNTHETIC
        for name, expected in (
            ("artifact_version", PACKAGE_VERSION if history else ARTIFACT_VERSION),
            ("feature_version", FEATURE_VERSION),
            ("feature_names", list(FEATURES)),
            ("label_version", LABEL_VERSION),
            ("class_names", list(CLASSES)),
            ("mapping_version", ODOO_MAPPING_VERSION if history else MAPPING_VERSION),
            ("dataset_version", DATASET_VERSION),
            ("source_type", source_type),
            (
                "domain",
                [
                    facts["company_id"],
                    request.requirement.product_id,
                    request.requirement.quantity_unit,
                ],
            ),
        ):
            if metadata[name] != expected:
                raise ValueError("Unsupported saved model metadata.")
        for name in ("model_id", "training_id"):
            text_identity(metadata[name])
        utc(datetime.fromisoformat(metadata["trained_through"]))
        solver = value["solver"]
        for name in ("adapter",):
            text_identity(solver[name])
        if (
            not solver["configuration"]
            or not solver["runtime"]
            or solver["time_limit_seconds"] <= 0
        ):
            raise ValueError("Incomplete saved solver evidence.")
        for version in solver["runtime"].values():
            text_identity(version)
        sources = value["provenance"]["entries"]
        paths = set()
        for source in sources:
            if set(source) != {
                "canonical_path",
                "field_name",
                "source_type",
                "source_reference",
                "observed_at",
            }:
                raise ValueError("Invalid saved provenance contract.")
            for name in ("canonical_path", "field_name", "source_type", "source_reference"):
                text_identity(source[name])
            utc(datetime.fromisoformat(source["observed_at"]))
            if source["canonical_path"] in paths:
                raise ValueError("Duplicate saved provenance path.")
            paths.add(source["canonical_path"])
        required_paths = {f"request.requirement.{k}" for k in value["request"]["requirement"]}
        required_paths.update(f"request.policy.{k}" for k in value["request"]["policy"])
        required_paths.update(f"facts.{k}" for k in ("company_id", "as_of", "approval_reference"))
        for supplier in value["request"]["suppliers"]:
            required_paths.update(
                f"request.suppliers[{supplier['supplier_id']}].{k}" for k in supplier
            )
        if not required_paths <= paths:
            raise ValueError("Missing saved field provenance.")
        if (
            case.parent_id is not None
            or value["comparison"] is not None
            or facts["source_type"] != source_type
            or facts.get("input_kind", "controlled_synthetic")
            not in (
                {HISTORY_INPUT_KIND}
                if history
                else {"controlled_synthetic", "odoo_quotations_synthetic_history"}
            )
            or value["risk_context"]["controlled_fixture"] is not True
            or value["request"] != json_value(request)
            or value["assessments"] != json_value(assessments)
            or value["result"] != json_value(result)
            or facts["requirement"] != value["request"]["requirement"]
            or facts["policy"] != value["request"]["policy"]
            or [s["terms"] for s in facts["suppliers"]] != value["request"]["suppliers"]
        ):
            raise ValueError("Unsupported or inconsistent saved contracts.")
        coefficients, context = risk_inputs(
            replace(request, risk_coefficients=None),
            # T14 reference digests preserve the score's four-place mapping precision.
            tuple(replace(a, score=a.score.quantize(Decimal("0.0001"))) for a in assessments),
            company_id=facts["company_id"],
            as_of=datetime.fromisoformat(facts["as_of"]),
        )
        if (
            coefficients != request.risk_coefficients
            or json_value(context) != value["risk_context"]
            or any(a.snapshot.source_type != source_type for a in assessments)
        ):
            raise ValueError("Stored risk evidence does not match its planning context.")
        plans = (
            ()
            if result.minimum_cost_plan is None
            else (result.minimum_cost_plan, *result.alternatives)
        )
        if plans:
            if checked_plan(request, plans[0].allocations) != plans[0]:
                raise ValueError("Invalid saved reference metrics or constraints.")
            epsilons = tuple(sorted(set(request.policy.epsilons)))
            if tuple(r.epsilon for r in result.runs) != epsilons[: len(result.runs)]:
                raise ValueError("Invalid saved stage order.")
            if result.status is PlanningStatus.OPTIMAL:
                if len(result.runs) != len(epsilons):
                    raise ValueError("Missing saved stage proof.")
            elif (
                not result.runs
                or result.runs[-1].status != result.status
                or result.runs[-1].status is PlanningStatus.OPTIMAL
                or any(r.status is not PlanningStatus.OPTIMAL for r in result.runs[:-1])
            ):
                raise ValueError("Retained plans require a recorded later-stage failure.")
            proved = {0}
            for run in result.runs:
                if run.status is not PlanningStatus.OPTIMAL:
                    continue
                plan = plans[run.plan_index]
                checked = checked_plan(
                    request, plan.allocations, Fraction(plans[0].total_cost), run.epsilon
                )
                if (run.plan_index != 0 and checked != plan) or checked.risk_exposure > plans[
                    0
                ].risk_exposure:
                    raise ValueError("Invalid saved alternative proof or metrics.")
                proved.add(run.plan_index)
            if proved != set(range(len(plans))) or len({p.allocations for p in plans}) != len(
                plans
            ):
                raise ValueError("Missing proof or duplicated plan.")
        return value
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as error:
        raise RepositoryError(
            "invalid_persisted_case", "The stored approval evidence is invalid."
        ) from error


def _approved_content(case, snapshot, intent, audit):
    if intent.outcome == "no_award":
        return None
    plans = [snapshot["result"]["minimum_cost_plan"], *snapshot["result"]["alternatives"]]
    if plans[0] is None or intent.plan_index >= len(plans):
        raise PlanningCaseError(
            "invalid_final_decision", "The selected proven plan does not exist."
        )
    return {
        "content_version": CONTENT_VERSION,
        "case_id": case.case_id,
        "snapshot_hash": case.snapshot_hash,
        "plan_index": intent.plan_index,
        "selected_plan": plans[intent.plan_index],
        "planning_snapshot": snapshot,
        "human_decision": audit,
    }


def validate_final_decision(case, decision):
    """Stored reopening/replay fails closed on inconsistent human or approved content."""
    try:
        snapshot = _saved_evidence(case)
        value = json.loads(decision.record)
        if (
            set(value)
            != {
                "decision_version",
                "case_id",
                "idempotency_key",
                "intent",
                "audit",
                "approved_content",
                "approved_content_hash",
            }
            or value["decision_version"] != DECISION_VERSION
        ):
            raise ValueError("Unsupported decision contract.")
        intent = FinalizePlanningCommand(**value["intent"]).normalized()
        canonical_uuid(decision.idempotency_key)
        utc(datetime.fromisoformat(value["audit"]["recorded_at"]))
        if (
            value["case_id"] != case.case_id
            or decision.case_id != case.case_id
            or value["idempotency_key"] != decision.idempotency_key
            or value["intent"] != json_value(intent)
            or intent.snapshot_hash != case.snapshot_hash
            or decision.fingerprint != fingerprint({"case_id": case.case_id, "intent": intent})
            or value["audit"] != _audit(snapshot, intent, value["audit"]["recorded_at"])
        ):
            raise ValueError("Decision audit or intent mismatch.")
        content = _approved_content(case, snapshot, intent, value["audit"])
        if value["approved_content"] != content or value["approved_content_hash"] != (
            None if content is None else fingerprint(content)
        ):
            raise ValueError("Approved content identity mismatch.")
        return value
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        raise RepositoryError(
            "invalid_persisted_decision", "The stored final decision is invalid."
        ) from error


def _audit(snapshot, intent, recorded_at):
    return {
        "outcome": intent.outcome,
        "plan_index": intent.plan_index,
        "actor_reference": intent.actor_reference,
        "actor_attribution": "caller-supplied audit reference; not authenticated buyer identity",
        "rationale": intent.rationale,
        "recorded_at": recorded_at,
        "demonstration": (
            "Controlled demonstration; synthetic ML evidence; "
            "no current operational validity asserted"
        ),
        "planning_reference_time": snapshot["facts"]["as_of"],
        "required_date": snapshot["request"]["requirement"]["required_date"],
        "solver_outcome": snapshot["result"]["status"],
        "incomplete_comparison": (
            snapshot["result"]["minimum_cost_plan"] is not None
            and snapshot["result"]["status"] != "optimal"
        ),
    }


def finalize_planning_case(uow, case_id, key, command):
    canonical_uuid(case_id)
    canonical_uuid(key)
    intent = command.normalized()
    intent_hash = fingerprint({"case_id": case_id, "intent": intent})
    with uow:
        uow.decisions.lock("key:" + key)
        uow.decisions.lock("case:" + case_id)
        previous = uow.decisions.by_key(key)
        if previous is not None and previous.fingerprint != intent_hash:
            raise PlanningCaseError(
                "idempotency_key_conflict", "Finalization key belongs to another intent."
            )
        case = uow.cases.get(case_id)
        if case is None:
            raise PlanningCaseError("planning_case_not_found", "The planning case does not exist.")
        if case.parent_id is not None:
            raise PlanningCaseError(
                "scenario_finalization_forbidden", "Stress cases remain analytical."
            )
        snapshot = _saved_evidence(case)
        if case.snapshot_hash != intent.snapshot_hash:
            raise PlanningCaseError(
                "snapshot_hash_mismatch", "Reload the saved case before deciding."
            )
        if previous is not None:
            return case, validate_final_decision(case, previous), True
        if uow.decisions.get(case_id) is not None:
            raise PlanningCaseError(
                "planning_case_already_finalized", "This case already has a final decision."
            )
        audit = _audit(snapshot, intent, json_value(datetime.now(UTC)))
        content = _approved_content(case, snapshot, intent, audit)
        record = {
            "decision_version": DECISION_VERSION,
            "case_id": case_id,
            "idempotency_key": key,
            "intent": json_value(intent),
            "audit": audit,
            "approved_content": content,
            "approved_content_hash": None if content is None else fingerprint(content),
        }
        decision = PlanningFinalDecision(case_id, key, intent_hash, snapshot_json(record))
        uow.decisions.add(decision)
        uow.commit()
        return case, record, False


def retrieve_planning_case(uow, case_id):
    canonical_uuid(case_id)
    with uow:
        case = uow.cases.get(case_id)
        if case is None:
            raise PlanningCaseError("planning_case_not_found", "The planning case does not exist.")
        validate_snapshot(case)
        decision = uow.decisions.get(case_id)
        return case, None if decision is None else validate_final_decision(case, decision)
