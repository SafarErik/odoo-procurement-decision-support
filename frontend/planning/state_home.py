"""State of the Home page: its two bounded lists, "awaiting decision" (drafts) and
"recently saved", each read with its own GET and its own error."""

import asyncio

import reflex as rx

from frontend.api import library
from frontend.api.library import library_row

HOME_LIMIT = 5  # rows per Home list; Home never shows totals it did not read


class HomeMixin(rx.State, mixin=True):
    home_pending: list[dict[str, str]] = []
    home_recent: list[dict[str, str]] = []
    home_pending_error: str = ""
    home_recent_error: str = ""
    home_loading: bool = False
    _home_pending_raw: list = []
    _home_recent_raw: list = []

    def _relabel_home(self):
        try:
            self.home_pending = [library_row(i, self._lang()) for i in self._home_pending_raw]
            self.home_recent = [library_row(i, self._lang()) for i in self._home_recent_raw]
        except (ValueError, TypeError, KeyError, ArithmeticError):
            self.home_pending = self.home_recent = []

    @rx.event
    async def home_on_load(self):
        if self.has_pending or self.is_loading:
            yield rx.redirect(self._pending_route)
            return
        if self.home_loading:
            return
        self.home_loading = True
        yield
        try:
            (pending, pending_error), (recent, recent_error) = await asyncio.gather(
                library.fetch_library({"status": "draft", "limit": HOME_LIMIT}, lang=self._lang()),
                library.fetch_library({"status": "all", "limit": HOME_LIMIT}, lang=self._lang()),
            )
            self.home_pending_error, self.home_recent_error = pending_error, recent_error
            self._home_pending_raw = pending["raw"] if pending else []
            self._home_recent_raw = recent["raw"] if recent else []
            self.home_pending = [library_row(i, self._lang()) for i in self._home_pending_raw]
            self.home_recent = [library_row(i, self._lang()) for i in self._home_recent_raw]
        finally:
            self.home_loading = False
