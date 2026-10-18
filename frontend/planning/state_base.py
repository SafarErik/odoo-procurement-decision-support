"""Shared state: language, busy flags, guarded navigation and the one pending request."""

import json
from copy import deepcopy
from uuid import uuid4

import reflex as rx

from frontend.config import settings
from frontend.i18n import DEFAULT_LANGUAGE, LANGUAGES, tr
from frontend.planning_client import FINAL_DECISION_CONFLICT, submit_planning_request

VIEWS = ("overview", "suppliers", "plans", "scenarios", "decision", "audit")
# Bookmarks saved before P3 keep working.
VIEW_ALIASES = {"whatif": "scenarios"}


def focus(identity: str):
    """Focus an element if it is mounted; a missing target is not an error (no Reflex ref)."""
    return rx.call_script(f"document.getElementById({json.dumps(identity)})?.focus()")


class BaseMixin(rx.State, mixin=True):
    """Fields and helpers every feature needs; secrets and executable artifacts stay server-side."""

    # Hungarian by default; the browser remembers the choice.
    lang: str = rx.LocalStorage(DEFAULT_LANGUAGE, name="pdss_language", sync=True)
    error_message: str = ""
    error_target: str = ""
    is_loading: bool = False
    has_pending: bool = False
    request_key: str = ""
    recovery_json: str = ""
    notice: str = ""
    decision_conflict: bool = False
    # shortcut: recovery is session-local; copy JSON before leaving until durable recovery exists.
    _pending: dict = {}
    _pending_route: str = "/planning"
    creation_dirty: bool = False
    scenario_dirty: bool = False
    navigation_open: bool = False
    navigation_focus: str = ""
    drawer_open: bool = False
    _navigation: tuple[str, str] = ("", "")

    def _tr(self, key: str, **values) -> str:
        return tr(key, self._lang(), **values)

    def _lang(self) -> str:
        return self.lang if self.lang in LANGUAGES else DEFAULT_LANGUAGE

    @rx.event
    def set_language(self, value: str | list[str]):
        # The segmented control reports str | list[str]; only a single known language counts.
        if isinstance(value, list):
            value = value[0] if len(value) == 1 else ""
        if value not in LANGUAGES or value == self.lang:
            return
        self.lang = value
        # Re-label what is already loaded; stored cases are never re-read from Odoo or re-solved.
        return self._relabel()

    def _relabel(self):
        events = []
        for method in ("_relabel_case", "_relabel_creation", "_relabel_library"):
            event = getattr(self, method)()
            if event is not None:
                events.append(event)
        return events or None

    def _guard_navigation(self, action: str, value: str, focus_id: str = ""):
        if self.has_pending or self.is_loading:
            return None
        if self.creation_dirty or self.scenario_dirty:
            self._navigation = (action, value)
            self.navigation_focus = "workspace-menu" if self.drawer_open else focus_id
            self.drawer_open = False
            self.navigation_open = True
            return None
        return self._navigate(action, value)

    def _navigate(self, action: str, value: str):
        self.drawer_open = False
        if action == "route":
            if value == "/planning":
                self._clear_comparison_context()
            return rx.redirect(value)
        if action == "view":
            self.view = value
            if self.has_case:
                return rx.redirect(f"/planning?case_id={self.details['case_id']}&view={value}")
        elif action == "odoo-history":
            return type(self).load_odoo_history

    def _discard_drafts(self):
        self._clear_review()
        self.creation_errors = {}
        self.creation_dirty = self.scenario_dirty = False
        self.odoo_ready = False
        self.odoo_history_mode = False
        self.odoo_history_rows = []
        self._odoo_payload = {}
        self._preview = {}
        self.stress_supplier = self.stress_capacity = self.stress_quantity = self.stress_price = ""
        self.error_message = self.error_target = ""

    @rx.event
    def stay_navigation(self, opened: bool = False):
        if not opened:
            self.navigation_open = False
            self._navigation = ("", "")

    @rx.event
    def discard_navigation(self):
        if self.has_pending or self.is_loading or not self.navigation_open:
            return
        action, value = self._navigation
        # Restoring the old tab's focus would automatically select it again after Discard.
        self.navigation_focus = action + "-" + value if action == "view" else "workspace-main"
        self.navigation_open = False
        self._navigation = ("", "")
        self._discard_drafts()
        return self._navigate(action, value)

    @rx.event
    def change_drawer(self, opened: bool):
        self.drawer_open = opened

    @rx.event
    def navigate_global(self, destination: str):
        routes = {"cases": "/cases", "rfqs": "/rfqs"}
        if destination in routes:
            return self._guard_navigation("route", routes[destination], "nav-" + destination)

    def _prepare_request(self, url: str, payload: dict):
        self._pending_route = (
            self.router.url.path + ("?" + self.router.url.query if self.router.url.query else "")
            or "/planning"
        )
        self.request_key = str(uuid4())
        self._pending = {"url": url, "payload": deepcopy(payload), "key": self.request_key}
        self.recovery_json = json.dumps(self._pending, indent=2, allow_nan=False)
        self.has_pending = True
        self.decision_conflict = False
        self.error_message = ""
        self.notice = ""
        self.is_loading = True

    async def _send_pending(self, *, recovering: bool = False):
        result, error, uncertain = await submit_planning_request(
            self._pending["url"],
            self._pending["payload"],
            self._pending["key"],
            settings.api_service_token.get_secret_value(),
            lang=self._lang(),
        )
        self.decision_conflict = error == FINAL_DECISION_CONFLICT
        self.error_message = self._tr("err_decision_conflict") if self.decision_conflict else error
        self.has_pending = uncertain or (recovering and result is None)
        if not self.has_pending:
            self._pending = {}
        if result is not None:
            self._show(result)
            self.notice = self._tr(
                "notice_decided" if self.details["final_outcome"] else "notice_saved"
            )
        return result

    @rx.event
    async def recover_request(self):
        if self.is_loading or self.decision_conflict or not self.has_pending or not self._pending:
            return
        self.is_loading = True
        reviewed_creation = bool(self._review_payload)
        scenario = self._pending["url"].endswith("/scenarios")
        decision = self._pending["url"].endswith("/final-decision")
        self.error_message = ""
        yield
        try:
            saved = await self._send_pending(recovering=True)
            if saved is not None and scenario:
                await self._ensure_original()
        finally:
            self.is_loading = False
        if (
            reviewed_creation
            and self.has_case
            and not self.has_pending
            and not self._review_payload
        ):
            for event in self._creation_saved_events():
                yield event
        elif saved is not None and scenario:
            yield rx.redirect(f"/planning?case_id={self.details['case_id']}&view=scenarios")
            yield focus("scenario-result-heading")
        elif saved is not None and decision:
            yield focus("saved-decision-heading")

    @rx.event
    def focus_pending_save(self):
        if self.has_pending or self.decision_conflict:
            return focus("request-recovery-heading")
