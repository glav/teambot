"""Tests for InputPane widget."""

import pytest


class TestInputPane:
    """Tests for InputPane widget."""

    @pytest.mark.asyncio
    async def test_history_navigation_up(self):
        """Up arrow shows previous command."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit some commands to build history
            await pilot.click("#prompt")
            await pilot.press("f", "i", "r", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#prompt")
            await pilot.press("s", "e", "c", "o", "n", "d")
            await pilot.press("enter")
            await pilot.pause()

            # Press up arrow to get previous command
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()

            assert input_pane.value == "second"

    @pytest.mark.asyncio
    async def test_history_navigation_down(self):
        """Down arrow shows next command after up."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit commands
            await pilot.click("#prompt")
            await pilot.press("f", "i", "r", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#prompt")
            await pilot.press("s", "e", "c", "o", "n", "d")
            await pilot.press("enter")
            await pilot.pause()

            # Navigate up twice then down once
            await pilot.click("#prompt")
            await pilot.press("up", "up", "down")
            await pilot.pause()

            assert input_pane.value == "second"

    @pytest.mark.asyncio
    async def test_empty_history_no_crash(self):
        """Up arrow with empty history doesn't crash."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Press up with empty history
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()

            # Should not crash, value should be empty
            assert input_pane.value == ""

    @pytest.mark.asyncio
    async def test_history_preserves_current_input(self):
        """Navigating history preserves current unsaved input."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit a command
            await pilot.click("#prompt")
            await pilot.press("h", "i", "s", "t", "o", "r", "y")
            await pilot.press("enter")
            await pilot.pause()

            # Type something new
            await pilot.click("#prompt")
            await pilot.press("n", "e", "w")
            await pilot.pause()

            # Navigate up then down to return to current
            await pilot.press("up", "down")
            await pilot.pause()

            # Should have preserved "new"
            assert input_pane.value == "new"
