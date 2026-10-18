"""Reflex HTTP orchestration composed from feature mixins; no model, Odoo or database access.

Features live in ``state_base`` (language, navigation, the one pending request),
``state_library``, ``state_creation``, ``state_case``, ``state_scenarios`` and
``state_decision``. One composed state keeps the shared busy/pending guards exact.
"""

import reflex as rx

from frontend.planning.state_base import BaseMixin
from frontend.planning.state_case import CaseMixin
from frontend.planning.state_creation import CreationMixin
from frontend.planning.state_decision import DecisionMixin
from frontend.planning.state_library import LibraryMixin
from frontend.planning.state_scenarios import ScenarioMixin


class PlanningState(
    BaseMixin, LibraryMixin, CreationMixin, CaseMixin, ScenarioMixin, DecisionMixin, rx.State
):
    """HTTP-client state; secrets and executable artifacts stay server-side."""
