"""Field-level source attribution kept outside the ERP-neutral planning core."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SourceAttribution:
    """Source identity and observation time for one explicitly supplied value."""

    field_name: str
    source_type: str
    source_reference: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class FieldProvenance:
    """Trace one canonical field to one observed source value."""

    canonical_path: str
    field_name: str
    source_type: str
    source_reference: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ProvenanceManifest:
    """Application-layer trace data kept outside the planning core."""

    entries: tuple[FieldProvenance, ...]
