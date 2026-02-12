"""Tests for NotificationChannel protocol."""

from __future__ import annotations

from typing import Any

import pytest

from teambot.notifications.events import NotificationEvent
from teambot.notifications.protocol import NotificationChannel


class MockChannel:
    """Mock implementation of NotificationChannel protocol."""

    def __init__(self, name: str = "mock", enabled: bool = True):
        self._name = name
        self._enabled = enabled
        self._subscribed_events: set[str] | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def send(self, event: NotificationEvent) -> bool:
        return True

    def format(self, event: NotificationEvent) -> str:
        return f"Event: {event.event_type}"

    def supports_event(self, event_type: str) -> bool:
        if self._subscribed_events is None:
            return True
        return event_type in self._subscribed_events

    async def poll(self) -> list[dict[str, Any]] | None:
        return None


class PartialChannel:
    """Partial implementation missing required methods."""

    @property
    def name(self) -> str:
        return "partial"

    # Missing: enabled, send, format, supports_event, poll


class TestNotificationChannelProtocol:
    """Tests for NotificationChannel protocol definition."""

    def test_mock_satisfies_protocol(self) -> None:
        """Mock implementation satisfies the protocol."""
        channel = MockChannel()

        # runtime_checkable allows isinstance checks
        assert isinstance(channel, NotificationChannel)

    def test_partial_implementation_fails_isinstance(self) -> None:
        """Partial implementation does not satisfy protocol."""
        partial = PartialChannel()

        # Should fail isinstance because missing methods
        assert not isinstance(partial, NotificationChannel)

    def test_protocol_has_name_property(self) -> None:
        """Protocol requires name property."""
        channel = MockChannel(name="test-channel")
        assert channel.name == "test-channel"

    def test_protocol_has_enabled_property(self) -> None:
        """Protocol requires enabled property."""
        channel = MockChannel(enabled=False)
        assert channel.enabled is False

    @pytest.mark.asyncio
    async def test_protocol_send_method(self) -> None:
        """Protocol requires async send method."""
        channel = MockChannel()
        event = NotificationEvent(event_type="test", data={})

        result = await channel.send(event)
        assert result is True

    def test_protocol_format_method(self) -> None:
        """Protocol requires format method."""
        channel = MockChannel()
        event = NotificationEvent(event_type="stage_changed", data={})

        result = channel.format(event)
        assert "stage_changed" in result

    def test_protocol_supports_event_method(self) -> None:
        """Protocol requires supports_event method."""
        channel = MockChannel()

        assert channel.supports_event("stage_changed") is True

    @pytest.mark.asyncio
    async def test_protocol_poll_method(self) -> None:
        """Protocol requires poll method (can return None)."""
        channel = MockChannel()

        result = await channel.poll()
        assert result is None
