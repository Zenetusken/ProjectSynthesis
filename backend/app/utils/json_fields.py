"""Shared helper for parsing JSON-as-TEXT ORM columns.

Used across feedback, adaptation, refinement, and optimization services
to avoid duplicating the same try/except JSON parse pattern.
"""

from __future__ import annotations

import json
import logging
from typing import Any, overload

logger = logging.getLogger(__name__)


@overload
def parse_json_column(raw: str | dict | list | None, default: dict) -> dict: ...


@overload
def parse_json_column(raw: str | dict | list | None, default: list) -> list: ...


@overload
def parse_json_column(raw: str | dict | list | None, default: None = None) -> Any: ...


def parse_json_column(
    raw: str | dict | list | None,
    default: Any = None,
) -> Any:
    """Parse a JSON-as-TEXT column value, returning *default* on failure.

    If *raw* is already a dict/list it is returned as-is.
    If *raw* is a non-empty string it is JSON-decoded.
    Otherwise *default* is returned.
    """
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str) or not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default
