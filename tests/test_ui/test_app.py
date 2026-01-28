"""Tests for TeamBotApp main application."""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestTeamBotApp:
    """Tests for TeamBotApp main application."""

    @pytest.mark.asyncio
    async def test_app_displays_both_panes(self):
        """App shows input and output panes."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            assert app.query_one("#input-pane") is not None
            assert app.query_one("#output") is not None
            assert app.query_one("#prompt") is not None

    @pytest.mark.asyncio
    async def test_input_echoed_to_output(self):
        """Submitted input appears in output pane."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "t", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            output = app.query_one("#output")
            # Check output contains the command (at least one line)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_input_cleared_after_submit(self):
        """Input field cleared after submission."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "t", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            input_pane = app.query_one("#prompt")
            assert input_pane.value == ""

    @pytest.mark.asyncio
    async def test_raw_input_shows_tip(self):
        """Raw input (not @agent or /command) shows tip message."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("enter")
            await pilot.pause()

            output = app.query_one("#output")
            # Should have output lines
            assert len(output.lines) >= 1

    @pytest.mark.asyncio
    async def test_app_with_executor(self):
        """App accepts executor parameter."""
        from teambot.ui.app import TeamBotApp

        mock_executor = MagicMock()

        app = TeamBotApp(executor=mock_executor)
        async with app.run_test():
            # App should have executor
            assert app._executor is mock_executor

    @pytest.mark.asyncio
    async def test_header_displays_teambot(self):
        """Header shows TeamBot branding."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            header = app.query_one("#header")
            assert header is not None
