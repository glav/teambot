"""Shared fixtures for notification tests."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.notifications.events import NotificationEvent


@pytest.fixture
def sample_event() -> NotificationEvent:
    """Create a sample notification event."""
    return NotificationEvent(
        event_type="stage_changed",
        data={"stage": "IMPLEMENTATION"},
        timestamp=datetime(2026, 2, 11, 12, 0, 0),
        feature_name="test-feature",
    )


@pytest.fixture
def mock_channel() -> MagicMock:
    """Create a mock notification channel."""
    channel = MagicMock()
    channel.name = "test-channel"
    channel.enabled = True
    channel.supports_event.return_value = True
    channel.send = AsyncMock(return_value=True)
    channel.format.return_value = "Formatted message"
    return channel


@pytest.fixture
def disabled_channel() -> MagicMock:
    """Create a disabled mock channel."""
    channel = MagicMock()
    channel.name = "disabled-channel"
    channel.enabled = False
    channel.supports_event.return_value = True
    channel.send = AsyncMock(return_value=True)
    return channel
