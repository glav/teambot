"""Tests for REPL loop."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from teambot.repl.loop import REPLLoop
from teambot.repl.parser import CommandType


class TestREPLLoopInit:
    """Tests for REPLLoop initialization."""

    def test_repl_creates_default_console(self):
        """Test REPL creates console if not provided."""
        repl = REPLLoop()
        assert repl._console is not None

    def test_repl_creates_default_sdk_client(self):
        """Test REPL creates SDK client if not provided."""
        repl = REPLLoop()
        assert repl._sdk_client is not None

    def test_repl_uses_provided_console(self):
        """Test REPL uses provided console."""
        mock_console = MagicMock()
        repl = REPLLoop(console=mock_console)
        assert repl._console is mock_console

    def test_repl_uses_provided_sdk_client(self):
        """Test REPL uses provided SDK client."""
        mock_client = MagicMock()
        repl = REPLLoop(sdk_client=mock_client)
        assert repl._sdk_client is mock_client


class TestREPLHandlers:
    """Tests for REPL command handlers."""

    def test_raw_input_returns_tip(self):
        """Test raw input shows usage tip."""
        repl = REPLLoop()
        result = repl._handle_raw_input("hello")
        assert "Tip" in result or "@agent" in result

    def test_raw_input_empty_returns_empty(self):
        """Test empty raw input returns empty."""
        repl = REPLLoop()
        result = repl._handle_raw_input("")
        assert result == ""

    def test_raw_input_whitespace_returns_empty(self):
        """Test whitespace raw input returns empty."""
        repl = REPLLoop()
        result = repl._handle_raw_input("   ")
        assert result == ""

    @pytest.mark.asyncio
    async def test_agent_handler_calls_sdk(self):
        """Test agent handler calls SDK execute."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Response")
        mock_console = MagicMock()

        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)
        repl._sdk_connected = True  # Simulate connected SDK
        result = await repl._handle_agent_command("pm", "Create plan")

        mock_sdk.execute.assert_called_once_with("pm", "Create plan")
        assert result == "Response"

    @pytest.mark.asyncio
    async def test_agent_handler_catches_sdk_error(self):
        """Test agent handler catches SDK errors."""
        from teambot.copilot.sdk_client import SDKClientError

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=SDKClientError("Connection failed"))
        mock_console = MagicMock()

        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)
        repl._sdk_connected = True  # Simulate connected SDK
        result = await repl._handle_agent_command("pm", "Create plan")

        assert "Error" in result

    @pytest.mark.asyncio
    async def test_agent_handler_not_connected(self):
        """Test agent handler when SDK not connected."""
        mock_console = MagicMock()

        repl = REPLLoop(console=mock_console)
        repl._sdk_connected = False
        result = await repl._handle_agent_command("pm", "Create plan")

        assert "not connected" in result.lower()

    @pytest.mark.asyncio
    async def test_advanced_command_not_connected(self):
        """Test advanced command handler when SDK not connected."""
        from teambot.repl.parser import Command
        from teambot.tasks.executor import TaskExecutor

        mock_console = MagicMock()
        mock_sdk = AsyncMock()
        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)
        repl._sdk_connected = False

        # Initialize executor (as done in run() method)
        repl._executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_complete=repl._on_task_complete,
            on_task_started=repl._on_task_started,
        )

        # Create a mock command for multi-agent execution
        command = Command(
            type=CommandType.AGENT,
            agent_id="pm",
            agent_ids=["pm", "ba"],
            content="Analyze feature",
            command="",
            args=None,
            background=False,
            is_pipeline=False,
            pipeline=None,
        )

        result = await repl._handle_advanced_command(command)
        assert "not connected" in result.lower()


class TestREPLSignalHandling:
    """Tests for signal handling."""

    def test_setup_signal_handlers(self):
        """Test signal handlers are set up."""
        repl = REPLLoop()

        # Should not raise
        repl._setup_signal_handlers()
        repl._restore_signal_handlers()

    def test_interrupt_flag_default_false(self):
        """Test interrupt flag starts false."""
        repl = REPLLoop()
        assert repl._interrupted is False


class TestREPLCleanup:
    """Tests for cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_stops_sdk(self):
        """Test cleanup stops SDK client."""
        mock_sdk = AsyncMock()
        mock_sdk.stop = AsyncMock()
        mock_console = MagicMock()

        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)
        await repl._cleanup()

        mock_sdk.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_handles_sdk_error(self):
        """Test cleanup handles SDK stop error gracefully."""
        mock_sdk = AsyncMock()
        mock_sdk.stop = AsyncMock(side_effect=Exception("Stop failed"))
        mock_console = MagicMock()

        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)

        # Should not raise
        await repl._cleanup()


class TestREPLIntegration:
    """Integration tests for REPL."""

    @pytest.mark.asyncio
    async def test_router_wired_correctly(self):
        """Test router has all handlers wired."""
        repl = REPLLoop()

        assert repl._router._agent_handler is not None
        assert repl._router._system_handler is not None
        assert repl._router._raw_handler is not None

    @pytest.mark.asyncio
    async def test_history_shared_with_commands(self):
        """Test history is shared between router and commands."""
        repl = REPLLoop()

        # Add to router history
        repl._router._history.append({"agent_id": "pm", "content": "test"})

        # Should be visible in commands
        assert len(repl._commands._history) == 1

    @pytest.mark.asyncio
    async def test_executor_initialized_when_sdk_unavailable(self):
        """Test executor is initialized even when SDK not available.
        
        This ensures /tasks command works for viewing task history
        even when the SDK is not connected.
        """
        # Create mock SDK client that is not available
        mock_sdk = AsyncMock()
        mock_sdk.is_available = MagicMock(return_value=False)
        mock_sdk.stop = AsyncMock()
        mock_console = MagicMock()

        # Create REPL with unavailable SDK
        repl = REPLLoop(console=mock_console, sdk_client=mock_sdk)

        # Stub _get_input to exit immediately
        async def mock_get_input():
            # Return /quit on first call to exit the loop
            repl._running = False
            return "/quit"

        repl._get_input = mock_get_input

        # Run the REPL (should initialize executor despite SDK being unavailable)
        await repl.run()

        # Verify executor was initialized
        assert repl._executor is not None, "Executor should be initialized"
        
        # Verify executor was set on commands (so /tasks works)
        assert repl._commands._executor is not None, "Commands should have executor"
        assert repl._commands._executor is repl._executor, "Commands should have same executor instance"
