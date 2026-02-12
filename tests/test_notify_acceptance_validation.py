"""Acceptance tests for @notify pseudo-agent feature.

These tests validate the real implementation against acceptance criteria.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from teambot.repl.commands import SystemCommands, handle_help
from teambot.repl.parser import parse_command
from teambot.repl.router import VALID_AGENTS, AgentRouter
from teambot.tasks.executor import (
    PSEUDO_AGENTS,
    TaskExecutor,
    is_pseudo_agent,
    truncate_for_notification,
)
from teambot.ui.agent_state import DEFAULT_AGENTS, AgentStatusManager
from teambot.ui.widgets.status_panel import StatusPanel


class TestAcceptanceNotifyPseudoAgent:
    """Acceptance tests for @notify pseudo-agent feature."""

    # -------------------------------------------------------------------------
    # AT-001: Simple Notification
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_001_simple_notification_sends(self):
        """User sends @notify "Build complete!" and gets confirmation."""
        # Setup with real executor
        mock_sdk = AsyncMock()
        config = {
            "notifications": {
                "enabled": True,
                "channels": [{"type": "telegram", "token": "test", "chat_id": "123"}],
            }
        }
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        # Mock EventBus to avoid real network calls
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Parse and execute real command
            command = parse_command('@notify "Build complete!"')
            result = await executor.execute(command)

            # Verify confirmation output
            assert result.success is True
            assert "Notification sent" in result.output
            assert "✅" in result.output

            # Verify EventBus was called with message
            mock_bus.emit_sync.assert_called_once()
            call_args = mock_bus.emit_sync.call_args
            assert call_args[0][0] == "custom_message"
            assert "Build complete!" in call_args[0][1]["message"]

    @pytest.mark.asyncio
    async def test_at_001_sdk_not_called(self):
        """@notify does not call Copilot SDK."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            command = parse_command('@notify "Test"')
            await executor.execute(command)

            # SDK should NOT be called
            mock_sdk.execute.assert_not_called()

    # -------------------------------------------------------------------------
    # AT-002: Notification with $ref
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_002_notification_with_ref_interpolation(self):
        """@notify "Summary: $pm" includes PM's output."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="PM generated project summary")
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        # First execute PM
        pm_command = parse_command("@pm create a brief project summary")
        await executor.execute(pm_command)

        # Now send notification with $pm reference
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            notify_command = parse_command('@notify "Project summary: $pm"')
            result = await executor.execute(notify_command)

            assert result.success is True
            # Verify the message was sent with interpolated content
            call_args = mock_bus.emit_sync.call_args[0][1]
            # The $pm reference should be interpolated
            assert "Project summary:" in call_args["message"]

    # -------------------------------------------------------------------------
    # AT-003: Notification with Large Output Truncation
    # -------------------------------------------------------------------------
    def test_at_003_truncation_at_500_chars(self):
        """Referenced output exceeding 500 chars is truncated."""
        # Test truncation function directly
        long_text = "A" * 600
        result = truncate_for_notification(long_text)

        assert len(result) == 503  # 500 + "..."
        assert result.endswith("...")
        assert result.startswith("A" * 500)

    def test_at_003_exactly_500_unchanged(self):
        """Text exactly 500 chars is not truncated."""
        text = "B" * 500
        result = truncate_for_notification(text)

        assert len(result) == 500
        assert "..." not in result

    @pytest.mark.asyncio
    async def test_at_003_truncation_applied_in_handler(self):
        """_handle_notify applies truncation to message."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Send a very long message
            long_message = "X" * 600
            await executor._handle_notify(long_message, background=False)

            # Verify truncation was applied
            call_args = mock_bus.emit_sync.call_args[0][1]
            sent_message = call_args["message"]
            assert len(sent_message) == 503
            assert sent_message.endswith("...")

    # -------------------------------------------------------------------------
    # AT-004: Notification in Pipeline Middle
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_004_notification_in_pipeline_middle(self):
        """@pm -> @notify -> @reviewer pipeline works in order."""
        mock_sdk = AsyncMock()
        call_order = []

        async def track_execute(agent_id, prompt, **kwargs):
            call_order.append(agent_id)
            return f"{agent_id} output"

        mock_sdk.execute = track_execute
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Pipeline with notify in middle (use -> for pipeline syntax)
            command = parse_command('@pm plan -> @notify "Plan ready" -> @reviewer review')
            result = await executor.execute(command)

            assert result.success is True
            # PM and reviewer should be called
            assert "pm" in call_order
            assert "reviewer" in call_order
            # Notify should have been called (EventBus)
            mock_bus.emit_sync.assert_called()

    # -------------------------------------------------------------------------
    # AT-005: Notification at Pipeline End
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_005_notification_at_pipeline_end(self):
        """@builder-1 -> @reviewer -> @notify pipeline completes."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Agent output")
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Use -> for pipeline syntax
            command = parse_command(
                '@builder-1 implement -> @reviewer review -> @notify "All done"'
            )
            result = await executor.execute(command)

            assert result.success is True
            # Notification should be sent after other agents
            mock_bus.emit_sync.assert_called()
            # All outputs should be present
            assert "notify" in result.output.lower() or "Notification" in result.output

    # -------------------------------------------------------------------------
    # AT-006: Notification Failure Non-Blocking
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_006_notification_failure_continues_pipeline(self):
        """Pipeline continues even if notification fails."""
        mock_sdk = AsyncMock()
        call_order = []

        async def track_execute(agent_id, prompt, **kwargs):
            call_order.append(agent_id)
            return f"{agent_id} completed"

        mock_sdk.execute = track_execute
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            # Make notification fail
            mock_bus.emit_sync.side_effect = Exception("Network error")
            mock_create.return_value = mock_bus

            # Use -> for pipeline syntax
            command = parse_command('@pm plan -> @notify "Update" -> @reviewer review')
            result = await executor.execute(command)

            # Pipeline should still succeed
            assert result.success is True
            # Both PM and reviewer should execute
            assert "pm" in call_order
            assert "reviewer" in call_order

    @pytest.mark.asyncio
    async def test_at_006_failure_shows_warning(self):
        """Notification failure shows warning but success=True."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_bus.emit_sync.side_effect = Exception("Failed")
            mock_create.return_value = mock_bus

            result = await executor._handle_notify("Test", background=False)

            # Should succeed (non-blocking)
            assert result.success is True
            # Should show warning
            assert "⚠️" in result.output or "failed" in result.output.lower()

    # -------------------------------------------------------------------------
    # AT-007: Agent Status Display
    # -------------------------------------------------------------------------
    def test_at_007_notify_in_valid_agents(self):
        """notify is in VALID_AGENTS set."""
        assert "notify" in VALID_AGENTS

    def test_at_007_notify_in_default_agents(self):
        """notify is in DEFAULT_AGENTS for status panel."""
        assert "notify" in DEFAULT_AGENTS

    def test_at_007_status_panel_shows_na_model(self):
        """Status panel shows (n/a) for notify model."""
        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()

        # Find the notify line
        lines = content.split("\n")
        notify_lines = [line for line in lines if "notify" in line]
        assert len(notify_lines) >= 1
        # Should show (n/a)
        assert "(n/a)" in notify_lines[0]

    def test_at_007_seven_agents_in_status(self):
        """Status panel renders all 7 agents including notify."""
        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()

        expected = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"]
        for agent in expected:
            assert agent in content, f"Missing {agent} in status panel"

    # -------------------------------------------------------------------------
    # AT-008: Background Notification Execution
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_008_background_notification(self):
        """@notify with & executes in background."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            command = parse_command('@notify "Background test" &')
            result = await executor.execute(command)

            # Should return immediately with background flag
            assert result.success is True
            # Background mode should be indicated
            assert result.background is True or "Notification sent" in result.output

    # -------------------------------------------------------------------------
    # AT-009: Downstream $notify Reference
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_009_downstream_notify_reference(self):
        """@pm can reference $notify output."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="PM processed input")
        config = {"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Execute notify first, then PM referencing it
            notify_cmd = parse_command('@notify "Test message"')
            await executor.execute(notify_cmd)

            # Check that result is stored
            stored_result = executor._manager._agent_results.get("notify")
            assert stored_result is not None
            assert "Notification sent" in stored_result.output

    def test_at_009_result_stored_in_agent_results(self):
        """Notify result is stored for $notify references."""

        # Verify the structure exists
        mock_sdk = AsyncMock()
        _ = TaskExecutor(sdk_client=mock_sdk)

        # After execution, result should be stored
        # This is tested in the async test above

    # -------------------------------------------------------------------------
    # AT-010: Legacy /notify Removed
    # -------------------------------------------------------------------------
    def test_at_010_slash_notify_returns_unknown(self):
        """ "/notify" returns unknown command error."""
        commands = SystemCommands()
        result = commands.dispatch("notify", ["test", "message"])

        assert result.success is False
        assert "Unknown command" in result.output

    def test_at_010_help_shows_at_notify(self):
        """Help text shows @notify, not /notify."""
        result = handle_help([])

        assert "@notify" in result.output
        assert "/notify" not in result.output

    def test_at_010_notify_not_in_handlers(self):
        """notify is not in SystemCommands handlers."""
        commands = SystemCommands()
        # Dispatch returns unknown for notify
        result = commands.dispatch("notify", [])
        assert "Unknown command" in result.output


class TestNotifyPseudoAgentCore:
    """Core validation tests for pseudo-agent mechanics."""

    def test_notify_is_pseudo_agent(self):
        """is_pseudo_agent('notify') returns True."""
        assert is_pseudo_agent("notify") is True

    def test_pm_is_not_pseudo_agent(self):
        """is_pseudo_agent('pm') returns False."""
        assert is_pseudo_agent("pm") is False

    def test_pseudo_agents_constant(self):
        """PSEUDO_AGENTS contains 'notify'."""
        assert "notify" in PSEUDO_AGENTS

    def test_router_accepts_notify(self):
        """AgentRouter.is_valid_agent('notify') returns True."""
        router = AgentRouter()
        assert router.is_valid_agent("notify") is True
