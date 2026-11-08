"""Strict parsing helpers shared by the API client modules and the state."""

from datetime import datetime
from typing import Any
from uuid import UUID


def is_uuid(value: Any) -> bool:
    """True only for a UUID in canonical lowercase hyphenated form (the API's identities)."""
    try:
        return str(UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def required_string(value: dict[str, Any], field: str) -> str:
    """``value[field]`` if it is a non-empty string; raises otherwise."""
    item = value[field]
    if not isinstance(item, str) or not item.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return item


def parse_datetime(value: Any) -> datetime:
    """An ISO datetime string (``Z`` allowed) as an aware datetime."""
    if not isinstance(value, str):
        raise TypeError("Expected an ISO datetime")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
