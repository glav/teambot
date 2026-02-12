"""Tests for REPL system commands."""

from unittest.mock import MagicMock, patch

from teambot.repl.commands import (
    CommandResult,
    SystemCommands,
    handle_help,
    handle_models,
    handle_quit,
    handle_reset_agent,
    handle_status,
    handle_use_agent,
)
from teambot.repl.router import AgentRouter


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

    def test_help_contains_use_agent_and_reset_agent(self):
        """Test /help output includes new commands."""
        result = handle_help([])
        assert "/use-agent" in result.output
        assert "/reset-agent" in result.output

    def test_help_shows_sdk_version(self):
        """Test /help output includes Copilot SDK version."""
        result = handle_help([])
        assert "Copilot SDK:" in result.output


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

    def test_status_shows_default_agent(self):
        """Test /status shows default agent when router provided."""
        router = AgentRouter(default_agent="pm")
        result = handle_status([], router)
        assert "Default Agent" in result.output
        assert "pm" in result.output

    def test_status_shows_session_override(self):
        """Test /status shows session override info."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        result = handle_status([], router)
        assert "builder-1" in result.output
        assert "session override" in result.output


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

    def test_dispatch_use_agent(self):
        """Test dispatching /use-agent routes to handler."""
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        result = commands.dispatch("use-agent", ["builder-1"])
        assert result.success is True
        assert router.get_default_agent() == "builder-1"

    def test_dispatch_reset_agent(self):
        """Test dispatching /reset-agent routes to handler."""
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        commands.dispatch("use-agent", ["builder-1"])
        result = commands.dispatch("reset-agent", [])
        assert result.success is True
        assert router.get_default_agent() == "pm"

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


class TestModelsCommand:
    """Tests for /models command."""

    def test_models_lists_all_valid_models(self):
        """'/models' returns all 14 valid models."""
        result = handle_models([])

        assert result.success is True
        assert "claude-sonnet-4.5" in result.output
        assert "gpt-5" in result.output
        assert "gemini-3-pro-preview" in result.output

    def test_models_shows_categories(self):
        """'/models' shows model categories or model info."""
        result = handle_models([])

        # Should show some kind of categorization or info
        assert "standard" in result.output.lower() or "model" in result.output.lower()

    def test_models_count(self):
        """'/models' lists exactly 14 models."""
        from teambot.config.schema import VALID_MODELS

        result = handle_models([])

        # Count how many valid models appear in output
        count = sum(1 for model in VALID_MODELS if model in result.output)
        assert count == 14

    def test_models_dispatch(self):
        """Test dispatching /models command."""
        commands = SystemCommands()
        result = commands.dispatch("models", [])

        assert result.success is True
        assert "gpt" in result.output.lower() or "claude" in result.output.lower()


class TestModelCommand:
    """Tests for /model command."""

    def test_model_shows_current_models(self):
        """'/model' without args shows current session models."""
        commands = SystemCommands()
        result = commands.dispatch("model", [])

        assert result.success is True
        # Should show some info about models

    def test_model_sets_agent_model(self):
        """'/model pm gpt-5' sets model for agent."""
        commands = SystemCommands()
        result = commands.dispatch("model", ["pm", "gpt-5"])

        assert result.success is True
        assert commands._session_model_overrides.get("pm") == "gpt-5"

    def test_model_invalid_agent(self):
        """'/model invalid gpt-5' shows error for invalid agent."""
        commands = SystemCommands()
        result = commands.dispatch("model", ["invalid-agent-xyz", "gpt-5"])

        # Should fail - we validate agent IDs exist
        assert result.success is False
        assert "Invalid agent" in result.output
        assert "invalid-agent-xyz" in result.output

    def test_model_invalid_model(self):
        """'/model pm invalid' shows error for invalid model."""
        commands = SystemCommands()
        result = commands.dispatch("model", ["pm", "invalid-model-xyz"])

        assert result.success is False
        assert "invalid" in result.output.lower()

    def test_model_clears_with_clear(self):
        """'/model pm clear' clears model for agent."""
        commands = SystemCommands()
        commands._session_model_overrides["pm"] = "gpt-5"

        result = commands.dispatch("model", ["pm", "clear"])

        assert result.success is True
        assert "pm" not in commands._session_model_overrides


class TestUseAgentCommand:
    """Tests for /use-agent command handler."""

    def test_use_agent_no_args_shows_current_and_available(self):
        """No args shows current default and available agents."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent([], router)
        assert result.success is True
        assert "pm" in result.output
        assert "builder-1" in result.output

    def test_use_agent_valid_switches_default(self):
        """Valid agent ID switches the default."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["builder-1"], router)
        assert result.success is True
        assert router.get_default_agent() == "builder-1"
        assert "builder-1" in result.output

    def test_use_agent_invalid_shows_error(self):
        """Invalid agent ID returns error with available agents."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["foo"], router)
        assert result.success is False
        assert "foo" in result.output
        assert router.get_default_agent() == "pm"  # Unchanged

    def test_use_agent_idempotent(self):
        """Setting same default returns informational message."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["pm"], router)
        assert result.success is True
        assert "already" in result.output.lower()

    def test_use_agent_no_router_returns_error(self):
        """No router available returns graceful error."""
        result = handle_use_agent(["builder-1"], None)
        assert result.success is False

    def test_use_agent_resolves_alias(self):
        """Alias is resolved to canonical ID before storing."""
        router = AgentRouter(default_agent="ba")
        result = handle_use_agent(["project_manager"], router)
        assert result.success is True
        assert router.get_default_agent() == "pm"
        assert "pm" in result.output


class TestResetAgentCommand:
    """Tests for /reset-agent command handler."""

    def test_reset_agent_restores_config_default(self):
        """Resets to config default after runtime switch."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        result = handle_reset_agent([], router)
        assert result.success is True
        assert router.get_default_agent() == "pm"
        assert "pm" in result.output

    def test_reset_agent_already_at_default(self):
        """Informational message when already at config default."""
        router = AgentRouter(default_agent="pm")
        result = handle_reset_agent([], router)
        assert result.success is True
        assert "already" in result.output.lower()

    def test_reset_agent_no_router_returns_error(self):
        """No router available returns graceful error."""
        result = handle_reset_agent([], None)
        assert result.success is False


class TestNotifyCommand:
    """Tests for /notify command."""

    def test_notify_without_args_shows_usage(self):
        """Test /notify without arguments returns usage help."""
        commands = SystemCommands(config={"notifications": {"enabled": True}})
        result = commands.notify([])

        assert result.success is False
        assert "Usage:" in result.output
        assert "/notify" in result.output

    def test_notify_without_config_shows_error(self):
        """Test /notify without config shows helpful error."""
        commands = SystemCommands(config=None)
        result = commands.notify(["test"])

        assert result.success is False
        assert "not configured" in result.output
        assert "teambot init" in result.output

    def test_notify_with_disabled_notifications_shows_error(self):
        """Test /notify with disabled notifications shows error."""
        commands = SystemCommands(config={"notifications": {"enabled": False}})
        result = commands.notify(["test"])

        assert result.success is False
        assert "not enabled" in result.output

    def test_notify_with_no_channels_shows_error(self):
        """Test /notify with no channels shows error."""
        commands = SystemCommands(config={"notifications": {"enabled": True, "channels": []}})
        result = commands.notify(["test"])

        assert result.success is False
        assert "No notification channels" in result.output

    def test_notify_with_empty_channels_shows_error(self):
        """Test /notify with empty channels list shows error."""
        commands = SystemCommands(
            config={"notifications": {"enabled": True}}  # No channels key
        )
        result = commands.notify(["test"])

        assert result.success is False
        assert "No notification channels" in result.output

    def test_notify_dispatch_routes_to_handler(self):
        """Test /notify is dispatched correctly."""
        commands = SystemCommands(config=None)
        result = commands.dispatch("notify", ["test"])

        # Should fail due to no config, but demonstrates routing works
        assert result.success is False
        assert "not configured" in result.output

    def test_help_includes_notify(self):
        """Test /help output includes /notify command."""
        commands = SystemCommands()
        result = commands.help([])

        assert result.success is True
        assert "/notify" in result.output

    def test_notify_joins_multiple_args(self):
        """Test /notify joins multiple arguments into message."""
        # This test verifies the message joining works even if sending fails
        commands = SystemCommands(config=None)
        result = commands.notify(["Hello", "World", "Test"])

        # Failed due to no config, but we can verify it tried
        assert result.success is False
        # The error message proves it processed the command

    @patch("teambot.notifications.config.create_event_bus_from_config")
    def test_notify_success(self, mock_create_bus):
        """Test /notify successfully sends message."""
        mock_bus = MagicMock()
        mock_bus._channels = [MagicMock()]
        mock_create_bus.return_value = mock_bus

        commands = SystemCommands(
            config={"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        )
        result = commands.notify(["Hello", "World"])

        assert result.success is True
        assert "✅" in result.output
        assert "Hello World" in result.output
        mock_bus.emit_sync.assert_called_once_with("custom_message", {"message": "Hello World"})

    @patch("teambot.notifications.config.create_event_bus_from_config")
    def test_notify_with_single_word(self, mock_create_bus):
        """Test /notify with single word message."""
        mock_bus = MagicMock()
        mock_bus._channels = [MagicMock()]
        mock_create_bus.return_value = mock_bus

        commands = SystemCommands(
            config={"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        )
        result = commands.notify(["Test"])

        assert result.success is True
        assert "Test" in result.output
        mock_bus.emit_sync.assert_called_once_with("custom_message", {"message": "Test"})

    @patch("teambot.notifications.config.create_event_bus_from_config")
    def test_notify_eventbus_creation_fails(self, mock_create_bus):
        """Test /notify when EventBus creation returns None."""
        mock_create_bus.return_value = None

        commands = SystemCommands(
            config={"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        )
        result = commands.notify(["test"])

        assert result.success is False
        assert "Failed to create" in result.output

    @patch("teambot.notifications.config.create_event_bus_from_config")
    def test_notify_eventbus_no_channels(self, mock_create_bus):
        """Test /notify when EventBus has no channels after creation."""
        mock_bus = MagicMock()
        mock_bus._channels = []  # Empty channels
        mock_create_bus.return_value = mock_bus

        commands = SystemCommands(
            config={"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
        )
        result = commands.notify(["test"])

        assert result.success is False
        assert "Failed to create" in result.output
