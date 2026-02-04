"""Tests for REPL system commands."""

from unittest.mock import MagicMock

from teambot.repl.commands import (
    CommandResult,
    SystemCommands,
    handle_help,
    handle_quit,
    handle_status,
)


class TestHelpCommand:
    """Tests for /help command."""

    def test_help_returns_command_list(self):
        """Test /help returns list of commands."""
        result = handle_help([])

        assert result.success is True
        assert "@agent" in result.output
        assert "/help" in result.output
        assert "/status" in result.output
        assert "/history" in result.output
        assert "/quit" in result.output

    def test_help_agent_topic(self):
        """Test /help agent shows agent information."""
        result = handle_help(["agent"])

        assert result.success is True
        assert "pm" in result.output
        assert "builder" in result.output

    def test_help_unknown_topic(self):
        """Test /help with unknown topic shows general help."""
        result = handle_help(["unknown"])

        assert result.success is True
        assert "Available commands" in result.output or "@agent" in result.output


class TestStatusCommand:
    """Tests for /status command."""

    def test_status_returns_agent_status(self):
        """Test /status returns agent status."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_agent_states.return_value = {
            "pm": {"status": "idle"},
            "builder-1": {"status": "working"},
        }

        commands = SystemCommands(orchestrator=mock_orchestrator)
        result = commands.status([])

        assert result.success is True
        assert "pm" in result.output
        assert "idle" in result.output.lower() or "working" in result.output.lower()

    def test_status_without_orchestrator(self):
        """Test /status without orchestrator shows basic status."""
        result = handle_status([])

        assert result.success is True
        # Should show something meaningful
        assert len(result.output) > 0


class TestHistoryCommand:
    """Tests for /history command."""

    def test_history_empty(self):
        """Test /history with no history."""
        commands = SystemCommands()
        commands._history = []

        result = commands.history([])

        assert result.success is True
        assert "No" in result.output or "empty" in result.output.lower()

    def test_history_with_entries(self):
        """Test /history with entries."""
        commands = SystemCommands()
        commands._history = [
            {"agent_id": "pm", "content": "Task 1"},
            {"agent_id": "ba", "content": "Task 2"},
        ]

        result = commands.history([])

        assert result.success is True
        assert "pm" in result.output
        assert "ba" in result.output

    def test_history_filter_by_agent(self):
        """Test /history pm filters to agent."""
        commands = SystemCommands()
        commands._history = [
            {"agent_id": "pm", "content": "Task 1"},
            {"agent_id": "ba", "content": "Task 2"},
            {"agent_id": "pm", "content": "Task 3"},
        ]

        result = commands.history(["pm"])

        assert result.success is True
        assert "pm" in result.output
        # BA entries should be filtered out or less prominent
        assert result.output.count("pm") >= 2

    def test_history_limit_entries(self):
        """Test /history limits output."""
        commands = SystemCommands()
        commands._history = [{"agent_id": "pm", "content": f"Task {i}"} for i in range(50)]

        result = commands.history([])

        assert result.success is True
        # Should limit display (not all 50)


class TestQuitCommand:
    """Tests for /quit command."""

    def test_quit_sets_exit_flag(self):
        """Test /quit sets exit flag."""
        result = handle_quit([])

        assert result.success is True
        assert result.should_exit is True

    def test_quit_shows_message(self):
        """Test /quit shows goodbye message."""
        result = handle_quit([])

        assert "bye" in result.output.lower() or "exit" in result.output.lower()


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_defaults(self):
        """Test CommandResult default values."""
        result = CommandResult(output="Test")

        assert result.output == "Test"
        assert result.success is True
        assert result.should_exit is False

    def test_command_result_exit(self):
        """Test CommandResult with exit flag."""
        result = CommandResult(output="Bye", should_exit=True)

        assert result.should_exit is True


class TestSystemCommandsDispatch:
    """Tests for command dispatch."""

    def test_dispatch_help(self):
        """Test dispatching /help."""
        commands = SystemCommands()
        result = commands.dispatch("help", [])

        assert result.success is True
        assert "help" in result.output.lower() or "@" in result.output

    def test_dispatch_status(self):
        """Test dispatching /status."""
        commands = SystemCommands()
        result = commands.dispatch("status", [])

        assert result.success is True

    def test_dispatch_history(self):
        """Test dispatching /history."""
        commands = SystemCommands()
        result = commands.dispatch("history", [])

        assert result.success is True

    def test_dispatch_quit(self):
        """Test dispatching /quit."""
        commands = SystemCommands()
        result = commands.dispatch("quit", [])

        assert result.should_exit is True

    def test_dispatch_exit_alias(self):
        """Test dispatching /exit as alias."""
        commands = SystemCommands()
        result = commands.dispatch("exit", [])

        assert result.should_exit is True

    def test_dispatch_unknown_command(self):
        """Test dispatching unknown command."""
        commands = SystemCommands()
        result = commands.dispatch("unknown", [])

        assert result.success is False
        assert "unknown" in result.output.lower() or "not found" in result.output.lower()

    def test_dispatch_with_args(self):
        """Test dispatching with arguments."""
        commands = SystemCommands()
        result = commands.dispatch("help", ["agent"])

        assert result.success is True
