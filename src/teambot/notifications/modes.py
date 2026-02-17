"""Notification mode definitions and event groupings."""

from __future__ import annotations

from typing import Literal

NotificationMode = Literal["stages_only", "agent_status", "all"]

# Event type groupings by mode
STAGES_ONLY_EVENTS: frozenset[str] = frozenset(
    {
        "stage_changed",
        "orchestration_started",
        "orchestration_completed",
    }
)

AGENT_STATUS_EVENTS: frozenset[str] = STAGES_ONLY_EVENTS | frozenset(
    {
        "agent_running",
        "agent_complete",
        "agent_failed",
    }
)

NOTIFICATION_MODES: dict[NotificationMode, frozenset[str] | None] = {
    "stages_only": STAGES_ONLY_EVENTS,
    "agent_status": AGENT_STATUS_EVENTS,
    "all": None,  # None means no filtering
}


def resolve_notification_mode(mode: str) -> frozenset[str] | None:
    """Resolve a mode name to its event set.

    Args:
        mode: One of "stages_only", "agent_status", "all"

    Returns:
        Set of event types, or None for all events

    Raises:
        ValueError: If mode is not recognized
    """
    if mode not in NOTIFICATION_MODES:
        valid = ", ".join(sorted(NOTIFICATION_MODES.keys()))
        raise ValueError(f"Invalid notification_mode '{mode}'. Valid modes: {valid}")
    return NOTIFICATION_MODES[mode]
