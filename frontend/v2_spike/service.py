"""Mock service adapter: lookup recorded outputs, approve a snapshot, report PDF pending."""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Protocol

from frontend.v2_spike.contracts import (
    ApprovedDTO,
    CaseDTO,
    PdfDTO,
    PlanDTO,
    ResultDTO,
    ServiceError,
    SupplierDTO,
)

FIXTURE = Path(__file__).resolve().parents[2] / "docs/spikes/v2-reflex-frontend-fixture.json"
MODES = (
    "Ready",
    "Service unavailable",
    "No plans",
    "Risk unavailable",
    "Approval unavailable",
    "PDF pending",
)


class CockpitClient(Protocol):
    async def load(self, mode: str) -> tuple[CaseDTO, list[SupplierDTO], ResultDTO]: ...
    async def scenario(self, operation: str, supplier_id: str, mode: str) -> ResultDTO: ...
    async def approve(
        self, scenario_key: str, plan_id: str, note: str, mode: str, *, expected_plan: PlanDTO
    ) -> ApprovedDTO: ...
    async def pdf(self, approved: ApprovedDTO, mode: str) -> PdfDTO: ...


class MockCockpitClient:
    """Stateless per-request mock; approvals are returned to each user's UI session."""

    def __init__(self, latency: float = 0.35):
        self.latency = latency

    async def _ready(self, mode: str) -> dict:
        await asyncio.sleep(self.latency)
        if mode not in MODES:
            raise ServiceError("Choose a supported preview state.")
        if mode == "Service unavailable":
            raise ServiceError("Case service is unavailable. Restore service and reload the case.")
        try:
            return json.loads(FIXTURE.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ServiceError(
                "Case data is unavailable. Restore the case service and reload."
            ) from exc

    async def load(self, mode: str = "Ready"):
        data = await self._ready(mode)
        suppliers = [SupplierDTO.model_validate(row) for row in data["suppliers"]]
        if mode == "Risk unavailable":
            suppliers = [
                s.model_copy(
                    update={
                        "risk_score": None,
                        "predicted_class": "Withheld",
                        "explanation": ["No current risk assessment is available."],
                    }
                )
                for s in suppliers
            ]
        result = ResultDTO.model_validate(data["scenarios"]["baseline"])
        if mode in ("No plans", "Risk unavailable"):
            result = result.model_copy(update={"plans": []})
        return CaseDTO.model_validate(data["case"]), suppliers, result

    async def scenario(self, operation: str, supplier_id: str, mode: str = "Ready"):
        data = await self._ready(mode)
        if mode in ("No plans", "Risk unavailable"):
            raise ServiceError("Complete case and risk data are required for scenario results.")
        key = f"{operation}_{supplier_id}"
        if key not in data["scenarios"]:
            raise ServiceError("Choose an available scenario and supplier.")
        return ResultDTO.model_validate(data["scenarios"][key])

    async def approve(
        self,
        scenario_key: str,
        plan_id: str,
        note: str,
        mode: str = "Ready",
        *,
        expected_plan: PlanDTO,
    ):
        data = await self._ready(mode)
        if mode == "Approval unavailable":
            raise ServiceError("Approval could not be recorded. Your plan remains open for review.")
        if mode in ("No plans", "Risk unavailable"):
            raise ServiceError("Reload complete plan and risk data before approval.")
        result = data["scenarios"].get(scenario_key)
        plan = next((p for p in (result or {}).get("plans", []) if p["plan_id"] == plan_id), None)
        if plan is None or not plan["feasible"]:
            raise ServiceError("Select a feasible plan from the current review.")
        if PlanDTO.model_validate(plan) != expected_plan:
            raise ServiceError("The plan changed. Reload the case and review it before approval.")
        snapshot = {
            "case_id": data["case"]["case_id"],
            "case_version": data["case"]["version"],
            "scenario_key": scenario_key,
            "plan": plan,
            "note": note.strip(),
        }
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        return ApprovedDTO(
            approval_id=f"APP-{digest[:12]}",
            snapshot_hash=digest,
            **{**snapshot, "plan": PlanDTO.model_validate(plan)},
        )

    async def pdf(self, approved: ApprovedDTO, mode: str = "Ready"):
        await self._ready(mode)
        return PdfDTO(
            status="pending",
            approval_id=approved.approval_id,
            snapshot_hash=approved.snapshot_hash,
            message=(
                "PDF not yet available. The backend will generate it from this approved snapshot."
            ),
        )


client: CockpitClient = MockCockpitClient()
