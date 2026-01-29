"""TDD Integration tests for split-pane interface.

These tests are written BEFORE implementation following TDD approach.
Tests will fail until implementation is complete.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestFallbackMode:
    """TDD tests for fallback mode - written BEFORE implementation."""

    def test_narrow_terminal_triggers_fallback(self):
        """Terminal < 80 columns should trigger legacy mode."""
        with patch("teambot.ui.app.shutil.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((79, 24))
            with patch("teambot.ui.app.sys.stdout.isatty", return_value=True):
                from teambot.ui.app import should_use_split_pane

                assert should_use_split_pane() is False

    def test_wide_terminal_uses_split_pane(self):
        """Terminal >= 80 columns should use split pane."""
        with patch("teambot.ui.app.shutil.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((80, 24))
            with patch("teambot.ui.app.sys.stdout.isatty", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    from teambot.ui.app import should_use_split_pane

                    assert should_use_split_pane() is True

    def test_legacy_mode_env_forces_fallback(self):
        """TEAMBOT_LEGACY_MODE=true should force legacy mode."""
        with patch.dict(os.environ, {"TEAMBOT_LEGACY_MODE": "true"}):
            from teambot.ui.app import should_use_split_pane

            assert should_use_split_pane() is False

    def test_non_tty_triggers_fallback(self):
        """Non-TTY terminal should trigger fallback."""
        with patch("teambot.ui.app.sys.stdout.isatty", return_value=False):
            from teambot.ui.app import should_use_split_pane

            assert should_use_split_pane() is False


class TestCommandRouting:
    """TDD tests for command routing - written BEFORE implementation."""

    @pytest.mark.asyncio
    async def test_agent_command_routes_to_executor(self, mock_executor, mock_router):
        """@agent command should route to TaskExecutor."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp(executor=mock_executor, router=mock_router)
        async with app.run_test() as pilot:
            # Type an agent command and submit
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "c", "r", "e", "a", "t", "e")
            await pilot.press("enter")
            await pilot.pause()

        mock_executor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_command_uses_system_commands(self, mock_executor):
        """/command should use SystemCommands.dispatch."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp(executor=mock_executor)
        async with app.run_test() as pilot:
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")
            await pilot.press("/", "h", "e", "l", "p")
            await pilot.press("enter")
            await pilot.pause()

            # /help should produce output without error
            assert len(output.lines) > initial_lines


class TestTaskCallbacks:
    """Tests for task execution and display."""

    @pytest.mark.asyncio
    async def test_executor_available_in_app(self):
        """Executor should be available in app."""
        from teambot.ui.app import TeamBotApp

        mock_executor = MagicMock()

        app = TeamBotApp(executor=mock_executor)
        async with app.run_test():
            # Verify executor is set
            assert app._executor is mock_executor


class TestClearCommand:
    """TDD tests for /clear command."""

    @pytest.mark.asyncio
    async def test_clear_command_clears_output(self, mock_router):
        """The /clear command should clear the output pane."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp(router=mock_router)
        async with app.run_test() as pilot:
            output = app.query_one("#output")

            # Write something to output
            output.write("Test message")
            assert len(output.lines) > 0

            # Execute /clear
            await pilot.click("#prompt")
            await pilot.press("/", "c", "l", "e", "a", "r")
            await pilot.press("enter")
            await pilot.pause()

            # Output should be cleared
            assert len(output.lines) == 0
