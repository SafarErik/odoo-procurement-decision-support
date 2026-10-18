"""Strict parsing helpers shared by the HTTP clients."""

from datetime import datetime
from typing import Any


def required_string(value: dict[str, Any], field: str) -> str:
    item = value[field]
    if not isinstance(item, str) or not item.strip():
        raise TypeError(f"Expected a non-empty string for {field}")
    return item


def parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise TypeError("Expected an ISO datetime")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
