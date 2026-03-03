"""Token usage data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TokenUsage:
    """Token usage from a single API call.

    All fields are optional (None = unavailable).
    Uses int for display simplicity despite SDK using float.

    Attributes:
        input_tokens: Prompt/input tokens consumed.
        output_tokens: Completion/output tokens generated.
        cache_read_tokens: Tokens read from cache.
        cache_write_tokens: Tokens written to cache.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None

    @property
    def total_tokens(self) -> int | None:
        """Calculate total tokens if data available.

        Returns:
            Sum of input + output tokens, or None if both are None.
        """
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON storage.

        Returns:
            Dict with all token fields including computed total.
        """
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenUsage:
        """Deserialize from JSON dict.

        Args:
            data: Dict with token fields.

        Returns:
            TokenUsage instance.
        """
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            cache_read_tokens=data.get("cache_read_tokens"),
            cache_write_tokens=data.get("cache_write_tokens"),
        )

    @classmethod
    def from_sdk_usage(cls, sdk_usage: Any) -> TokenUsage:
        """Create from Copilot SDK Usage dataclass.

        The SDK uses float for token counts; we convert to int.

        Args:
            sdk_usage: SDK Usage object with token fields.

        Returns:
            TokenUsage instance with int values.
        """

        def to_int(value: float | None) -> int | None:
            """Convert float to int, preserving None and 0."""
            if value is None:
                return None
            return int(value)

        return cls(
            input_tokens=to_int(getattr(sdk_usage, "input_tokens", None)),
            output_tokens=to_int(getattr(sdk_usage, "output_tokens", None)),
            cache_read_tokens=to_int(getattr(sdk_usage, "cache_read_tokens", None)),
            cache_write_tokens=to_int(getattr(sdk_usage, "cache_write_tokens", None)),
        )

    def __add__(self, other: TokenUsage) -> TokenUsage:
        """Add two TokenUsage instances for aggregation.

        Handles None values gracefully - None + X = X, None + None = None.

        Args:
            other: Another TokenUsage to add.

        Returns:
            New TokenUsage with summed values.
        """

        def add_optional(a: int | None, b: int | None) -> int | None:
            """Add two optional ints, treating None as absent."""
            if a is None and b is None:
                return None
            return (a or 0) + (b or 0)

        return TokenUsage(
            input_tokens=add_optional(self.input_tokens, other.input_tokens),
            output_tokens=add_optional(self.output_tokens, other.output_tokens),
            cache_read_tokens=add_optional(self.cache_read_tokens, other.cache_read_tokens),
            cache_write_tokens=add_optional(self.cache_write_tokens, other.cache_write_tokens),
        )
