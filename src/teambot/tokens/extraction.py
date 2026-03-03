"""Token extraction from SDK event data."""

from __future__ import annotations

import logging
from typing import Any

from teambot.tokens.models import TokenUsage

logger = logging.getLogger(__name__)


def extract_tokens_from_event_data(event_data: Any) -> TokenUsage:
    """Extract token usage from SDK event data.

    Handles missing attributes gracefully by returning None for each field.
    Converts float values (SDK format) to int.

    Args:
        event_data: SDK event.data object with potential token fields.

    Returns:
        TokenUsage with extracted values (may have None fields).
    """

    def get_int(attr_name: str) -> int | None:
        """Get attribute as int, handling missing/None."""
        value = getattr(event_data, attr_name, None)
        if value is None:
            return None
        return int(value)

    usage = TokenUsage(
        input_tokens=get_int("input_tokens"),
        output_tokens=get_int("output_tokens"),
        cache_read_tokens=get_int("cache_read_tokens"),
        cache_write_tokens=get_int("cache_write_tokens"),
    )

    logger.debug(f"Extracted token usage: input={usage.input_tokens}, output={usage.output_tokens}")

    return usage
