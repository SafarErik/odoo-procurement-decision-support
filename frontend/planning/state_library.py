"""Saved-case library: bounded pages, filters and on-demand scenarios."""

from typing import Any
from uuid import UUID

import reflex as rx

from frontend.config import settings
from frontend.planning.state_base import focus
from frontend.planning_library_client import fetch_library, library_row


class LibraryMixin(rx.State, mixin=True):
    library_rows: list[dict[str, str]] = []
    library_children: list[dict[str, str]] = []
    library_origin: str = "all"
    library_status: str = "all"
    library_search: str = ""
    library_cursor: str = ""
    children_cursor: str = ""
    expanded_case: str = ""
    selected_library_case: str = ""
    library_error: str = ""
    children_error: str = ""
    library_loading: bool = False
    children_loading: bool = False
    library_loaded: bool = False
    _library_params: dict = {}
    _library_raw: list = []
    _children_raw: list = []
    # Saved scenarios of the open base case (Scenarios tab); same read-only GET as the library.
    base_scenarios: list[dict[str, str]] = []
    base_scenarios_cursor: str = ""
    base_scenarios_error: str = ""
    base_scenarios_loading: bool = False
    base_scenarios_case: str = ""
    _base_scenarios_raw: list = []

    def _relabel_library(self):
        try:
            self.library_rows = [library_row(i, self._lang()) for i in self._library_raw]
            self.library_children = [library_row(i, self._lang()) for i in self._children_raw]
            self.base_scenarios = [library_row(i, self._lang()) for i in self._base_scenarios_raw]
        except (ValueError, TypeError, KeyError, ArithmeticError):
            self.library_rows = self.library_children = self.base_scenarios = []

    @rx.var
    def library_selection(self) -> dict[str, str]:
        return next(
            (r for r in self.library_rows if r["case_id"] == self.selected_library_case),
            self.library_rows[0] if self.library_rows else {},
        )

    @rx.event
    def select_library_case(self, case_id: str):
        if any(r["case_id"] == case_id for r in self.library_rows):
            self.selected_library_case = case_id

    @rx.event
    def open_library(self):
        return self.navigate_global("cases")

    @rx.event
    def open_saved_case(self, case_id: str, view: str = "overview"):
        try:
            if str(UUID(case_id)) != case_id:
                return
        except (ValueError, TypeError, AttributeError):
            return
        view = view if view in ("overview", "scenarios", "decision") else "overview"
        return self._guard_navigation("route", f"/planning?case_id={case_id}&view={view}", "")

    @rx.event
    def new_comparison(self):
        return self._guard_navigation("route", "/rfqs", "new-comparison")

    @rx.event
    async def library_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        async for event in self.refresh_library():
            yield event

    @rx.event
    async def set_library_filter(self, field: str, value: str):
        allowed = {
            "origin": ("all", "odoo", "demo"),
            "status": ("all", "draft", "approved", "no_award"),
        }
        if field in allowed and value in allowed[field]:
            setattr(self, "library_" + field, value)
            async for event in self.refresh_library():
                yield event

    @rx.event
    async def refresh_library(self, form_data: dict[str, Any] | None = None):
        if self.library_loading or self.has_pending or self.is_loading:
            return
        if form_data is not None:
            self.library_origin = form_data.get("origin", self.library_origin)
            self.library_status = form_data.get("status", self.library_status)
            self.library_search = str(form_data.get("q", "")).strip()
        self._library_params = {
            "origin": self.library_origin,
            "status": self.library_status,
            "q": self.library_search,
        }
        self.expanded_case = self.children_cursor = self.children_error = ""
        self.library_children = []
        self._children_raw = []
        async for event in self._load_library_page(""):
            yield event

    @rx.event
    async def next_library_page(self):
        if self.library_cursor and not self.library_loading:
            self.expanded_case = ""
            self.library_children = []
            self._children_raw = []
            async for event in self._load_library_page(self.library_cursor):
                yield event
            yield focus("library-heading")

    async def _load_library_page(self, cursor):
        self.library_loading = True
        self.library_error = self.library_cursor = ""
        self.library_rows = []
        self._library_raw = []
        yield
        try:
            params = dict(self._library_params)
            if cursor:
                params["cursor"] = cursor
            page, self.library_error = await fetch_library(
                settings.planning_cases_url,
                settings.api_service_token.get_secret_value(),
                params,
                lang=self._lang(),
            )
            self.library_loaded = True
            if page is not None:
                self.library_rows, self.library_cursor = page["items"], page["next_cursor"]
                self._library_raw = page["raw"]
        finally:
            self.library_loading = False

    @rx.event
    async def expand_scenarios(self, case_id: str, more: bool = False):
        if self.children_loading or self.library_loading or self.has_pending or self.is_loading:
            return
        if case_id == self.expanded_case and not more:
            self.expanded_case = ""
            self.library_children = []
            self._children_raw = []
            return
        cursor = self.children_cursor if more and case_id == self.expanded_case else ""
        self.expanded_case = case_id
        self.selected_library_case = case_id
        self.library_children = []
        self._children_raw = []
        self.children_loading = True
        self.children_error = self.children_cursor = ""
        yield
        try:
            params = {"origin": self._library_params.get("origin", "all")}
            if cursor:
                params["cursor"] = cursor
            page, self.children_error = await fetch_library(
                f"{settings.planning_cases_url}/{case_id}/scenarios",
                settings.api_service_token.get_secret_value(),
                params,
                lang=self._lang(),
            )
            if page is not None:
                self.library_children, self.children_cursor = page["items"], page["next_cursor"]
                self._children_raw = page["raw"]
        finally:
            self.children_loading = False

    def _clear_base_scenarios(self):
        self.base_scenarios = []
        self._base_scenarios_raw = []
        self.base_scenarios_cursor = self.base_scenarios_error = self.base_scenarios_case = ""

    @rx.event
    async def load_base_scenarios(self, more: bool = False):
        """Read-only GET of the open base case's saved scenarios; never re-reads Odoo or solves."""
        case_id = self.details.get("case_id", "")
        if (
            self.base_scenarios_loading
            or not self.has_case
            or self.details.get("parent_id") != "Base case"
            or (more and (case_id != self.base_scenarios_case or not self.base_scenarios_cursor))
        ):
            return
        cursor = self.base_scenarios_cursor if more else ""
        if not more:
            self._clear_base_scenarios()
        self.base_scenarios_case = case_id
        self.base_scenarios_loading = True
        self.base_scenarios_error = ""
        yield
        try:
            page, error = await fetch_library(
                f"{settings.planning_cases_url}/{case_id}/scenarios",
                settings.api_service_token.get_secret_value(),
                {"cursor": cursor} if cursor else {},
                lang=self._lang(),
            )
            # Another case may have been opened while the page was on its way.
            if self.details.get("case_id") != case_id:
                return
            self.base_scenarios_error = self._tr("err_base_scenarios") if error else ""
            if page is not None:
                self.base_scenarios = self.base_scenarios + page["items"]
                self._base_scenarios_raw = self._base_scenarios_raw + page["raw"]
                self.base_scenarios_cursor = page["next_cursor"]
        finally:
            self.base_scenarios_loading = False
