"""One-time human decision on the base case and its approved PDF (in the UI language)."""

from base64 import b64encode
from copy import deepcopy
from typing import Any

import reflex as rx

from frontend.config import settings
from frontend.i18n import tr
from frontend.planning.state_base import focus
from frontend.planning_client import fetch_planning_case
from frontend.planning_pdf_client import fetch_planning_pdf


class DecisionMixin(rx.State, mixin=True):
    final_choice: str = ""
    decision_open: bool = False
    decision_review: dict[str, str] = {}
    _decision_payload: dict = {}
    pdf_data_url: str = ""
    pdf_error: str = ""
    pdf_reference: str = ""
    pdf_filename: str = ""

    @rx.event
    def choose_final_plan(self, value: str):
        if (
            self.has_case
            and not self.is_loading
            and not self.has_pending
            and not self.decision_open
            and not self.details.get("final_outcome")
            and value in [p["label"] for p in self.plans] + ["", "No-award"]
            and (value != "No-award" or self.details.get("parent_id") == "Base case")
        ):
            self.final_choice = value
            self._clear_decision_review()
            if value in {"", "No-award"}:
                return focus("final-decision-heading")

    @rx.var
    def comparison_state(self) -> str:
        lang = self.lang if self.lang in ("hu", "en") else "hu"
        if self.decision_conflict:
            return tr("state_conflict", lang)
        if self.has_pending:
            return tr("state_saving" if self.is_loading else "state_unconfirmed", lang)
        if not self.has_case:
            return ""
        outcome = self.details.get("final_outcome", "")
        if outcome == "Approved":
            return tr("state_approved", lang)
        if outcome == "No-award":
            return tr("state_no_award", lang)
        if self.details.get("parent_id", "Base case") != "Base case":
            return tr("state_scenario", lang)
        if self.final_choice == "No-award":
            return tr("state_no_award_selected", lang)
        if self.final_choice:
            return tr("state_selected", lang)
        return tr("state_awaiting", lang)

    @rx.var
    def selected_plan(self) -> dict[str, str]:
        choice = (
            self.details.get("final_plan", "")
            if self.details.get("final_outcome") == "Approved"
            else self.final_choice
        )
        return next((p for p in self.plans if p["label"] == choice), {})

    @rx.event
    def review_final_decision(self, form_data: dict[str, Any]):
        if self.is_loading or self.has_pending or self.decision_conflict:
            return
        self._clear_decision_review()
        self.error_target = "decision"
        self.error_message = ""
        try:
            if (
                not self.has_case
                or self.details["parent_id"] != "Base case"
                or self.details["final_outcome"]
            ):
                raise ValueError(self._tr("err_decide_base"))
            choice = form_data.get("choice", "")
            actor = form_data.get("actor", "")
            reason = form_data.get("reason", "")
            if choice not in [p["label"] for p in self.plans] + ["No-award"]:
                raise ValueError(self._tr("err_choose_plan"))
            index = next((i for i, p in enumerate(self.plans) if p["label"] == choice), None)
            if not isinstance(actor, str) or not 1 <= len(actor.strip()) <= 255:
                raise ValueError(self._tr("err_actor"))
            if (
                not isinstance(reason, str)
                or len(reason) > 2000
                or (index != 0 and not reason.strip())
            ):
                raise ValueError(self._tr("err_reason"))
            if form_data.get("demonstration") != "on":
                raise ValueError(self._tr("err_ack"))
            payload = {
                "snapshot_hash": self.details["snapshot_hash"],
                "outcome": "no_award" if choice == "No-award" else "approve",
                "plan_index": index,
                "actor_reference": actor,
                "rationale": reason.strip() or None,
                "demonstration_acknowledged": True,
            }
        except (ValueError, KeyError) as error:
            self.error_message = str(error)
            return focus("decision-error")
        self.final_choice = choice
        self._decision_payload = payload
        self.decision_review = {
            "case_id": self.details["case_id"],
            "choice": choice,
            "actor": actor.strip(),
            "reason": reason.strip() or "—",
            **deepcopy(self.selected_plan),
        }
        self.decision_open = True

    def _clear_decision_review(self):
        self.decision_open = False
        self.decision_review = {}
        self._decision_payload = {}

    @rx.event
    def change_decision_confirmation(self, opened: bool):
        if not opened and not self.is_loading and not self.has_pending:
            self._clear_decision_review()

    @rx.event
    async def confirm_final_decision(self):
        if self.is_loading or self.has_pending or self.decision_conflict or not self.decision_open:
            return
        if (
            not self.has_case
            or self.details.get("parent_id") != "Base case"
            or self.details.get("final_outcome")
            or self.decision_review.get("case_id") != self.details.get("case_id")
            or self.decision_review.get("choice") != self.final_choice
            or self._decision_payload.get("snapshot_hash") != self.details.get("snapshot_hash")
        ):
            self._clear_decision_review()
            self.error_target = "decision"
            self.error_message = self._tr("err_review_changed")
            return
        self._prepare_request(
            f"{settings.planning_cases_url}/{self.details['case_id']}/final-decision",
            self._decision_payload,
        )
        self._clear_decision_review()
        yield
        try:
            saved = await self._send_pending()
        finally:
            self.is_loading = False
        if saved is not None:
            self.view = "decision"
            yield focus("saved-decision-heading")
        elif self.has_pending:
            yield focus("request-recovery-heading")

    @rx.event
    async def reopen_conflicted_decision(self):
        if self.is_loading or not self.decision_conflict or not self.has_case:
            return
        self.is_loading = True
        yield
        try:
            saved, error = await fetch_planning_case(
                settings.planning_cases_url,
                self.details["case_id"],
                settings.api_service_token.get_secret_value(),
                lang=self._lang(),
            )
            if saved is not None and saved.details["final_outcome"]:
                self.has_pending = False
                self._pending = {}
                self.decision_conflict = False
                self._show(saved)
                self.view = "decision"
                self.notice = self._tr("notice_reopened")
            else:
                self.error_message = error or self._tr("err_no_decision_record")
        finally:
            self.is_loading = False
        if not self.decision_conflict:
            yield focus("saved-decision-heading")

    @rx.event
    async def request_pdf(self):
        if self.is_loading or self.has_pending:
            return
        if not self.has_case or self.details.get("final_outcome") != "Approved":
            self.pdf_error = self._tr("err_pdf_not_approved")
            return
        self.is_loading = True
        self.pdf_error = ""
        self.pdf_data_url = ""
        yield
        try:
            document, self.pdf_error = await fetch_planning_pdf(
                settings.planning_cases_url,
                self.details["case_id"],
                self.details["final_content_hash"],
                settings.api_service_token.get_secret_value(),
                language=self._lang(),
            )
            if document is not None:
                self.pdf_reference = document.reference
                self.pdf_filename = document.filename
                self.pdf_data_url = "data:application/pdf;base64," + b64encode(
                    document.data
                ).decode("ascii")
        finally:
            self.is_loading = False
