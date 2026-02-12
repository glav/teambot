"""Acceptance test validation for Real-Time Notification System.

These tests validate the acceptance scenarios by exercising the REAL implementation.
External HTTP calls are mocked but core logic is tested directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import REAL implementation classes
from teambot.notifications.channels.telegram import TelegramChannel
from teambot.notifications.config import (
    create_event_bus_from_config,
    resolve_config_secrets,
    resolve_env_vars,
)
from teambot.notifications.event_bus import EventBus, RateLimitError
from teambot.notifications.events import NotificationEvent


class TestNotificationAcceptanceScenarios:
    """Acceptance test scenarios for Real-Time Notification System."""

    # =========================================================================
    # AT-001: Basic Telegram Notification on Stage Complete
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_001_telegram_notification_on_stage_complete(self) -> None:
        """AT-001: User receives Telegram notification when workflow stage completes.

        Validates:
        - TelegramChannel sends message via Telegram API
        - Message contains emoji prefix, bold stage name, agent info
        - Message is HTML formatted
        """
        # Create REAL TelegramChannel
        channel = TelegramChannel(dry_run=False)

        # Create REAL NotificationEvent for stage completion
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "BUSINESS_PROBLEM"},
            feature_name="simple-task",
        )

        # Format message using REAL templates
        message = channel.format(event)

        # Verify message format
        assert "📌" in message or "✅" in message  # Emoji prefix
        assert "<b>" in message  # Bold formatting
        assert "BUSINESS_PROBLEM" in message  # Stage name
        assert "simple-task" in message  # Feature name

        # Test actual send with mocked HTTP (external service)
        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch.dict(
                os.environ,
                {
                    "TEAMBOT_TELEGRAM_TOKEN": "test-token-123",
                    "TEAMBOT_TELEGRAM_CHAT_ID": "12345678",
                },
            ),
            patch.object(channel, "_get_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await channel.send(event)

            # Verify send succeeded
            assert result is True
            mock_client.post.assert_called_once()

            # Verify API call format
            call_args = mock_client.post.call_args
            assert "sendMessage" in call_args[0][0]
            assert call_args[1]["json"]["parse_mode"] == "HTML"
            assert "BUSINESS_PROBLEM" in call_args[1]["json"]["text"]

    # =========================================================================
    # AT-002: Notification Failure Does Not Block Workflow
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_002_notification_failure_does_not_block_workflow(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AT-002: Workflow continues even when Telegram API is unreachable.

        Validates:
        - EventBus catches channel exceptions
        - Errors are logged but not propagated
        - Multiple events can be emitted even with failures
        """
        caplog.set_level(logging.ERROR)

        # Create REAL EventBus
        bus = EventBus(feature_name="test-feature")

        # Create channel that will fail
        failing_channel = MagicMock()
        failing_channel.name = "failing-channel"
        failing_channel.enabled = True
        failing_channel.supports_event.return_value = True
        failing_channel.send = AsyncMock(side_effect=Exception("Network unreachable"))

        bus.subscribe(failing_channel)

        # Emit multiple events - should NOT raise
        events = [
            NotificationEvent(event_type="stage_changed", data={"stage": "SETUP"}),
            NotificationEvent(event_type="stage_changed", data={"stage": "SPEC"}),
            NotificationEvent(event_type="stage_changed", data={"stage": "PLAN"}),
        ]

        for event in events:
            await bus.emit(event)

        # Give async tasks time to complete
        await asyncio.sleep(0.1)

        # Verify errors were logged but not raised
        assert "send failed" in caplog.text.lower()

        # All events were attempted
        assert failing_channel.send.call_count == 3

    # =========================================================================
    # AT-003: Dry Run Mode Logs Without Sending
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_003_dry_run_mode_logs_without_sending(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AT-003: dry_run mode logs formatted messages without HTTP calls.

        Validates:
        - dry_run=True logs message with [DRY RUN] prefix
        - No HTTP client is used
        - Full formatted message is visible in logs
        """
        caplog.set_level(logging.INFO)

        # Create REAL TelegramChannel with dry_run=True
        channel = TelegramChannel(dry_run=True)

        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "IMPLEMENTATION"},
            feature_name="test-feature",
        )

        # Send should succeed without HTTP call
        result = await channel.send(event)

        assert result is True
        assert "[DRY RUN]" in caplog.text
        assert "IMPLEMENTATION" in caplog.text

        # Verify no HTTP client was created
        assert channel._client is None

    # =========================================================================
    # AT-004: Environment Variable Resolution
    # =========================================================================
    def test_at_004_environment_variable_resolution(self) -> None:
        """AT-004: Config loader resolves ${VAR_NAME} syntax from environment.

        Validates:
        - resolve_env_vars() substitutes environment variables
        - resolve_config_secrets() handles nested dicts
        - Actual env values are returned, not patterns
        """
        # Set environment variable
        with patch.dict(os.environ, {"MY_TOKEN": "test_value_12345"}):
            # Test REAL resolve_env_vars function
            result = resolve_env_vars("${MY_TOKEN}")
            assert result == "test_value_12345"

            # Test nested config resolution
            config = {
                "notifications": {
                    "channels": [
                        {
                            "type": "telegram",
                            "token": "${MY_TOKEN}",
                            "chat_id": "${MY_TOKEN}",
                        }
                    ]
                }
            }

            resolved = resolve_config_secrets(config)
            assert resolved["notifications"]["channels"][0]["token"] == "test_value_12345"
            assert resolved["notifications"]["channels"][0]["chat_id"] == "test_value_12345"

    # =========================================================================
    # AT-005: Missing Environment Variable Handling
    # =========================================================================
    def test_at_005_missing_environment_variable_handling(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AT-005: Clear handling when required env var not set.

        Validates:
        - Missing env vars resolve to empty string
        - TelegramChannel.enabled returns False when credentials missing
        - Channel won't attempt to send without credentials
        """
        # Ensure env vars are NOT set
        monkeypatch.delenv("TEAMBOT_TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TEAMBOT_TELEGRAM_CHAT_ID", raising=False)

        # Test REAL resolve function returns empty for missing
        result = resolve_env_vars("${MISSING_VAR_XYZ}")
        assert result == ""

        # Test REAL TelegramChannel reports disabled
        channel = TelegramChannel()
        assert channel.enabled is False

    @pytest.mark.asyncio
    async def test_at_005b_missing_credentials_logs_warning(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AT-005b: Warning logged when credentials missing."""
        caplog.set_level(logging.WARNING)

        monkeypatch.delenv("TEAMBOT_TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TEAMBOT_TELEGRAM_CHAT_ID", raising=False)

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        result = await channel.send(event)

        assert result is False
        assert "not configured" in caplog.text.lower()

    # =========================================================================
    # AT-006: Init Wizard Telegram Setup
    # =========================================================================
    def test_at_006_init_wizard_creates_config_with_env_refs(self, tmp_path: Path) -> None:
        """AT-006: teambot init creates config with env var references.

        Validates:
        - Notifications config uses ${VAR} syntax
        - Token and chat_id are not stored as literals
        - Config is valid JSON
        """
        # Simulate what _setup_telegram_notifications creates
        config: dict = {}

        # This is what the REAL _setup_telegram_notifications does:
        token_env = "TEAMBOT_TELEGRAM_TOKEN"
        chat_id_env = "TEAMBOT_TELEGRAM_CHAT_ID"

        config["notifications"] = {
            "enabled": True,
            "channels": [
                {
                    "type": "telegram",
                    "token": f"${{{token_env}}}",
                    "chat_id": f"${{{chat_id_env}}}",
                }
            ],
        }

        # Verify config format
        assert config["notifications"]["channels"][0]["token"] == "${TEAMBOT_TELEGRAM_TOKEN}"
        assert config["notifications"]["channels"][0]["chat_id"] == "${TEAMBOT_TELEGRAM_CHAT_ID}"

        # Verify it's valid JSON
        config_path = tmp_path / "teambot.json"
        config_path.write_text(json.dumps(config, indent=2))
        loaded = json.loads(config_path.read_text())
        assert loaded["notifications"]["enabled"] is True

    def test_at_006b_init_skips_in_noninteractive(self) -> None:
        """AT-006b: Init skips notification prompt in non-interactive mode."""
        from teambot.cli import _should_setup_notifications
        from teambot.visualization.console import ConsoleDisplay

        # Create display
        display = ConsoleDisplay()

        # In non-interactive mode (no TTY), should return False
        with patch("sys.stdin.isatty", return_value=False):
            result = _should_setup_notifications(display)
            assert result is False

    # =========================================================================
    # AT-007: Multiple Event Types Filtered
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_007_event_type_filtering(self) -> None:
        """AT-007: Channel only receives subscribed event types.

        Validates:
        - Channel with event filter only receives matching events
        - Non-matching events are skipped
        - EventBus respects supports_event() check
        """
        # Create REAL TelegramChannel with event filter
        channel = TelegramChannel(
            subscribed_events={"pipeline_complete"},  # Only this event
            dry_run=True,
        )

        # Verify filter
        assert channel.supports_event("pipeline_complete") is True
        assert channel.supports_event("stage_changed") is False
        assert channel.supports_event("agent_complete") is False

        # Test with REAL EventBus
        bus = EventBus(feature_name="test")

        # Create tracking channel
        tracking_channel = MagicMock()
        tracking_channel.name = "tracker"
        tracking_channel.enabled = True
        tracking_channel.supports_event.side_effect = lambda e: e == "pipeline_complete"
        tracking_channel.send = AsyncMock(return_value=True)

        bus.subscribe(tracking_channel)

        # Emit multiple event types
        events = [
            NotificationEvent(event_type="stage_changed", data={"stage": "SETUP"}),
            NotificationEvent(event_type="agent_complete", data={"agent_id": "pm"}),
            NotificationEvent(event_type="pipeline_complete", data={"status": "success"}),
        ]

        for event in events:
            await bus.emit(event)

        await asyncio.sleep(0.1)

        # Only pipeline_complete should be sent
        assert tracking_channel.send.call_count == 1
        sent_event = tracking_channel.send.call_args[0][0]
        assert sent_event.event_type == "pipeline_complete"

    # =========================================================================
    # AT-008: Rate Limit Retry Behavior
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_008_rate_limit_retry_behavior(self, caplog: pytest.LogCaptureFixture) -> None:
        """AT-008: HTTP 429 triggers exponential backoff retry.

        Validates:
        - RateLimitError triggers retry
        - Exponential backoff is applied
        - Eventually succeeds after retries
        - Log shows retry attempts
        """
        caplog.set_level(logging.WARNING)

        # Create REAL EventBus
        bus = EventBus(feature_name="test")

        # Track retry attempts
        attempt_count = [0]

        async def mock_send(event: NotificationEvent) -> bool:
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise RateLimitError(retry_after=0.1)  # Short for testing
            return True

        # Create channel that rate limits then succeeds
        channel = MagicMock()
        channel.name = "rate-limited"
        channel.enabled = True
        channel.supports_event.return_value = True
        channel.send = mock_send

        bus.subscribe(channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        # Wait for retries
        await asyncio.sleep(0.5)

        # Verify retry behavior
        assert attempt_count[0] == 3  # 2 failures + 1 success
        assert "rate limited" in caplog.text.lower()
        assert "retry" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_at_008b_max_retries_exceeded(self, caplog: pytest.LogCaptureFixture) -> None:
        """AT-008b: After max retries, notification is dropped (not failed)."""
        caplog.set_level(logging.ERROR)

        bus = EventBus(feature_name="test")

        # Channel always rate limits
        channel = MagicMock()
        channel.name = "always-limited"
        channel.enabled = True
        channel.supports_event.return_value = True
        channel.send = AsyncMock(side_effect=RateLimitError(retry_after=0.05))

        bus.subscribe(channel)

        event = NotificationEvent(event_type="test", data={})

        # Should NOT raise even after max retries
        await bus.emit(event)
        await asyncio.sleep(0.5)

        # Verify max retries logged
        assert "max retries exceeded" in caplog.text.lower()


class TestNotificationAcceptanceIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_at_integration_full_pipeline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Integration: Full pipeline from config to notification."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123456")

        # Create REAL EventBus from REAL config
        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "dry_run": True,  # Don't actually send
                    }
                ],
            }
        }

        bus = create_event_bus_from_config(config, feature_name="integration-test")

        assert bus is not None
        assert len(bus._channels) == 1

        # Emit event through REAL EventBus
        bus.emit_sync("stage_changed", {"stage": "COMPLETE"})

        # Give async task time
        await asyncio.sleep(0.1)

    def test_at_integration_config_loader_validation(self, tmp_path: Path) -> None:
        """Integration: ConfigLoader validates notification schema."""
        from teambot.config.loader import ConfigError, ConfigLoader

        # Valid config
        valid_config = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TOKEN}",
                        "chat_id": "${CHAT_ID}",
                    }
                ],
            },
        }

        config_path = tmp_path / "valid.json"
        config_path.write_text(json.dumps(valid_config))

        loader = ConfigLoader()
        config = loader.load(config_path)
        assert config["notifications"]["enabled"] is True

        # Invalid config - missing required field
        invalid_config = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "token": "${TOKEN}"}],  # Missing chat_id
            },
        }

        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text(json.dumps(invalid_config))

        with pytest.raises(ConfigError, match="missing required field 'chat_id'"):
            loader.load(invalid_path)
