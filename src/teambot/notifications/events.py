"""Notification event data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NotificationEvent:
    """Event data for notifications.

    Attributes:
        event_type: Type of event (e.g., "stage_changed", "agent_failed")
        data: Event-specific data dictionary
        timestamp: When the event occurred
        stage: Current workflow stage (optional)
        agent: Agent ID if applicable (optional)
        feature_name: Feature/objective name for context (optional)
    """

    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    stage: str | None = None
    agent: str | None = None
    feature_name: str | None = None
