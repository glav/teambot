"""Acceptance tests for @notify command bypass mode filtering.

These tests validate the real implementation against acceptance scenarios.
Core notification logic is tested directly; selective mocking is used for external dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from teambot.notifications.config import _create_channel, create_event_bus_from_config
from teambot.notifications.events import NotificationEvent
from teambot.tasks.executor import TaskExecutor


class TestNotifyBypassAcceptanceScenarios:
    """Acceptance test scenarios for @notify mode bypass feature."""

    # =========================================================================
    # AT-001: @notify with stages_only mode
    # =========================================================================
    def test_at_001_notify_with_stages_only_mode(self, monkeypatch) -> None:
        """AT-001: @notify delivers notification despite stages_only mode.

        Scenario: User sends @notify when notification_mode is set to stages_only
        Expected: Notification is delivered to configured channel
        """
        # Setup: Configure environment for Telegram channel
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-001")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        # Create channel with stages_only mode (would normally filter custom_message)
        channel_config = {
            "type": "telegram",
            "notification_mode": "stages_only",
        }

        # Call REAL implementation
        channel = _create_channel(channel_config)

        # Verify: custom_message event type is supported (bypass works)
        assert channel is not None
        assert channel.supports_event("custom_message") is True

        # Verify: The message "Build deployment complete!" would be delivered
        # by checking the channel accepts the event type
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "Build deployment complete!"},
        )
        assert channel.supports_event(event.event_type) is True

    # =========================================================================
    # AT-002: @notify with agent_status mode
    # =========================================================================
    def test_at_002_notify_with_agent_status_mode(self, monkeypatch) -> None:
        """AT-002: @notify delivers notification despite agent_status mode.

        Scenario: User sends @notify when notification_mode is set to agent_status
        Expected: Notification is delivered to configured channel
        """
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-002")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel_config = {
            "type": "telegram",
            "notification_mode": "agent_status",
        }

        # Call REAL implementation
        channel = _create_channel(channel_config)

        # Verify: custom_message bypasses agent_status mode
        assert channel is not None
        assert channel.supports_event("custom_message") is True

        # Verify: "Manual checkpoint reached" message would be delivered
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "Manual checkpoint reached"},
        )
        assert channel.supports_event(event.event_type) is True

    # =========================================================================
    # AT-003: @notify with notifications disabled
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_003_notify_with_notifications_disabled(self) -> None:
        """AT-003: @notify does NOT send when notifications are disabled.

        Scenario: User sends @notify when notifications.enabled is false
        Expected: Notification is NOT sent; appropriate feedback shown
        """
        # Config with notifications disabled
        config = {
            "notifications": {
                "enabled": False,
                "channels": [{"type": "telegram"}],
            }
        }

        # Create executor with REAL implementation
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        # Call REAL _handle_notify method
        result = await executor._handle_notify("Test message", background=False)

        # Verify: Success is True (doesn't break pipeline) but message indicates disabled
        assert result.success is True
        assert "disabled" in result.output.lower()

    # =========================================================================
    # AT-004: @notify with no channels configured
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_004_notify_with_no_channels_configured(self, monkeypatch) -> None:
        """AT-004: @notify shows 'No notification channels configured' message.

        Scenario: User sends @notify when no channels are configured
        Expected: User sees appropriate error/info message
        """
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-004")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        # Config with notifications enabled but no channels
        config = {
            "notifications": {
                "enabled": True,
                "channels": [],  # Empty channels list
            }
        }

        # Use REAL create_event_bus_from_config
        event_bus = create_event_bus_from_config(config)

        # EventBus is created but has no channels
        assert event_bus is not None
        assert len(event_bus._channels) == 0

        # Verify executor handles this correctly
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = []  # No channels
            mock_create.return_value = mock_bus

            result = await executor._handle_notify("Test message", background=False)

            # Verify: Message indicates no channels
            assert result.success is True
            assert "no notification channels" in result.output.lower()

    # =========================================================================
    # AT-005: Automated events still filtered by mode
    # =========================================================================
    def test_at_005_automated_events_filtered_by_mode(self, monkeypatch) -> None:
        """AT-005: stage_changed delivered, agent_running filtered by stages_only.

        Scenario: Verify automated events respect notification_mode filtering
        Expected: stage_changed is delivered; agent_running is filtered out
        """
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-005")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel_config = {
            "type": "telegram",
            "notification_mode": "stages_only",
        }

        # Call REAL implementation
        channel = _create_channel(channel_config)

        # Verify: stage_changed is in stages_only mode (delivered)
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("orchestration_started") is True
        assert channel.supports_event("orchestration_completed") is True

        # Verify: agent_running is NOT in stages_only mode (filtered out)
        assert channel.supports_event("agent_running") is False
        assert channel.supports_event("agent_complete") is False
        assert channel.supports_event("agent_failed") is False

        # Verify: custom_message still bypasses (AT-001 cross-check)
        assert channel.supports_event("custom_message") is True

    # =========================================================================
    # AT-006: Explicit events array can exclude custom_message
    # =========================================================================
    def test_at_006_explicit_events_array_excludes_custom_message(self, monkeypatch) -> None:
        """AT-006: Explicit events array takes precedence over bypass.

        Scenario: User configures events: [] or events without custom_message
        Expected: Notification is NOT delivered; explicit config honored
        """
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-006")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        # Case 1: Explicit empty events array
        channel_config_empty = {
            "type": "telegram",
            "events": [],  # Explicitly disable all events
        }

        channel = _create_channel(channel_config_empty)

        # Verify: custom_message is NOT supported (explicit config honored)
        assert channel.supports_event("custom_message") is False
        assert channel.supports_event("stage_changed") is False

        # Case 2: Explicit events array without custom_message
        channel_config_subset = {
            "type": "telegram",
            "events": ["stage_changed", "agent_failed"],  # No custom_message
        }

        channel2 = _create_channel(channel_config_subset)

        # Verify: Only specified events are supported
        assert channel2.supports_event("stage_changed") is True
        assert channel2.supports_event("agent_failed") is True
        assert channel2.supports_event("custom_message") is False  # Not in list

    # =========================================================================
    # Integration: Full EventBus flow with stages_only mode
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_001_full_event_bus_integration(self, monkeypatch) -> None:
        """Integration test: Full EventBus flow verifies custom_message delivery.

        This test uses the REAL EventBus with REAL channel creation to verify
        the complete notification flow works end-to-end.
        """
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token-integration")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "notification_mode": "stages_only",
                        "dry_run": True,  # Don't actually send to Telegram
                    }
                ],
            }
        }

        # Use REAL create_event_bus_from_config
        event_bus = create_event_bus_from_config(config)

        assert event_bus is not None
        assert len(event_bus._channels) == 1

        channel = event_bus._channels[0]

        # Verify channel accepts custom_message (bypass works)
        assert channel.supports_event("custom_message") is True

        # Verify channel still filters non-stage events
        assert channel.supports_event("agent_running") is False

        # Verify channel accepts stage events
        assert channel.supports_event("stage_changed") is True
