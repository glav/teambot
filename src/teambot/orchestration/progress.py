"""Progress callback utilities for orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from teambot.ui.agent_state import AgentStatusManager


def create_progress_callback(
    status_manager: AgentStatusManager,
    on_stage: Callable[[str], None] | None = None,
    on_time: Callable[[str, str], None] | None = None,
) -> Callable[[str, Any], None]:
    """Create progress callback for orchestration.

    Args:
        status_manager: AgentStatusManager for agent state updates
        on_stage: Callback for stage changes
        on_time: Callback for time updates (elapsed, remaining)

    Returns:
        Progress callback function
    """

    def on_progress(event_type: str, data: Any) -> None:
        if event_type == "agent_running":
            status_manager.set_running(data["agent_id"], data.get("task"))
        elif event_type == "agent_streaming":
            status_manager.set_streaming(data["agent_id"])
        elif event_type == "agent_complete":
            status_manager.set_completed(data["agent_id"])
        elif event_type == "agent_failed":
            status_manager.set_failed(data["agent_id"])
        elif event_type == "agent_cancelled":
            status_manager.set_idle(data["agent_id"])
        elif event_type == "agent_idle":
            status_manager.set_idle(data["agent_id"])
        elif event_type == "stage_changed":
            if on_stage:
                on_stage(data["stage"])
        elif event_type == "time_update":
            if on_time:
                on_time(data["elapsed"], data["remaining"])
        # Parallel group events
        elif event_type == "parallel_group_start":
            # Parallel group starting - update all stages in the group
            for stage in data.get("stages", []):
                if on_stage:
                    on_stage(f"parallel:{stage}")
        elif event_type == "parallel_stage_start":
            # Individual stage within parallel group starting
            status_manager.set_running(data.get("agent", "builder-1"), data.get("stage", "unknown"))
        elif event_type == "parallel_stage_complete":
            # Individual stage within parallel group completed
            status_manager.set_completed(data.get("agent", "builder-1"))
        elif event_type == "parallel_stage_failed":
            # Individual stage within parallel group failed
            status_manager.set_failed(data.get("agent", "builder-1"))
        elif event_type == "parallel_group_complete":
            # All stages in parallel group completed
            pass  # Group completion handled at higher level

    return on_progress
