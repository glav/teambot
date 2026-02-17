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
        ValueError: If mode is not recognized or not a string
    """
    valid_modes = ", ".join(sorted(NOTIFICATION_MODES.keys()))
    if not isinstance(mode, str):
        raise ValueError(
            f"notification_mode must be a string, got {type(mode).__name__}. "
            f"Valid modes: {valid_modes}"
        )
    if mode not in NOTIFICATION_MODES:
        raise ValueError(f"Invalid notification_mode '{mode}'. Valid modes: {valid_modes}")
    return NOTIFICATION_MODES[mode]
