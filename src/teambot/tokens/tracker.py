"""Token usage tracker for aggregation."""

from __future__ import annotations

from typing import Any

from teambot.tokens.models import TokenUsage


class TokenTracker:
    """Tracks and aggregates token usage across tasks.

    Maintains running totals by agent, by stage, and overall.
    Designed for both orchestration runs and interactive sessions.

    Attributes:
        _by_agent: Usage aggregated by agent_id.
        _by_stage: Usage aggregated by workflow stage.
        _total: Running total across all recorded usage.
        _warning_logged: Flag to prevent duplicate warnings.
    """

    def __init__(self) -> None:
        """Initialize empty tracker."""
        self._by_agent: dict[str, TokenUsage] = {}
        self._by_stage: dict[str, TokenUsage] = {}
        self._total: TokenUsage = TokenUsage()
        self._warning_logged: bool = False

    def record(
        self,
        usage: TokenUsage | None,
        agent_id: str,
        stage: str | None = None,
    ) -> None:
        """Record token usage from a task execution.

        Args:
            usage: TokenUsage from the task, or None if unavailable.
            agent_id: ID of the agent that executed the task.
            stage: Optional workflow stage name.
        """
        if usage is None:
            return

        # Update agent aggregation
        if agent_id in self._by_agent:
            self._by_agent[agent_id] = self._by_agent[agent_id] + usage
        else:
            self._by_agent[agent_id] = usage

        # Update stage aggregation (only if stage provided)
        if stage is not None:
            if stage in self._by_stage:
                self._by_stage[stage] = self._by_stage[stage] + usage
            else:
                self._by_stage[stage] = usage

        # Update total
        self._total = self._total + usage

    def get_total(self) -> TokenUsage:
        """Get total token usage across all recorded tasks.

        Returns:
            TokenUsage with grand totals, or empty if nothing recorded.
        """
        return self._total

    def get_by_agent(self) -> dict[str, TokenUsage]:
        """Get token usage aggregated by agent ID.

        Returns:
            Dict mapping agent_id to their total TokenUsage.
        """
        return self._by_agent.copy()

    def get_by_stage(self) -> dict[str, TokenUsage]:
        """Get token usage aggregated by workflow stage.

        Returns:
            Dict mapping stage name to total TokenUsage.
        """
        return self._by_stage.copy()

    def reset(self) -> None:
        """Clear all recorded data.

        Useful for resetting between sessions or runs.
        """
        self._by_agent.clear()
        self._by_stage.clear()
        self._total = TokenUsage()
        self._warning_logged = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize tracker state for persistence.

        Returns:
            Dict suitable for JSON serialization.
        """
        return {
            "schema_version": "1.0",
            "total": self._total.to_dict(),
            "by_agent": {k: v.to_dict() for k, v in self._by_agent.items()},
            "by_stage": {k: v.to_dict() for k, v in self._by_stage.items()},
        }

    def should_warn_unavailable(self) -> bool:
        """Check if warning about unavailable data should be logged.

        Returns True the first time called, False on subsequent calls.
        This prevents repeated warnings when token data is unavailable.

        Returns:
            True if warning should be logged, False otherwise.
        """
        if not self._warning_logged:
            self._warning_logged = True
            return True
        return False
