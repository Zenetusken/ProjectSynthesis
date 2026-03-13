"""Shared SSE event formatting for streaming endpoints."""

import json
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


def _default_serializer(obj: object) -> str:
    """Fallback JSON serializer for SSE payloads."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Exception):
        return str(obj)
    return repr(obj)


def sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event with safe JSON serialization.

    Uses a fallback serializer so that non-serializable values (datetimes,
    exceptions, etc.) never crash the stream silently.
    """
    try:
        payload = json.dumps(data, default=_default_serializer)
    except Exception as e:
        logger.error("SSE serialization failed for event %s: %s", event_type, e)
        payload = json.dumps({"error": f"Serialization error: {e}"})
    return f"event: {event_type}\ndata: {payload}\n\n"
